{{ config(materialized='table') }}

/*
  Mart: One Big Table (OBT) - Customers
  Granularity: 1 row per Customer.
  
  Use Case: "One Big Table" (OBT) architecture for BI tools and AI Agents.
  Pre-joins customer dimensions with aggregated order facts, financials, and reviews.
*/

WITH dim_customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
),

fct_orders AS (
    SELECT * FROM {{ ref('fct_orders') }}
),

order_reviews AS (
    SELECT * FROM {{ ref('stg_olist_order_reviews') }}
),

-- Aggregate orders per customer
customer_orders AS (
    SELECT
        customer_sk,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(total_items_value_usd) AS total_items_value_usd,
        SUM(total_freight_value_usd) AS total_freight_value_usd,
        SUM(total_payment_value_usd) AS total_payment_value_usd,
        MIN(order_purchase_timestamp) AS first_order_date,
        MAX(order_purchase_timestamp) AS last_order_date
    FROM fct_orders
    GROUP BY 1
),

-- Aggregate reviews per customer
customer_reviews AS (
    SELECT
        o.customer_sk,
        AVG(r.review_score) AS avg_review_score,
        COUNT(r.review_id) AS total_reviews
    FROM fct_orders o
    JOIN order_reviews r ON o.order_id = r.order_id
    GROUP BY 1
)

SELECT
    c.customer_sk,
    c.customer_id,
    c.customer_unique_id,
    c.zip_code_prefix,
    c.city,
    c.state,
    
    COALESCE(co.total_orders, 0) AS total_orders,
    COALESCE(co.total_items_value_usd, 0) AS total_items_value_usd,
    COALESCE(co.total_freight_value_usd, 0) AS total_freight_value_usd,
    COALESCE(co.total_payment_value_usd, 0) AS total_payment_value_usd,
    co.first_order_date,
    co.last_order_date,
    
    cr.avg_review_score,
    COALESCE(cr.total_reviews, 0) AS total_reviews

FROM dim_customers c
LEFT JOIN customer_orders co ON c.customer_sk = co.customer_sk
LEFT JOIN customer_reviews cr ON c.customer_sk = cr.customer_sk
