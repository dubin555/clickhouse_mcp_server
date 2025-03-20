
```sql
-- Create sales analysis table with comments
CREATE TABLE IF NOT EXISTS default.city_sales
(
    city String COMMENT 'Name of the city where the sale occurred',
    product_category Enum('Electronics' = 1, 'Apparel' = 2, 'Grocery' = 3) COMMENT 'Category of the product sold',
    sale_date Date COMMENT 'Date of the sales transaction',
    units_sold UInt32 COMMENT 'Number of units sold in the transaction',
    unit_price Float32 COMMENT 'Price per unit in USD',
    total_sales Float32 MATERIALIZED units_sold * unit_price COMMENT 'Calculated total sales amount'
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(sale_date)
ORDER BY (city, product_category, sale_date)
COMMENT 'Table storing city-wise product sales data for business analysis';

-- Generate 10,000 random sales records
INSERT INTO default.city_sales (city, product_category, sale_date, units_sold, unit_price)
SELECT
    ['New York', 'London', 'Tokyo', 'Paris', 'Singapore', 'Dubai'][rand() % 6 + 1] AS city,
    toInt16(rand() % 3 + 1) AS product_category,
    today() - rand() % 365 AS sale_date,
    rand() % 100 + 1 AS units_sold,      -- Units between 1-100
    randNormal(50, 15) AS unit_price     -- Normal distribution around $50
FROM numbers(10000);
```

