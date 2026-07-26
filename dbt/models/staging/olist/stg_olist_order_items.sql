{{ config(materialized='view') }}

SELECT
    order_id,
    TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
    product_id,
    seller_id,
    TRY_CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
    TRY_CAST(price AS DOUBLE) AS price,
    TRY_CAST(freight_value AS DOUBLE) AS freight_value
FROM {{ source('raw_olist', 'olist_order_items') }}
