{{
  config(
    materialized='table'
  )
}}

/*
  Mart: mart_product_kpis_daily
  Grain: One row per day
  
  Daily product KPIs for executive reporting.
  All rates use SAFE_DIVIDE to avoid division-by-zero errors.
*/

with sessions as (
    select * from {{ ref('int_sessions') }}
),

orders as (
    select * from {{ ref('int_orders') }}
),

daily_sessions as (
    select
        session_date,
        
        -- Users and sessions
        count(distinct user_pseudo_id) as daily_active_users,
        count(distinct session_key) as total_sessions,
        
        -- Funnel presence (non-sequential)
        count(distinct case when has_view_item then session_key end) as sessions_with_product_view,
        count(distinct case when has_add_to_cart then session_key end) as sessions_with_add_to_cart,
        count(distinct case when has_begin_checkout then session_key end) as sessions_with_checkout,
        count(distinct case when has_purchase then session_key end) as sessions_with_purchase,
        count(distinct case when has_search then session_key end) as sessions_with_search,
        
        -- Purchasers
        count(distinct case when has_purchase then user_pseudo_id end) as daily_purchasers
        
    from sessions
    group by session_date
),

daily_orders as (
    select
        order_date,
        count(distinct order_transaction_key) as total_orders,
        sum(order_revenue_usd) as total_revenue_usd
    from orders
    group by order_date
)

select
    ds.session_date as report_date,
    
    -- Volume
    ds.daily_active_users,
    ds.total_sessions,
    ds.daily_purchasers,
    coalesce(do2.total_orders, 0) as total_orders,
    coalesce(do2.total_revenue_usd, 0) as total_revenue_usd,
    
    -- Funnel presence counts
    ds.sessions_with_product_view,
    ds.sessions_with_add_to_cart,
    ds.sessions_with_checkout,
    ds.sessions_with_purchase,
    ds.sessions_with_search,
    
    -- Conversion rates
    safe_divide(ds.daily_purchasers, ds.daily_active_users) as user_conversion_rate,
    safe_divide(ds.sessions_with_purchase, ds.total_sessions) as session_conversion_rate,
    
    -- Monetization
    safe_divide(coalesce(do2.total_revenue_usd, 0), nullif(coalesce(do2.total_orders, 0), 0)) as avg_order_value_usd,
    safe_divide(coalesce(do2.total_revenue_usd, 0), ds.total_sessions) as revenue_per_session_usd,
    
    -- Funnel rates (non-sequential, session presence)
    safe_divide(ds.sessions_with_product_view, ds.total_sessions) as product_view_rate,
    safe_divide(ds.sessions_with_add_to_cart, ds.sessions_with_product_view) as view_to_cart_rate,
    safe_divide(ds.sessions_with_checkout, ds.sessions_with_add_to_cart) as cart_to_checkout_rate,
    safe_divide(ds.sessions_with_purchase, ds.sessions_with_checkout) as checkout_to_purchase_rate,
    
    -- Search adoption
    safe_divide(ds.sessions_with_search, ds.total_sessions) as search_adoption_rate

from daily_sessions ds
left join daily_orders do2
    on ds.session_date = do2.order_date

order by ds.session_date
