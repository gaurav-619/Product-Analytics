# Data Dictionary

Complete column-level documentation for all dbt models.

---

## Staging

### stg_ga4_events
**Grain:** One row per GA4 event  
**Materialization:** View  
**Source:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

| Column | Type | Description |
|--------|------|-------------|
| event_date | STRING | Event date in YYYYMMDD format (original) |
| event_timestamp | INT64 | Event timestamp in microseconds since epoch |
| event_timestamp_utc | TIMESTAMP | Event timestamp as UTC timestamp |
| event_date_parsed | DATE | Event date as DATE type |
| event_name | STRING | GA4 event name (page_view, purchase, etc.) |
| user_pseudo_id | STRING | Anonymized user identifier |
| ga_session_id | INT64 | GA4 session identifier from event_params |
| session_key | STRING | Composite key: user_pseudo_id + ga_session_id. NULL if session ID missing. |
| ga_session_number | INT64 | User's cumulative session count |
| page_location | STRING | Full URL of the page |
| page_title | STRING | HTML page title |
| page_referrer | STRING | Referring page URL |
| search_term | STRING | Search query (on view_search_results events) |
| transaction_id | STRING | Transaction ID from event_params |
| ecommerce_transaction_id | STRING | Transaction ID from ecommerce struct |
| ecommerce_purchase_revenue | FLOAT64 | Purchase revenue (local currency) |
| ecommerce_purchase_revenue_in_usd | FLOAT64 | Purchase revenue in USD |
| ecommerce_total_item_quantity | INT64 | Total item quantity in transaction |
| device_category | STRING | Device type: desktop, mobile, tablet |
| operating_system | STRING | User's operating system |
| browser | STRING | User's browser |
| country | STRING | User's country |
| city | STRING | User's city |
| continent | STRING | User's continent |
| sub_continent | STRING | User's sub-continent |
| first_user_source | STRING | First-touch traffic source |
| first_user_medium | STRING | First-touch traffic medium |
| first_user_campaign | STRING | First-touch campaign name |
| engagement_time_msec | INT64 | Engagement time in milliseconds |
| engaged_session_event | INT64 | Engaged session flag |
| items | ARRAY | Raw items array (preserved for downstream) |

---

## Intermediate

### int_sessions
**Grain:** One row per session_key  
**Primary Key:** session_key

| Column | Type | Description |
|--------|------|-------------|
| session_key | STRING | Composite session identifier |
| session_start_timestamp | TIMESTAMP | Earliest event timestamp in session |
| session_end_timestamp | TIMESTAMP | Latest event timestamp in session |
| session_date | DATE | Date of session start |
| user_pseudo_id | STRING | User identifier |
| device_category | STRING | Device from first event |
| operating_system | STRING | OS from first event |
| browser | STRING | Browser from first event |
| country | STRING | Country from first event |
| city | STRING | City from first event |
| first_user_source | STRING | Traffic source from first event |
| first_user_medium | STRING | Traffic medium from first event |
| first_user_campaign | STRING | Campaign from first event |
| landing_page | STRING | First page URL in session |
| event_count | INT64 | Total events in session |
| has_page_view | BOOL | Session contains page_view event |
| has_view_item | BOOL | Session contains view_item event |
| has_add_to_cart | BOOL | Session contains add_to_cart event |
| has_begin_checkout | BOOL | Session contains begin_checkout event |
| has_purchase | BOOL | Session contains purchase event |
| has_search | BOOL | Session contains view_search_results event |
| session_revenue_usd | FLOAT64 | Sum of purchase revenue in USD |
| transaction_count | INT64 | Distinct transactions in session |
| total_engagement_time_msec | INT64 | Total engagement time |

### int_users
**Grain:** One row per user_pseudo_id  
**Primary Key:** user_pseudo_id

