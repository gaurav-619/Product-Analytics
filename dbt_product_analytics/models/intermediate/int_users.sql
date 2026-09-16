{{
  config(
    materialized='table'
  )
}}

/*
  Intermediate model: int_users
  Grain: One row per user_pseudo_id
  
  Aggregates session-level data into user-level lifetime metrics.
  
  Caveats (documented in docs/limitations.md):
  - user_pseudo_id is a browser/device-level identifier; users on multiple 
    devices appear as separate users
  - Acquisition attributes (first device, source/medium) are taken from the
    user's earliest observed session, which may not be their true first visit
    if it occurred outside the data window
  - "Lifetime" metrics are bounded by the configured date range
*/

with sessions as (
    select * from {{ ref('int_sessions') }}
),

user_agg as (
    select
        user_pseudo_id,
        
        -- Activity window
        min(session_date) as first_seen_date,
        max(session_date) as last_seen_date,
        
        -- Session counts
        count(distinct session_key) as session_count,
        count(distinct case when has_purchase then session_key end) as purchase_session_count,
        
        -- Order and revenue
        sum(transaction_count) as order_count,
        sum(session_revenue_usd) as total_revenue_usd,
        
        -- Purchaser flag
        max(case when has_purchase then 1 else 0 end) = 1 as is_purchaser,
        
        -- Search adoption
        max(case when has_search then 1 else 0 end) = 1 as has_ever_searched
        
    from sessions
    group by user_pseudo_id
),

-- First session attributes (imperfect — see caveats above)
first_session as (
    select
        user_pseudo_id,
        device_category as first_device_category,
        first_user_source,
        first_user_medium,
        first_user_campaign,
        row_number() over (
            partition by user_pseudo_id 
            order by session_start_timestamp asc
        ) as rn
    from sessions
),

first_session_deduped as (
    select * from first_session where rn = 1
)

select
    ua.user_pseudo_id,
    ua.first_seen_date,
    ua.last_seen_date,
    ua.session_count,
    ua.purchase_session_count,
    ua.order_count,
    ua.total_revenue_usd,
    ua.is_purchaser,
    ua.has_ever_searched,
    
    fs.first_device_category,
    fs.first_user_source,
    fs.first_user_medium,
    fs.first_user_campaign

from user_agg ua
left join first_session_deduped fs
    on ua.user_pseudo_id = fs.user_pseudo_id
