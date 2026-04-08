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
    """Create a SQLAlchemy engine connected to the amman_market database.

    Returns:
        engine: SQLAlchemy engine instance

    Notes:
        Use DATABASE_URL environment variable if set, otherwise default to:
        postgresql://postgres:postgres@localhost:5432/amman_market
    """
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/amman_market")
    try:
        engine = create_engine(db_url)
        # Test connection
        with engine.connect() as connection:
            print("Successfully connected to the database.")
        return engine
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        exit(1)


def extract_data(engine):
    """Extract all required tables from the database into DataFrames.

    Args:
        engine: SQLAlchemy engine connected to amman_market

    Returns:
        dict: mapping of table names to DataFrames
              (e.g., {"customers": df, "products": df, "orders": df, "order_items": df})
    """
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


def compute_kpis(data_dict):
    """Compute the 2 required KPIs.

    Args:
        data_dict: dict of DataFrames from extract_data()

    Returns:
        dict: mapping of KPI names to their computed values.
    """
    # Unpack and prepare data
    orders = data_dict["orders"]
    order_items = data_dict["order_items"]
    products = data_dict["products"]

    # --- Data Preparation ---
    # Merge required tables for calculations
    df = pd.merge(order_items, orders, on="order_id")
    df = pd.merge(df, products, on="product_id")

    # Rename columns to match expected names for consistency
    df.rename(columns={
        'category': 'product_category',
        'unit_price': 'price'
    }, inplace=True)

    # Convert date columns and calculate totals
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['line_item_total'] = df['quantity'] * df['price']
    
    kpi_results = {}

    # --- KPI 1: Monthly Revenue (Time-based) ---
    # Use 'ME' for Month-End frequency to support newer pandas versions
    monthly_revenue = df.set_index('order_date').groupby(pd.Grouper(freq='ME'))['line_item_total'].sum()
    monthly_revenue.name = "monthly_revenue"
    kpi_results["monthly_revenue"] = monthly_revenue
    
    # --- KPI 2: Average Order Value (AOV) by Product Category ---
    order_totals = df.groupby('order_id')['line_item_total'].sum()
    # Get the primary category for each order (simplified for this KPI)
    order_categories = df.loc[df.groupby('order_id')['quantity'].idxmax()][['order_id', 'product_category']]

    aov_df = pd.merge(order_totals.rename('order_total'), order_categories, on='order_id')
    aov_by_category = aov_df.groupby('product_category')['order_total'].mean().sort_values(ascending=False)
    aov_by_category.name = "aov_by_category"
    kpi_results["aov_by_category"] = aov_by_category
    
    print("KPI computation complete.")
    return kpi_results


def run_statistical_tests(data_dict):
    """Run a hypothesis test on Average Order Value across categories.

    Args:
        data_dict: dict of DataFrames from extract_data()

    Returns:
        dict: mapping of test name to its results.
    """
    # --- Test: ANOVA on AOV across Product Categories ---
    # H0: The mean AOV is the same across all product categories.
    # H1: The mean AOV is different for at least one product category.
    
    # Prepare data for the test
    df_items = data_dict["order_items"].copy()
    df_products = data_dict["products"].copy()
    
    # Rename columns for consistency
    df_products.rename(columns={'category': 'product_category', 'unit_price': 'price'}, inplace=True)
    
    df_test = pd.merge(df_items, df_products, on="product_id")
    df_test['line_item_total'] = df_test['quantity'] * df_test['price']

    order_totals = df_test.groupby('order_id')['line_item_total'].sum()
    order_categories = df_test.loc[df_test.groupby('order_id')['quantity'].idxmax()][['order_id', 'product_category']]
    aov_df = pd.merge(order_totals.rename('order_total'), order_categories, on='order_id')
    
    categories = aov_df['product_category'].unique()
    grouped_data = [aov_df['order_total'][aov_df['product_category'] == cat] for cat in categories]
    
    # Run ANOVA if there is more than one category to compare
    if len(grouped_data) > 1:
        f_statistic, p_value = stats.f_oneway(*grouped_data)
        alpha = 0.05
        interpretation = (f"Reject H0. Statistically significant difference in AOV across categories (p={p_value:.4f})." 
                          if p_value < alpha else 
                          f"Fail to reject H0. No significant difference in AOV found (p={p_value:.4f}).")
        
        stat_results = {
            "aov_by_category_anova": {
                "test_name": "One-way ANOVA on AOV by Product Category",
                "f_statistic": f_statistic, "p_value": p_value, "interpretation": interpretation
            }
        }
    else:
        stat_results = {
            "aov_by_category_anova": {
                "test_name": "One-way ANOVA on AOV by Product Category",
                "interpretation": "Test not run. Only one product category found."
            }
        }
    
    print("Statistical tests complete.")
    return stat_results


