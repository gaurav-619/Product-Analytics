{{
  config(
    materialized='table'
  )
}}

/*
  Intermediate model: int_sessions
  Grain: One row per session_key (user + session combination)
  
  Aggregates event-level data into session-level metrics and flags.
  Only includes events with a valid (non-null) session_key.
  
  Funnel flags indicate whether a session contained each event type,
  but do NOT enforce sequential ordering (that is in int_session_funnel).
*/

with events as (
    select *
    from {{ ref('stg_ga4_events') }}
    where session_key is not null
),

session_agg as (
    select
        session_key,
        
        -- Session timing
        min(event_timestamp_utc) as session_start_timestamp,
        max(event_timestamp_utc) as session_end_timestamp,
        cast(min(event_date_parsed) as date) as session_date,
        
        -- User
        -- Use the user_pseudo_id from the first event in the session
        min(user_pseudo_id) as user_pseudo_id,
        
        -- Event counts
        count(*) as event_count,
        
        -- Funnel presence flags (did this event type occur in the session?)
        max(case when event_name = 'page_view' then 1 else 0 end) = 1 as has_page_view,
        max(case when event_name = 'view_item' then 1 else 0 end) = 1 as has_view_item,
        max(case when event_name = 'add_to_cart' then 1 else 0 end) = 1 as has_add_to_cart,
        max(case when event_name = 'begin_checkout' then 1 else 0 end) = 1 as has_begin_checkout,
        max(case when event_name = 'purchase' then 1 else 0 end) = 1 as has_purchase,
        max(case when event_name = 'view_search_results' then 1 else 0 end) = 1 as has_search,
        
        -- Revenue: sum only from purchase events
        coalesce(
            sum(case when event_name = 'purchase' then ecommerce_purchase_revenue_in_usd end),
            0
        ) as session_revenue_usd,
        
        -- Transaction count: distinct transaction IDs from purchase events
        count(
            distinct case when event_name = 'purchase'
                then coalesce(ecommerce_transaction_id, transaction_id)
            end
        ) as transaction_count,
        
        -- Engagement
        sum(coalesce(engagement_time_msec, 0)) as total_engagement_time_msec

    from events
    group by session_key
),

-- Get device, geo, and acquisition context from the FIRST event in the session
first_event as (
    select
        session_key,
        device_category,
        operating_system,
        browser,
        country,
        city,
        first_user_source,
        first_user_medium,
        first_user_campaign,
        page_location as landing_page,
        row_number() over (
            partition by session_key 
            order by event_timestamp_utc asc
        ) as rn
    from events
),

first_event_deduped as (
    select * from first_event where rn = 1
)

select
    sa.session_key,
    sa.session_start_timestamp,
    sa.session_end_timestamp,
    sa.session_date,
    sa.user_pseudo_id,
    
    -- Context from first event
    fe.device_category,
    fe.operating_system,
    fe.browser,
    fe.country,
    fe.city,
    fe.first_user_source,
    fe.first_user_medium,
    fe.first_user_campaign,
    fe.landing_page,
    
    -- Session metrics
    sa.event_count,
    sa.has_page_view,
    sa.has_view_item,
    sa.has_add_to_cart,
    sa.has_begin_checkout,
    sa.has_purchase,
    sa.has_search,
    sa.session_revenue_usd,
    sa.transaction_count,
    sa.total_engagement_time_msec

from session_agg sa
left join first_event_deduped fe
    on sa.session_key = fe.session_key
