## KPI 5

- **Name:**
  Average Order Value (AOV) by Product Category

- **Definition:**
  The average monetary value of a sales order, segmented by the primary product category within that order. It helps identify which categories drive the highest spending per transaction.

- **Formula:**
  (Sum of `line_item_total` for all orders in a category) / (Total count of unique orders in that category)

- **Data Source (tables/columns):**
  - `orders` (order_id)
  - `order_items` (order_id, product_id, quantity)
  - `products` (product_id, unit_price, category)

- **Baseline Value:**
  The overall AOV across all categories can serve as a baseline. For example, if the overall AOV is 121 JOD, any category with an AOV significantly above this is a high-performer.

- **Interpretation:**
  A high AOV for a category indicates that customers tend to place larger, more expensive orders for these items. A low AOV suggests smaller, more frequent, or lower-priced purchases. This KPI is crucial for marketing and inventory decisions, highlighting which product types are most profitable to promote.