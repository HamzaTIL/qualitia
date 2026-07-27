{{ config(materialized='table') }}

/*
  Mart: Payment Profiles
  Use Case: Finance & Checkout Optimization
  Analyzes order volume, revenue, and customer behavior by payment method.
*/

WITH fct_payments AS (
    SELECT * FROM {{ ref('fct_order_payments') }}
),

fct_orders AS (
    SELECT * FROM {{ ref('fct_orders') }}
)

SELECT
    p.payment_type,
    p.payment_installments,
    
    -- Volume
    COUNT(p.payment_sk) AS total_transactions,
    COUNT(DISTINCT p.order_id) AS total_unique_orders,
    
    -- Financials
    SUM(p.payment_value_usd) AS total_revenue_usd,
    AVG(p.payment_value_usd) AS avg_transaction_value_usd,
    
    -- Status Context
    SUM(CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END) AS total_canceled_orders

FROM fct_payments p
JOIN fct_orders o ON p.order_id = o.order_id
GROUP BY 1, 2
