{{ config(materialized='table') }}

/*
  Mart: Product Performance
  Use Case: Catalog & Inventory Management
  Summarizes sales, revenue, reviews, and freight costs at the product level.
*/

WITH fct_items AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

products AS (
    SELECT * FROM {{ ref('dim_products') }}
),

reviews AS (
    SELECT * FROM {{ ref('stg_olist_order_reviews') }}
)

SELECT
    p.product_sk,
    p.product_id,
    p.product_category_english AS product_category,
    
    -- Dimensions
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    
    -- Sales Volume
    COUNT(f.order_item_sk) AS total_units_sold,
    SUM(f.item_price_usd) AS total_revenue_usd,
    SUM(f.freight_value_usd) AS total_freight_generated_usd,
    
    -- Review Score details
    AVG(r.review_score) AS avg_product_review_score,
    SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) AS total_negative_reviews

FROM products p
JOIN fct_items f ON p.product_sk = f.product_sk
LEFT JOIN reviews r ON f.order_id = r.order_id
GROUP BY 1, 2, 3, 4, 5, 6, 7
