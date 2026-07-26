{{ config(materialized='table') }}

/*
  Fact: Orders
  Granularity: One row per exact order. Rolls up order_items and payments to provide
  a high-level summary of the entire order.
*/

WITH orders AS (
    SELECT * FROM {{ ref('stg_olist_orders') }}
),

order_items_agg AS (
    SELECT
        order_id,
        COUNT(order_item_id) AS total_items,
        SUM(price) AS total_items_value_usd,
        SUM(freight_value) AS total_freight_value_usd
    FROM {{ ref('stg_olist_order_items') }}
    GROUP BY 1
),

payments_agg AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payment_value_usd
    FROM {{ ref('stg_olist_order_payments') }}
    GROUP BY 1
)

SELECT
    o.order_id,
    MD5(o.customer_id) AS customer_sk,
    o.order_status,
    
    -- Financials
    COALESCE(i.total_items, 0) AS total_items,
    COALESCE(i.total_items_value_usd, 0) AS total_items_value_usd,
    COALESCE(i.total_freight_value_usd, 0) AS total_freight_value_usd,
    COALESCE(p.total_payment_value_usd, 0) AS total_payment_value_usd,
    
    -- Timestamps
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    
    -- Logistics KPIs
    DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date) AS actual_delivery_duration_days,
    CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN TRUE ELSE FALSE END AS is_delivery_delayed

FROM orders o
LEFT JOIN order_items_agg i ON o.order_id = i.order_id
LEFT JOIN payments_agg p ON o.order_id = p.order_id
