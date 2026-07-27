{{ config(materialized='table') }}

/*
  Dimension: Locations (Geolocation)
  The raw geolocation table has multiple coordinates per zip code.
  This model groups by zip code to provide a clean 1-to-1 mapping of zip code to avg lat/lng, city, and state.
*/

WITH raw_geo AS (
    SELECT * FROM {{ ref('stg_olist_geolocation') }}
)

SELECT
    geolocation_zip_code_prefix AS zip_code_prefix,
    MAX(geolocation_city) AS city,
    MAX(geolocation_state) AS state,
    AVG(geolocation_lat) AS latitude,
    AVG(geolocation_lng) AS longitude
FROM raw_geo
GROUP BY 1
