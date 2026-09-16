-- 03_validate_purchase_fields.sql
-- Inspect purchase events to understand which revenue and transaction fields
-- are populated in the obfuscated dataset.

select
    count(*) as total_purchase_events,
    
    -- Transaction ID availability
    count(ecommerce.transaction_id) as has_ecommerce_txn_id,
    count(
        (select ep.value.string_value from unnest(event_params) ep where ep.key = 'transaction_id')
    ) as has_param_txn_id,
    
    -- Revenue field availability
    count(ecommerce.purchase_revenue) as has_purchase_revenue,
    count(ecommerce.purchase_revenue_in_usd) as has_purchase_revenue_usd,
    
    -- Revenue statistics
    min(ecommerce.purchase_revenue_in_usd) as min_revenue_usd,
    max(ecommerce.purchase_revenue_in_usd) as max_revenue_usd,
    avg(ecommerce.purchase_revenue_in_usd) as avg_revenue_usd,
    
    -- Item array availability
    count(case when array_length(items) > 0 then 1 end) as has_items,
    
    -- Distinct transactions
    count(distinct ecommerce.transaction_id) as distinct_txn_ids

from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
where event_name = 'purchase'
  and _table_suffix between '20210101' and '20210131';
