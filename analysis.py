"""Integration 4 — KPI Dashboard: Amman Digital Market Analytics

Extract data from PostgreSQL, compute KPIs, run statistical tests,
and create visualizations for the executive summary.

Usage:
    python analysis.py
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sqlalchemy import create_engine


def connect_db():
    """Create a SQLAlchemy engine connected to the amman_market database."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/amman_market")
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            print("Successfully connected to the database.")
        return engine
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        exit(1)


def extract_data(engine):
    """Extract all required tables from the database into DataFrames."""
    table_names = ["customers", "products", "orders", "order_items"]
    data_dict = {}
    try:
        for table in table_names:
            print(f"Extracting table: {table}...")
            data_dict[table] = pd.read_sql_table(table, engine)
        print("Data extraction complete.")
        return data_dict
    except Exception as e:
        print(f"Error extracting data: {e}")
        exit(1)

def clean_and_prepare_data(data_dict):
    """Clean, filter, and prepare the data for analysis."""
    # 1. Create copies to work on
    customers = data_dict["customers"].copy()
    products = data_dict["products"].copy()
    orders = data_dict["orders"].copy()
    order_items = data_dict["order_items"].copy()

    # 2. Handle Missing Keys (delete rows where linking is impossible)
    orders.dropna(subset=['order_id', 'customer_id'], inplace=True)
    order_items.dropna(subset=['order_id', 'product_id'], inplace=True)
    
    # 3. Impute Missing Values (No Deletion)
    products['unit_price'].fillna(products['unit_price'].median(), inplace=True)
    order_items['quantity'].fillna(order_items['quantity'].median(), inplace=True)
    products['category'].fillna('Unknown', inplace=True)
    orders['status'].fillna('cancelled', inplace=True) # Assume missing status is a failed order

    # 4. Filter Data Based on Business Rules
    orders = orders[orders['status'] != 'cancelled']
    order_items = order_items[order_items['quantity'] <= 100]

    # 5. Merge into a single DataFrame
    df = pd.merge(order_items, orders, on="order_id", how="inner")
    df = pd.merge(df, products, on="product_id", how="inner")
    df = pd.merge(df, customers, on="customer_id", how="inner")

    # 6. Rename columns and create calculated columns
    df.rename(columns={
        'registration_date': 'signup_date',
        'category': 'product_category',
        'unit_price': 'price'
    }, inplace=True)
    
    df['order_date'] = pd.to_datetime(df['order_date'])
    if 'signup_date' in df.columns:
        df['signup_date'] = pd.to_datetime(df['signup_date'])
    df['line_item_total'] = df['quantity'] * df['price']
    
    print("Data cleaning and preparation complete.")
    return df, orders # Return cleaned orders df for MAC calculation

def compute_kpis(df, cleaned_orders):
    """Compute the 5 KPIs from the cleaned data."""
    if df.empty:
        print("Warning: DataFrame is empty after cleaning. KPIs will be empty.")
        # Return a structure of empty results to avoid crashing
        return {
            "monthly_revenue": pd.Series(), "monthly_active_customers": pd.Series(),
            "arpu": pd.Series(), "retention_cohort": pd.DataFrame(),
            "aov_by_category": pd.Series()
        }

    kpi_results = {}
    
    # FIX: Use 'ME' for Month-End frequency
    # KPI 1: Monthly Revenue
    monthly_revenue = df.set_index('order_date').groupby(pd.Grouper(freq='ME'))['line_item_total'].sum()
    kpi_results["monthly_revenue"] = monthly_revenue

    # KPI 2: Monthly Active Customers (use cleaned orders)
    monthly_active_customers = cleaned_orders.set_index('order_date').groupby(pd.Grouper(freq='ME'))['customer_id'].nunique()
    kpi_results["monthly_active_customers"] = monthly_active_customers
    
    # KPI 3: Average Revenue Per User
    # Use .div and fill_value=0 to prevent division by zero errors
    arpu = monthly_revenue.div(monthly_active_customers, fill_value=0)
    kpi_results["arpu"] = arpu

    # KPI 4: Customer Retention Cohort
    df['order_month'] = df['order_date'].dt.to_period('M')
    df['cohort'] = df.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
    
    cohort_data = df.groupby(['cohort', 'order_month'])['customer_id'].nunique().reset_index()
    cohort_data['cohort_index'] = (cohort_data['order_month'] - cohort_data['cohort']).apply(lambda x: x.n)
    
    cohort_size = cohort_data[cohort_data['cohort_index'] == 0].set_index('cohort')['customer_id']
    cohort_retention = cohort_data.set_index(['cohort', 'cohort_index'])['customer_id'].unstack(1)
    cohort_retention = cohort_retention.divide(cohort_size, axis=0)
    kpi_results["retention_cohort"] = cohort_retention
    
    # KPI 5: Average Order Value by Product Category
    order_totals = df.groupby('order_id')['line_item_total'].sum()
    order_categories = df.loc[df.groupby('order_id')['quantity'].idxmax()][['order_id', 'product_category']]
    aov_df = pd.merge(order_totals.rename('order_total'), order_categories, on='order_id')
    aov_by_category = aov_df.groupby('product_category')['order_total'].mean().sort_values(ascending=False)
    kpi_results["aov_by_category"] = aov_by_category
    
    print("KPI computation complete.")
    return kpi_results

