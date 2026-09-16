{{
  config(
    materialized='view'
  )
}}

/*
  Staging model: stg_ga4_events
  Grain: One row per GA4 event
  
  Flattens the nested GA4 BigQuery export schema into a clean, typed, 
  analytics-ready event table. Uses the get_event_param macro to safely
  extract values from the event_params repeated record.
  
  Date filtering uses _TABLE_SUFFIX with configurable dbt variables
  (ga4_start_date, ga4_end_date) to control query costs.
  
  Source: Google's public, obfuscated GA4 Google Merchandise Store sample dataset
*/

with source as (
    select
        *
    from {{ source('ga4', 'events') }}
    where _table_suffix between '{{ var("ga4_start_date") }}' and '{{ var("ga4_end_date") }}'
),

renamed as (
    select
        -- Event identifiers
        event_date,
        event_timestamp,
        timestamp_micros(event_timestamp) as event_timestamp_utc,
        cast(parse_date('%Y%m%d', event_date) as date) as event_date_parsed,
        event_name,
        
        -- User identifier (anonymized by Google)
        user_pseudo_id,
        
        -- Session identifier extracted from event params
        -- GA4 stores session ID as an integer event parameter
        {{ get_event_param('ga_session_id', 'int_value') }} as ga_session_id,
        
        -- Construct a composite session key for reliable joins
        -- NULL if ga_session_id is not present (some events may lack it)
        case
            when {{ get_event_param('ga_session_id', 'int_value') }} is not null
            then concat(
                user_pseudo_id, 
                '-', 
                cast({{ get_event_param('ga_session_id', 'int_value') }} as string)
            )
            else null
        end as session_key,
        
        -- Session number (how many sessions this user has had)
        {{ get_event_param('ga_session_number', 'int_value') }} as ga_session_number,
        
        -- Page context
        {{ get_event_param('page_location', 'string_value') }} as page_location,
        {{ get_event_param('page_title', 'string_value') }} as page_title,
        {{ get_event_param('page_referrer', 'string_value') }} as page_referrer,
        
        -- Search
        -- search_term is populated on view_search_results events
        {{ get_event_param('search_term', 'string_value') }} as search_term,
        
        -- Transaction identifiers
        -- In GA4 BigQuery exports, transaction_id can appear both as an event param
        -- and in the ecommerce struct. We extract both for deduplication.
        {{ get_event_param('transaction_id', 'string_value') }} as transaction_id,
        
        -- Ecommerce fields
        -- These fields are in the top-level ecommerce struct in the GA4 export.
        -- In the obfuscated dataset, some ecommerce sub-fields may be absent.
        -- We use safe access patterns.
        ecommerce.purchase_revenue as ecommerce_purchase_revenue,
        ecommerce.purchase_revenue_in_usd as ecommerce_purchase_revenue_in_usd,
        ecommerce.transaction_id as ecommerce_transaction_id,
        ecommerce.total_item_quantity as ecommerce_total_item_quantity,
        
        -- Device context
        device.category as device_category,
        device.operating_system as operating_system,
        device.web_info.browser as browser,
        
        -- Geographic context
        geo.country as country,
        geo.city as city,
        geo.continent as continent,
        geo.sub_continent as sub_continent,
        
        -- Traffic source (first-touch attribution from GA4)
        -- These represent the FIRST source that brought this user to the property
        traffic_source.source as first_user_source,
        traffic_source.medium as first_user_medium,
        traffic_source.name as first_user_campaign,
        
        -- Engagement
        {{ get_event_param('engagement_time_msec', 'int_value') }} as engagement_time_msec,
        {{ get_event_param('engaged_session_event', 'int_value') }} as engaged_session_event,
        
        -- Items array (preserved for downstream unnesting)
        items

    from source
)

select * from renamed
