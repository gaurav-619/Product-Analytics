-- 01_profile_source.sql
-- Profile the GA4 public dataset to understand its shape before modeling.
-- Run this directly in the BigQuery console.

-- Total row count and date range
select
    count(*) as total_events,
    min(event_date) as earliest_date,
    max(event_date) as latest_date,
    count(distinct event_date) as distinct_dates,
    count(distinct user_pseudo_id) as distinct_users
from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
where _table_suffix between '20210101' and '20210131';
