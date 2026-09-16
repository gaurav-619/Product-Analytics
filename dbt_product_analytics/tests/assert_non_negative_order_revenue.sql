/*
  Custom test: assert_non_negative_order_revenue
  
  Validates that no order in int_orders has negative revenue.
  Returns rows that violate the constraint (failing rows).
  dbt expects 0 rows returned for a passing test.
*/

select
    order_transaction_key,
    order_revenue_usd
from {{ ref('int_orders') }}
where order_revenue_usd < 0