def create_visualizations(kpi_results, stat_results):
    """Create publication-quality charts for the 2 KPIs.

    Args:
        kpi_results: dict from compute_kpis()
        stat_results: dict from run_statistical_tests()
    """
    sns.set_theme(style="whitegrid")
    
    # --- 1. Monthly Revenue ---
    plt.figure(figsize=(12, 6))
    ax = sns.lineplot(data=kpi_results['monthly_revenue'], marker='o')
    ax.set_title("Monthly Revenue Shows Strong and Consistent Growth", fontsize=16, weight='bold')
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (JOD)")
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.tight_layout()
    plt.savefig("output/kpi_1_monthly_revenue.png")
    plt.close()
    
    # --- 2. AOV by Product Category ---
    plt.figure(figsize=(12, 8))
    aov_data = kpi_results['aov_by_category']
    ax = sns.barplot(x=aov_data.values, y=aov_data.index, palette="mako")
    ax.set_title("Electronics & Home Goods Drive Highest Average Order Value", fontsize=16, weight='bold')
    ax.set_xlabel("Average Order Value (JOD)")
    ax.set_ylabel("Product Category")
    for i, v in enumerate(aov_data.values):
        ax.text(v + 1, i, f' {v:,.2f}', color='black', va='center')
    plt.tight_layout()
    plt.savefig("output/kpi_2_aov_by_category.png")
    plt.close()
    
    print("Visualizations created and saved to 'output/' directory.")


def main():
    """Orchestrate the full analysis pipeline."""
    os.makedirs("output", exist_ok=True)
    
    print("--- Starting Amman Digital Market Analytics Pipeline ---")
    
    engine = connect_db()
    data_dict = extract_data(engine)
    kpi_results = compute_kpis(data_dict)
    stat_results = run_statistical_tests(data_dict)
    create_visualizations(kpi_results, stat_results)
    
    # Print a summary of KPI values and test results
    print("\n--- Executive Summary ---")
    
    if not kpi_results['monthly_revenue'].empty:
        latest_revenue = kpi_results['monthly_revenue'].iloc[-1]
        latest_revenue_month = kpi_results['monthly_revenue'].index[-1].strftime('%B %Y')
        print(f"\n📈 Latest Monthly Revenue ({latest_revenue_month}): {latest_revenue:,.2f} JOD")
    else:
        print("\n📈 No revenue data to display.")
        
    if not kpi_results['aov_by_category'].empty:
        mean_aov = kpi_results['aov_by_category'].mean()
        print(f"💰 Overall Average Order Value (AOV): {mean_aov:,.2f} JOD")
    else:
        print("💰 No AOV data to display.")

    print("\n🔬 Statistical Test Results:")
    for test_name, result in stat_results.items():
        print(f"  - Test: {result['test_name']}")
        print(f"    - Result: {result['interpretation']}")
        
    print("\n✅ Analysis complete. All charts have been saved to the 'output' directory.")
    print("--- Pipeline Finished ---")


if __name__ == "__main__":
    main()