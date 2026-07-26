{{ config(materialized='table') }}

/*
  Mart: Logistics Network
  Use Case: Supply Chain & Routing Analysis
  Analyzes the performance of delivery routes (Seller State -> Customer State).
*/

WITH fct_items AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
),

sellers AS (
    SELECT * FROM {{ ref('dim_sellers') }}
)

SELECT
    s.state AS origin_state,
    c.state AS destination_state,
    
    -- Volume
    COUNT(DISTINCT f.order_id) AS total_orders_routed,
    SUM(f.freight_value_usd) AS total_route_freight_usd,
    
    -- Distance / Pricing KPIs
    AVG(f.freight_value_usd) AS avg_freight_per_item_usd,
    
    -- Speed KPIs
    AVG(f.actual_delivery_duration_days) AS avg_delivery_duration_days,
    AVG(f.estimated_delivery_duration_days) AS avg_estimated_duration_days,
    
    -- Delay KPIs
    SUM(CASE WHEN f.is_delivery_delayed THEN 1 ELSE 0 END) AS total_delayed_orders,
    SUM(CASE WHEN f.is_delivery_delayed THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT f.order_id) AS delay_rate_pct

FROM fct_items f
JOIN customers c ON f.customer_sk = c.customer_sk
JOIN sellers s ON f.seller_sk = s.seller_sk
GROUP BY 1, 2
