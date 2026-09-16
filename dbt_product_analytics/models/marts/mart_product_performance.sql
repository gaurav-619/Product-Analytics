{{
  config(
    materialized='table'
  )
}}

/*
  Mart: mart_product_performance
  Grain: One row per item (item_id, item_name)
  
  Item-level purchase metrics based ONLY on purchase events.
  Does not include view or add-to-cart counts to avoid cross-event inflation.
  
  Items without an item_id are excluded (cannot form a reliable key).
*/

with purchase_items as (
    select
        item_id,
        item_name,
        item_brand,
        item_category,
        user_pseudo_id,
        session_key,
        event_date_parsed,
        coalesce(quantity, 1) as quantity,
        coalesce(item_revenue_in_usd, item_revenue, price_in_usd, price, 0) as item_revenue_usd
    from {{ ref('int_product_events') }}
    where event_name = 'purchase'
      and item_id is not null
)

select
    item_id,
    min(item_name) as item_name,
    min(item_brand) as item_brand,
    min(item_category) as item_category,
    
    -- Volume
    count(*) as purchase_event_count,
    sum(quantity) as total_units_sold,
    count(distinct user_pseudo_id) as unique_purchasers,
    count(distinct session_key) as purchase_sessions,
    
    -- Revenue
    sum(item_revenue_usd) as total_item_revenue_usd,
    safe_divide(sum(item_revenue_usd), sum(quantity)) as avg_revenue_per_unit_usd,
    
    -- Date range
    min(event_date_parsed) as first_purchase_date,
    max(event_date_parsed) as last_purchase_date

from purchase_items
group by item_id
order by total_item_revenue_usd desc
