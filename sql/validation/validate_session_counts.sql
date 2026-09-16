-- validate_session_counts.sql
-- Cross-validate session counts between staging, int_sessions, and mart models.
-- Run after dbt build. Replace YOUR_DATASET with your target dataset.

-- Compare total sessions in intermediate vs mart
select
    'int_sessions' as model,
    count(distinct session_key) as total_sessions,
    count(distinct user_pseudo_id) as total_users
from `YOUR_PROJECT.YOUR_DATASET.int_sessions`

union all

select
    'mart_kpis_sum' as model,
    sum(total_sessions) as total_sessions,
    sum(daily_active_users) as total_users
from `YOUR_PROJECT.YOUR_DATASET.mart_product_kpis_daily`;
