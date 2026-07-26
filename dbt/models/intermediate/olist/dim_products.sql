{{ config(materialized='table') }}

WITH products AS (
    SELECT * FROM {{ ref('stg_olist_products') }}
),

translation AS (
    SELECT * FROM {{ ref('stg_olist_category_translation') }}
)

SELECT
    MD5(p.product_id) AS product_sk,
    p.product_id,
    p.product_category_name,
    COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS product_category_english,
    p.product_name_length,
    p.product_description_length,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm
FROM products p
LEFT JOIN translation t ON p.product_category_name = t.product_category_name
