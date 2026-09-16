{{
  config(
    materialized='table'
  )
}}

/*
  Mart: mart_segment_performance
  Grain: One row per (segment_type, segment_value)
  
  Compares performance across different user/session segments:
  - device_category: desktop, mobile, tablet
  - acquisition_medium: organic, cpc, referral, etc.
  - search_adoption: sessions with vs. without site search
  - purchaser_status: purchaser vs. non-purchaser users
  
  IMPORTANT: Search adoption metrics show ASSOCIATION, not causation.
  Users who search may have higher purchase intent to begin with.
  See docs/limitations.md and docs/experiment_design.md.
*/

-- Device segment
with device_segment as (
    select
        'device_category' as segment_type,
        coalesce(device_category, 'unknown') as segment_value,
        count(distinct user_pseudo_id) as unique_users,
        count(distinct session_key) as total_sessions,
        count(distinct case when has_purchase then session_key end) as purchase_sessions,
        count(distinct case when has_purchase then user_pseudo_id end) as purchasers,
        sum(session_revenue_usd) as total_revenue_usd,
        sum(transaction_count) as total_orders,
        safe_divide(
            count(distinct case when has_purchase then session_key end),
            count(distinct session_key)
        ) as session_conversion_rate,
        safe_divide(
            sum(session_revenue_usd),
            count(distinct session_key)
        ) as revenue_per_session_usd,
        safe_divide(
            sum(session_revenue_usd),
            nullif(sum(transaction_count), 0)
        ) as avg_order_value_usd
    from {{ ref('int_sessions') }}
    group by device_category
),

-- Acquisition medium segment
medium_segment as (
    select
        'acquisition_medium' as segment_type,
        coalesce(first_user_medium, '(none)') as segment_value,
        count(distinct user_pseudo_id) as unique_users,
        count(distinct session_key) as total_sessions,
        count(distinct case when has_purchase then session_key end) as purchase_sessions,
        count(distinct case when has_purchase then user_pseudo_id end) as purchasers,
        sum(session_revenue_usd) as total_revenue_usd,
        sum(transaction_count) as total_orders,
        safe_divide(
            count(distinct case when has_purchase then session_key end),
            count(distinct session_key)
        ) as session_conversion_rate,
        safe_divide(
            sum(session_revenue_usd),
            count(distinct session_key)
        ) as revenue_per_session_usd,
        safe_divide(
            sum(session_revenue_usd),
            nullif(sum(transaction_count), 0)
        ) as avg_order_value_usd
    from {{ ref('int_sessions') }}
    group by first_user_medium
),

-- Search adoption segment
-- has_search is TRUE when the session contains a view_search_results event
-- This is an OBSERVATIONAL comparison — see experiment_design.md
search_segment as (
    select
        'search_adoption' as segment_type,
        case when has_search then 'search_session' else 'non_search_session' end as segment_value,
        count(distinct user_pseudo_id) as unique_users,
        count(distinct session_key) as total_sessions,
        count(distinct case when has_purchase then session_key end) as purchase_sessions,
        count(distinct case when has_purchase then user_pseudo_id end) as purchasers,
        sum(session_revenue_usd) as total_revenue_usd,
        sum(transaction_count) as total_orders,
        safe_divide(
            count(distinct case when has_purchase then session_key end),
            count(distinct session_key)
        ) as session_conversion_rate,
        safe_divide(
            sum(session_revenue_usd),
            count(distinct session_key)
        ) as revenue_per_session_usd,
        safe_divide(
            sum(session_revenue_usd),
            nullif(sum(transaction_count), 0)
        ) as avg_order_value_usd
    from {{ ref('int_sessions') }}
    group by has_search
),

-- Purchaser status segment (user-level)
purchaser_segment as (
    select
        'purchaser_status' as segment_type,
        case when is_purchaser then 'purchaser' else 'non_purchaser' end as segment_value,
        count(distinct user_pseudo_id) as unique_users,
        sum(session_count) as total_sessions,
        sum(purchase_session_count) as purchase_sessions,
        sum(case when is_purchaser then 1 else 0 end) as purchasers,
        sum(total_revenue_usd) as total_revenue_usd,
        sum(order_count) as total_orders,
        safe_divide(
            sum(purchase_session_count),
            nullif(sum(session_count), 0)
        ) as session_conversion_rate,
        safe_divide(
            sum(total_revenue_usd),
            nullif(sum(session_count), 0)
        ) as revenue_per_session_usd,
        safe_divide(
            sum(total_revenue_usd),
            nullif(sum(order_count), 0)
        ) as avg_order_value_usd
    from {{ ref('int_users') }}
    group by is_purchaser
)

select * from device_segment
union all
select * from medium_segment
union all
select * from search_segment
union all
select * from purchaser_segment
