{{ config(materialized='table') }}

WITH stg AS (
    SELECT * FROM {{ ref('stg_olist_sellers') }}
)

SELECT
    MD5(seller_id) AS seller_sk,
    seller_id,
    seller_zip_code_prefix AS zip_code_prefix,
    seller_city AS city,
    seller_state AS state
FROM stg
