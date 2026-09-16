{{
  config(
    materialized='table'
  )
}}

/*
  Mart: mart_funnel_performance
  Grain: One row per (report_date, device_category)
  
  Uses the STRICT SEQUENTIAL funnel from int_session_funnel.
  Each step requires the previous step to have occurred first within the session.
  
  This provides a more conservative (and realistic) view of funnel conversion
  compared to simple presence-based funnel counts.
*/

with funnel as (
    select
        sf.session_key,
        sf.user_pseudo_id,
        sf.reached_session,
        sf.reached_view_item,
        sf.reached_add_to_cart_after_view,
        sf.reached_begin_checkout_after_cart,
        sf.reached_purchase_after_checkout,
        s.session_date,
        s.device_category
    from {{ ref('int_session_funnel') }} sf
    inner join {{ ref('int_sessions') }} s
        on sf.session_key = s.session_key
),

aggregated as (
    select
        session_date as report_date,
        coalesce(device_category, 'unknown') as device_category,
        
        -- Step counts
        count(distinct case when reached_session then session_key end) as sessions_entered,
        count(distinct case when reached_view_item then session_key end) as sessions_product_view,
        count(distinct case when reached_add_to_cart_after_view then session_key end) as sessions_add_to_cart,
        count(distinct case when reached_begin_checkout_after_cart then session_key end) as sessions_begin_checkout,
        count(distinct case when reached_purchase_after_checkout then session_key end) as sessions_purchase,
        
        -- Step-to-step rates (sequential)
        safe_divide(
            count(distinct case when reached_view_item then session_key end),
            count(distinct case when reached_session then session_key end)
        ) as rate_session_to_view,
        
        safe_divide(
            count(distinct case when reached_add_to_cart_after_view then session_key end),
            count(distinct case when reached_view_item then session_key end)
        ) as rate_view_to_cart,
        
        safe_divide(
            count(distinct case when reached_begin_checkout_after_cart then session_key end),
            count(distinct case when reached_add_to_cart_after_view then session_key end)
        ) as rate_cart_to_checkout,
        
        safe_divide(
            count(distinct case when reached_purchase_after_checkout then session_key end),
            count(distinct case when reached_begin_checkout_after_cart then session_key end)
        ) as rate_checkout_to_purchase,
        
        -- Overall conversion (sequential)
        safe_divide(
            count(distinct case when reached_purchase_after_checkout then session_key end),
            count(distinct case when reached_session then session_key end)
        ) as overall_conversion_rate

    from funnel
    group by session_date, device_category
)

select * from aggregated
order by report_date, device_category
