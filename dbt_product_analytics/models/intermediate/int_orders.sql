{{
  config(
    materialized='table'
  )
}}

/*
  Intermediate model: int_orders
  Grain: One row per deduplicated transaction
  
  Extracts purchase events and deduplicates by transaction key.
  
  Transaction key logic:
  - Prefer ecommerce_transaction_id (from the ecommerce struct)
  - Fall back to transaction_id (from event_params)
  - Exclude rows where both are NULL (cannot form a valid order key)
  
  Deduplication: If the same transaction key appears on multiple purchase events,
  keep only the earliest one (by event_timestamp_utc).
*/

with purchase_events as (
    select
        *,
        -- Construct the canonical transaction key
        coalesce(ecommerce_transaction_id, transaction_id) as order_transaction_key
    from {{ ref('stg_ga4_events') }}
    where event_name = 'purchase'
      and coalesce(ecommerce_transaction_id, transaction_id) is not null
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by order_transaction_key
            order by event_timestamp_utc asc
        ) as dedup_rn
    from purchase_events
),

orders as (
    select
        order_transaction_key,
        event_timestamp_utc as order_timestamp,
        event_date_parsed as order_date,
        user_pseudo_id,
        session_key,
        
        -- Revenue
        -- Use USD revenue, falling back to local revenue
        coalesce(
            ecommerce_purchase_revenue_in_usd,
            ecommerce_purchase_revenue,
            0
        ) as order_revenue_usd,
        
        -- Item quantity
        ecommerce_total_item_quantity as total_item_quantity,
        
        -- Context
        device_category,
        country,
        first_user_source,
        first_user_medium
    
    from deduplicated
    where dedup_rn = 1
)

select * from orders
