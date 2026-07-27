{{ config(materialized='table') }}

WITH stg AS (
    SELECT * FROM {{ ref('stg_olist_customers') }}
)

SELECT
    MD5(customer_id) AS customer_sk,
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix AS zip_code_prefix,
    customer_city AS city,
    customer_state AS state
FROM stg