| Column | Type | Description |
|--------|------|-------------|
| user_pseudo_id | STRING | Anonymized user identifier |
| first_seen_date | DATE | Earliest session date |
| last_seen_date | DATE | Latest session date |
| session_count | INT64 | Total distinct sessions |
| purchase_session_count | INT64 | Sessions with purchase |
| order_count | INT64 | Total orders |
| total_revenue_usd | FLOAT64 | Lifetime revenue (within window) |
| is_purchaser | BOOL | Has at least one purchase |
| has_ever_searched | BOOL | Has used site search |
| first_device_category | STRING | Device from first observed session |
| first_user_source | STRING | First-touch source |
| first_user_medium | STRING | First-touch medium |
| first_user_campaign | STRING | First-touch campaign |

### int_orders
**Grain:** One row per deduplicated transaction  
**Primary Key:** order_transaction_key

| Column | Type | Description |
|--------|------|-------------|
| order_transaction_key | STRING | COALESCE(ecommerce_txn_id, param_txn_id) |
| order_timestamp | TIMESTAMP | Earliest purchase event timestamp |
| order_date | DATE | Order date |
| user_pseudo_id | STRING | Purchaser identifier |
| session_key | STRING | Session where purchase occurred |
| order_revenue_usd | FLOAT64 | Order revenue in USD |
| total_item_quantity | INT64 | Total items in order |
| device_category | STRING | Device used for purchase |
| country | STRING | Country at time of purchase |
| first_user_source | STRING | First-touch source |
| first_user_medium | STRING | First-touch medium |

### int_session_funnel
**Grain:** One row per session_key  
**Primary Key:** session_key

| Column | Type | Description |
|--------|------|-------------|
| session_key | STRING | Session identifier |
| user_pseudo_id | STRING | User identifier |
| session_start_time | TIMESTAMP | Session start |
| first_view_item_time | TIMESTAMP | First view_item event (nullable) |
| first_add_to_cart_time | TIMESTAMP | First add_to_cart event (nullable) |
| first_begin_checkout_time | TIMESTAMP | First begin_checkout event (nullable) |
| first_purchase_time | TIMESTAMP | First purchase event (nullable) |
| reached_session | BOOL | Always TRUE |
| reached_view_item | BOOL | Had a view_item event |
| reached_add_to_cart_after_view | BOOL | add_to_cart after view_item |
| reached_begin_checkout_after_cart | BOOL | begin_checkout after add_to_cart |
| reached_purchase_after_checkout | BOOL | purchase after begin_checkout |

### int_product_events
**Grain:** One row per event-item combination  
**No single primary key** (event can have multiple items)

| Column | Type | Description |
|--------|------|-------------|
| event_timestamp_utc | TIMESTAMP | Event timestamp |
| event_date_parsed | DATE | Event date |
| event_name | STRING | Event type |
| user_pseudo_id | STRING | User identifier |
| session_key | STRING | Session identifier |
| device_category | STRING | Device type |
| item_id | STRING | Product item ID |
| item_name | STRING | Product name |
| item_brand | STRING | Product brand |
| item_category | STRING | Primary category |
| item_category2 | STRING | Sub-category (if available) |
| item_category3 | STRING | Sub-sub-category (if available) |
| price | FLOAT64 | Item price |
| price_in_usd | FLOAT64 | Item price in USD |
| quantity | INT64 | Item quantity |
| item_revenue | FLOAT64 | Item revenue |
| item_revenue_in_usd | FLOAT64 | Item revenue in USD |

---

## Marts

### mart_product_kpis_daily
**Grain:** One row per report_date  
**Primary Key:** report_date

See [metric_definitions.md](metric_definitions.md) for formula details.

### mart_funnel_performance
**Grain:** One row per (report_date, device_category)

### mart_retention_cohorts
**Grain:** One row per (cohort_week, activity_week_index)

### mart_customer_rfm
**Grain:** One row per purchaser (user_pseudo_id)  
**Primary Key:** user_pseudo_id

### mart_segment_performance
**Grain:** One row per (segment_type, segment_value)

### mart_product_performance
**Grain:** One row per item_id  
**Primary Key:** item_id
