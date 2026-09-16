{{
  config(
    materialized='table'
  )
}}

/*
  Intermediate model: int_product_events
  Grain: One row per event-item combination
  
  Unnests the items array from GA4 events to create item-level records.
  Used for product performance analysis (views, adds, purchases by item).
  
  Uses LEFT JOIN UNNEST to handle events with empty/null items arrays.
  Events without items will have null item fields.
*/

with events_with_items as (
    select
        e.event_timestamp_utc,
        e.event_date_parsed,
        e.event_name,
        e.user_pseudo_id,
        e.session_key,
        e.device_category,
        
        -- Item fields from unnested array
        item.item_id,
        item.item_name,
        item.item_brand,
        item.item_category,
        item.item_category2,
        item.item_category3,
        item.price,
        item.price_in_usd,
        item.quantity,
        item.item_revenue,
        item.item_revenue_in_usd
        
    from {{ ref('stg_ga4_events') }} e
    left join unnest(e.items) as item
    
    -- Only include events that typically have item context
    where e.event_name in (
        'view_item',
        'view_item_list',
        'select_item',
        'add_to_cart',
        'remove_from_cart',
        'begin_checkout',
        'add_shipping_info',
        'add_payment_info',
        'purchase'
    )
)

select * from events_with_items
