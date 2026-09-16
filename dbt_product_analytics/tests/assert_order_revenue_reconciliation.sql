/*
  Custom test: assert_order_revenue_reconciliation
  
  Diagnostic test comparing total revenue in int_orders against total
  purchase revenue in the staging model (stg_ga4_events).
  
  This test allows a small tolerance (1% or $1, whichever is greater)
  because:
  - Deduplication in int_orders removes duplicate purchase events
  - Currency conversion differences may exist between ecommerce fields
  - Rounding in FLOAT64 arithmetic
  
  NOTE: This is a diagnostic test. If it fails after initial profiling,
  investigate whether the tolerance needs adjustment based on actual
  source field behavior. Document findings in data_quality_report.md.
  
  Returns rows only if the discrepancy exceeds the tolerance.
*/

with orders_total as (
    select
        sum(order_revenue_usd) as total_order_revenue
    from {{ ref('int_orders') }}
),

source_total as (
    select
        sum(coalesce(ecommerce_purchase_revenue_in_usd, ecommerce_purchase_revenue, 0)) as total_source_revenue
    from {{ ref('stg_ga4_events') }}
    where event_name = 'purchase'
      and coalesce(ecommerce_transaction_id, transaction_id) is not null
),

comparison as (
    select
        o.total_order_revenue,
        s.total_source_revenue,
        abs(o.total_order_revenue - s.total_source_revenue) as absolute_difference,
        safe_divide(
            abs(o.total_order_revenue - s.total_source_revenue),
            nullif(s.total_source_revenue, 0)
        ) as relative_difference
    from orders_total o
    cross join source_total s
)

-- Fail if difference exceeds 1% AND $1.00
select *
from comparison
where relative_difference > 0.01
  and absolute_difference > 1.0
