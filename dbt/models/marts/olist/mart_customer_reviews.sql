{{ config(materialized='table') }}

/*
  Use Case: Customer Satisfaction & Delivery Delay Analysis
  Maps review scores to order details and actual delivery performance.
  An agent can audit this table to see if drops in average review scores
  correlate with actual delivery delays (Data Quality / Operational Anomaly).
*/

WITH fct AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

reviews AS (
    SELECT * FROM {{ ref('stg_olist_order_reviews') }}
),

customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
)

SELECT
    f.order_id,
    f.order_item_id,
    f.customer_sk,
    c.customer_unique_id,
    c.city AS customer_city,
    c.state AS customer_state,
    
    -- Review Score details
    r.review_id,
    COALESCE(r.review_score, 0) AS review_score,
    r.review_comment_title,
    r.review_comment_message,
    r.review_creation_date,
    
    -- Product/Seller detail
    f.product_sk,
    f.seller_sk,
    
    -- Shipping performance
    f.is_delivery_delayed,
    f.delivery_delay_days,
    f.actual_delivery_duration_days,
    f.estimated_delivery_duration_days,
    f.item_price_usd,
    f.freight_value_usd

FROM fct f
JOIN reviews r ON f.order_id = r.order_id
JOIN customers c ON f.customer_sk = c.customer_sk
