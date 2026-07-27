{{ config(materialized='table') }}

/*
  Mart: One Big Table (OBT) - Order Details
  Granularity: 1 row per Order Item.
  
  Use Case: "One Big Table" (OBT) architecture for BI tools (Tableau) and AI Agents.
  This highly denormalized table pre-joins all core dimensions (Customer, Seller, Product),
  order facts, financial data, and reviews into a single flat structure. 
  This allows users to filter, slice, and aggregate without writing complex SQL joins.
*/

WITH fct_items AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

fct_orders AS (
    SELECT * FROM {{ ref('fct_orders') }}
),

dim_customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
),

dim_sellers AS (
    SELECT * FROM {{ ref('dim_sellers') }}
),

dim_products AS (
    SELECT * FROM {{ ref('dim_products') }}
),

-- Aggregate reviews to order level to prevent fan-out if an order has multiple reviews
order_reviews AS (
    SELECT
        order_id,
        MAX(review_score) AS review_score,
        MAX(review_creation_date) AS review_creation_date
    FROM {{ ref('stg_olist_order_reviews') }}
    GROUP BY 1
)

SELECT
    -- Primary Keys & Identifiers
    i.order_item_sk,
    i.order_id,
    i.order_item_id,
    o.customer_sk,
    i.seller_sk,
    i.product_sk,

    -- 1. Order Status & Timestamps
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    -- 2. Item Financials
    i.item_price_usd,
    i.freight_value_usd,
    i.total_item_cost_usd,

    -- 3. Order-Level Financial Context
    o.total_payment_value_usd AS order_total_payment_usd,

    -- 4. Customer Details
    c.customer_unique_id,
    c.city AS customer_city,
    c.state AS customer_state,

    -- 5. Seller Details
    s.seller_id,
    s.city AS seller_city,
    s.state AS seller_state,

    -- 6. Product Details
    p.product_id,
    p.product_category_english AS product_category,
    p.product_weight_g,

    -- 7. Logistics & Performance KPIs
    o.actual_delivery_duration_days,
    o.is_delivery_delayed,

    -- 8. Customer Satisfaction
    r.review_score,
    r.review_creation_date

FROM fct_items i
JOIN fct_orders o ON i.order_id = o.order_id
JOIN dim_customers c ON o.customer_sk = c.customer_sk
JOIN dim_sellers s ON i.seller_sk = s.seller_sk
JOIN dim_products p ON i.product_sk = p.product_sk
LEFT JOIN order_reviews r ON i.order_id = r.order_id
