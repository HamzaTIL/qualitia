{{ config(materialized='table') }}

/*
  Use Case: Seller Operational Sales Summary
  Summarizes order counts, total sales, shipping performance, and average customer satisfaction.
  An agent can monitor this to identify rogue sellers, outliers, or sudden drops in a seller's KPI.
*/

WITH fct AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

sellers AS (
    SELECT * FROM {{ ref('dim_sellers') }}
),

reviews AS (
    SELECT * FROM {{ ref('stg_olist_order_reviews') }}
)

SELECT
    s.seller_sk,
    s.seller_id,
    s.city AS seller_city,
    s.state AS seller_state,
    
    -- Aggregated Sales volume
    COUNT(DISTINCT f.order_id) AS total_orders,
    COUNT(f.order_item_sk) AS total_items_sold,
    SUM(f.item_price_usd) AS total_revenue_usd,
    SUM(f.freight_value_usd) AS total_freight_charged_usd,
    
    -- Quality / Shipping metrics
    AVG(f.actual_delivery_duration_days) AS avg_delivery_duration_days,
    SUM(CASE WHEN f.is_delivery_delayed = TRUE THEN 1 ELSE 0 END) AS total_delayed_orders,
    SUM(CASE WHEN f.is_delivery_delayed = TRUE THEN 1 ELSE 0 END) / COUNT(DISTINCT f.order_id) AS delay_rate_pct,
    
    -- Customer Satisfaction metrics
    AVG(r.review_score) AS avg_review_score,
    SUM(CASE WHEN r.review_score = 1 THEN 1 ELSE 0 END) AS total_1_star_reviews

FROM sellers s
JOIN fct f ON s.seller_sk = f.seller_sk
LEFT JOIN reviews r ON f.order_id = r.order_id
GROUP BY 1, 2, 3, 4
