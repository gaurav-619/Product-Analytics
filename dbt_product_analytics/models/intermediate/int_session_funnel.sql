{{
  config(
    materialized='table'
  )
}}

/*
  Intermediate model: int_session_funnel
  Grain: One row per session_key
  
  Strict sequential funnel analysis.
  
  This model enforces that each funnel step must occur AFTER the previous step
  within the same session. This is a deliberate analytical choice:
  
  - A user who adds to cart without ever viewing a product page is NOT counted
    as reaching the add_to_cart step in this sequential funnel
  - This gives a more accurate picture of the intended purchase flow
  - For non-sequential (any-order) presence flags, use int_sessions instead
  
  Sequential steps:
    1. Session entered (all valid sessions)
    2. Product view (view_item)
    3. Add to cart (add_to_cart) — must occur AFTER view_item
    4. Checkout start (begin_checkout) — must occur AFTER add_to_cart
    5. Purchase (purchase) — must occur AFTER begin_checkout
*/

with events as (
    select *
    from {{ ref('stg_ga4_events') }}
    where session_key is not null
),

-- Get the earliest timestamp of each funnel event per session
session_funnel_times as (
    select
        session_key,
        user_pseudo_id,
        
        min(event_timestamp_utc) as session_start_time,
        
        min(case when event_name = 'view_item' 
            then event_timestamp_utc end) as first_view_item_time,
            
        min(case when event_name = 'add_to_cart' 
            then event_timestamp_utc end) as first_add_to_cart_time,
            
        min(case when event_name = 'begin_checkout' 
            then event_timestamp_utc end) as first_begin_checkout_time,
            
        min(case when event_name = 'purchase' 
            then event_timestamp_utc end) as first_purchase_time
    
    from events
    group by session_key, user_pseudo_id
),

sequential_flags as (
    select
        session_key,
        user_pseudo_id,
        session_start_time,
        first_view_item_time,
        first_add_to_cart_time,
        first_begin_checkout_time,
        first_purchase_time,
        
        -- Step 1: Session entered — always true for valid sessions
        true as reached_session,
        
        -- Step 2: Viewed a product
        first_view_item_time is not null as reached_view_item,
        
        -- Step 3: Added to cart AFTER viewing a product
        (first_add_to_cart_time is not null
         and first_view_item_time is not null
         and first_add_to_cart_time >= first_view_item_time
        ) as reached_add_to_cart_after_view,
        
        -- Step 4: Began checkout AFTER adding to cart (which was after view)
        (first_begin_checkout_time is not null
         and first_add_to_cart_time is not null
         and first_view_item_time is not null
         and first_add_to_cart_time >= first_view_item_time
         and first_begin_checkout_time >= first_add_to_cart_time
        ) as reached_begin_checkout_after_cart,
        
        -- Step 5: Purchased AFTER beginning checkout (full funnel)
        (first_purchase_time is not null
         and first_begin_checkout_time is not null
         and first_add_to_cart_time is not null
         and first_view_item_time is not null
         and first_add_to_cart_time >= first_view_item_time
         and first_begin_checkout_time >= first_add_to_cart_time
         and first_purchase_time >= first_begin_checkout_time
        ) as reached_purchase_after_checkout
    
    from session_funnel_times
)

select * from sequential_flags
