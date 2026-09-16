-- 02_event_inventory.sql
-- Inventory of all event names in the dataset with counts.
-- Useful to verify which funnel events are present.

select
    event_name,
    count(*) as event_count,
    count(distinct user_pseudo_id) as distinct_users,
    min(event_date) as first_seen,
    max(event_date) as last_seen
from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
where _table_suffix between '20210101' and '20210131'
group by event_name
order by event_count desc;
