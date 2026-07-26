{{ config(materialized='view') }}

SELECT
    order_id,
    TRY_CAST(payment_sequential AS INTEGER) AS payment_sequential,
    payment_type,
    TRY_CAST(payment_installments AS INTEGER) AS payment_installments,
    TRY_CAST(payment_value AS DOUBLE) AS payment_value
FROM {{ source('raw_olist', 'olist_order_payments') }}
