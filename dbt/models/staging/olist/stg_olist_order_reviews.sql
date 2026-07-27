{{ config(materialized='view') }}

SELECT
    review_id,
    order_id,
    TRY_CAST(review_score AS INTEGER) AS review_score,
    review_comment_title,
    review_comment_message,
    TRY_CAST(review_creation_date AS TIMESTAMP) AS review_creation_date,
    TRY_CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp
FROM {{ source('raw_olist', 'olist_order_reviews') }}
