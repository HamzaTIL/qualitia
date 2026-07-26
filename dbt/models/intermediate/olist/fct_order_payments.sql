{{ config(materialized='table') }}

/*
  Fact: Order Payments
  Granularity: One row per order payment. Orders can have multiple payments (e.g. Voucher + Credit Card).
*/

WITH payments AS (
    SELECT * FROM {{ ref('stg_olist_order_payments') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_olist_orders') }}
)

SELECT
    MD5(p.order_id || '-' || p.payment_sequential) AS payment_sk,
    p.order_id,
    
    -- Foreign Keys mapped back to customer
    MD5(o.customer_id) AS customer_sk,
    
    -- Payment Details
    p.payment_sequential,
    p.payment_type,
    p.payment_installments,
    p.payment_value AS payment_value_usd,
    
    -- Order Context
    o.order_purchase_timestamp,
    o.order_status

FROM payments p
JOIN orders o ON p.order_id = o.order_id