def run_statistical_tests(df):
    """Run hypothesis tests on the cleaned data."""
    if df.empty:
        print("Skipping statistical tests, data is empty.")
        return {}
        
    # Test 1: ANOVA on AOV across Product Categories
    order_totals = df.groupby('order_id')['line_item_total'].sum()
    order_categories = df.loc[df.groupby('order_id')['quantity'].idxmax()][['order_id', 'product_category']]
    aov_df = pd.merge(order_totals.rename('order_total'), order_categories, on='order_id')
    
    categories = aov_df['product_category'].unique()
    grouped_data = [aov_df['order_total'][aov_df['product_category'] == cat] for cat in categories]
    
    if len(grouped_data) > 1:
        f_statistic, p_value = stats.f_oneway(*grouped_data)
        interpretation = (f"Reject H0. Significant difference in AOV found (p={p_value:.4f})." if p_value < 0.05 else f"Fail to reject H0. No significant difference in AOV found (p={p_value:.4f}).")
        stat_results = {"aov_by_category_anova": {"test_name": "ANOVA on AOV by Category", "interpretation": interpretation}}
    else:
        stat_results = {"aov_by_category_anova": {"test_name": "ANOVA on AOV by Category", "interpretation": "Test not run. Only one category found."}}
    
    print("Statistical tests complete.")
    return stat_results

def create_visualizations(kpi_results, stat_results):
    """Create and save visualizations for all KPIs."""
    sns.set_theme(style="whitegrid")
    
    # Visualization 1: Monthly Revenue
    plt.figure(figsize=(12, 6)); sns.lineplot(data=kpi_results['monthly_revenue'], marker='o').set_title("Monthly Revenue Growth", fontsize=16, weight='bold'); plt.ylabel("Revenue (JOD)"); plt.savefig("output/kpi_1_monthly_revenue.png"); plt.close()

    # Visualization 2: Monthly Active Customers
    plt.figure(figsize=(12, 6)); sns.lineplot(data=kpi_results['monthly_active_customers'], marker='o', color='green').set_title("Monthly Active Customers Growth", fontsize=16, weight='bold'); plt.ylabel("Number of Customers"); plt.savefig("output/kpi_2_monthly_active_customers.png"); plt.close()

    # Visualization 3: Average Revenue Per User
    plt.figure(figsize=(12, 6)); sns.lineplot(data=kpi_results['arpu'], marker='o', color='purple').set_title("Average Revenue Per User (ARPU)", fontsize=16, weight='bold'); plt.ylabel("ARPU (JOD)"); plt.savefig("output/kpi_3_arpu.png"); plt.close()

    # Visualization 4: Customer Retention Cohort
    plt.figure(figsize=(14, 9)); sns.heatmap(data=kpi_results['retention_cohort'], annot=True, fmt='.0%', cmap='viridis').set_title("Monthly Customer Retention by Cohort", fontsize=16, weight='bold'); plt.xlabel("Months Since First Purchase"); plt.ylabel("First Purchase Cohort"); plt.savefig("output/kpi_4_retention_cohort.png"); plt.close()
    
    # Visualization 5: AOV by Product Category
    plt.figure(figsize=(12, 8)); aov_data = kpi_results['aov_by_category']; sns.barplot(x=aov_data.values, y=aov_data.index, palette="mako").set_title("Average Order Value by Product Category", fontsize=16, weight='bold'); plt.xlabel("AOV (JOD)"); plt.ylabel("Product Category"); plt.savefig("output/kpi_5_aov_by_category.png"); plt.close()
    
    print("Visualizations created and saved to 'output/' directory.")

def main():
    """Orchestrate the full analysis pipeline."""
    os.makedirs("output", exist_ok=True)
    
    print("--- Starting Amman Digital Market Analytics Pipeline ---")
    
    engine = connect_db()
    data_dict = extract_data(engine)
    
    # New structure: clean data first, then pass it to other functions
    cleaned_df, cleaned_orders = clean_and_prepare_data(data_dict)
    
    kpi_results = compute_kpis(cleaned_df, cleaned_orders)
    stat_results = run_statistical_tests(cleaned_df)
    create_visualizations(kpi_results, stat_results)
    
    print("\n--- Executive Summary ---")
    if not kpi_results.get('monthly_revenue', pd.Series()).empty:
        latest_revenue = kpi_results['monthly_revenue'].iloc[-1]; latest_revenue_month = kpi_results['monthly_revenue'].index[-1].strftime('%B %Y')
        print(f"\n📈 Latest Monthly Revenue ({latest_revenue_month}): {latest_revenue:,.2f} JOD")
        latest_mac = kpi_results['monthly_active_customers'].iloc[-1]
        print(f"👥 Latest Monthly Active Customers ({latest_revenue_month}): {int(latest_mac)} customers")
        mean_aov = kpi_results['aov_by_category'].mean()
        print(f"💰 Overall Average Order Value (AOV): {mean_aov:,.2f} JOD")
    else:
        print("\nNo data available to generate summary.")

    if stat_results:
        print("\n🔬 Statistical Test Results:")
        for test_name, result in stat_results.items():
            print(f"  - Test: {result['test_name']} -> {result['interpretation']}")
            
    print("\n✅ Analysis complete. All charts saved to 'output' directory.")
    print("--- Pipeline Finished ---")

if __name__ == "__main__":
    main()