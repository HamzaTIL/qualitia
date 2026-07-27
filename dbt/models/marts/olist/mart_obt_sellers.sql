{{ config(materialized='table') }}

/*
  Mart: One Big Table (OBT) - Sellers
  Granularity: 1 row per Seller.
  
  Use Case: "One Big Table" (OBT) architecture for BI tools and AI Agents.
  Pre-joins seller dimensions with aggregated sales facts, shipping performance, and reviews.
*/

WITH dim_sellers AS (
    SELECT * FROM {{ ref('dim_sellers') }}
),

fct_items AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

order_reviews AS (
    SELECT * FROM {{ ref('stg_olist_order_reviews') }}
),

-- Aggregate items per seller
seller_sales AS (
    SELECT
        seller_sk,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(order_item_sk) AS total_items_sold,
        SUM(item_price_usd) AS total_revenue_usd,
        SUM(freight_value_usd) AS total_freight_charged_usd,
        AVG(actual_delivery_duration_days) AS avg_delivery_duration_days,
        SUM(CASE WHEN is_delivery_delayed = TRUE THEN 1 ELSE 0 END) AS total_delayed_orders
    FROM fct_items
    GROUP BY 1
),

-- Aggregate reviews per seller
seller_reviews AS (
    SELECT
        i.seller_sk,
        AVG(r.review_score) AS avg_review_score,
        SUM(CASE WHEN r.review_score <= 2 THEN 1 ELSE 0 END) AS total_negative_reviews
    FROM fct_items i
    JOIN order_reviews r ON i.order_id = r.order_id
    GROUP BY 1
)

SELECT
    s.seller_sk,
    s.seller_id,
    s.zip_code_prefix,
    s.city,
    s.state,
    
    COALESCE(ss.total_orders, 0) AS total_orders,
    COALESCE(ss.total_items_sold, 0) AS total_items_sold,
    COALESCE(ss.total_revenue_usd, 0) AS total_revenue_usd,
    COALESCE(ss.total_freight_charged_usd, 0) AS total_freight_charged_usd,
    ss.avg_delivery_duration_days,
    ss.total_delayed_orders,
    CASE WHEN ss.total_orders > 0 THEN (ss.total_delayed_orders * 100.0) / ss.total_orders ELSE 0.0 END AS delay_rate_pct,
    
    sr.avg_review_score,
    COALESCE(sr.total_negative_reviews, 0) AS total_negative_reviews

FROM dim_sellers s
LEFT JOIN seller_sales ss ON s.seller_sk = ss.seller_sk
LEFT JOIN seller_reviews sr ON s.seller_sk = sr.seller_sk
