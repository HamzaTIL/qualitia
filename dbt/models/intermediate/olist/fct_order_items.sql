{{ config(materialized='table') }}

WITH items AS (
    SELECT * FROM {{ ref('stg_olist_order_items') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_olist_orders') }}
)

SELECT
    MD5(i.order_id || '-' || i.order_item_id) AS order_item_sk,
    i.order_id,
    i.order_item_id,
    
    -- Foreign Keys
    MD5(o.customer_id) AS customer_sk,
    MD5(i.product_id) AS product_sk,
    MD5(i.seller_id) AS seller_sk,
    
    -- Status
    o.order_status,
    
    -- Measures
    i.price AS item_price_usd,
    i.freight_value AS freight_value_usd,
    i.price + i.freight_value AS total_item_cost_usd,
    
    -- Dates and Timestamps
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    i.shipping_limit_date,
    
    -- Quality Indicators (Delays, lags)
    DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date) AS actual_delivery_duration_days,
    DATE_DIFF('day', o.order_purchase_timestamp, o.order_estimated_delivery_date) AS estimated_delivery_duration_days,
    DATE_DIFF('day', o.order_estimated_delivery_date, o.order_delivered_customer_date) AS delivery_delay_days,
    CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN TRUE ELSE FALSE END AS is_delivery_delayed

FROM items i
JOIN orders o ON i.order_id = o.order_id
