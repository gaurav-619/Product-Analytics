# Architecture

## Overview

This project follows a layered analytics architecture that separates concerns:

```
Source Data → Transformation → Analysis → Presentation
```

## Layer Details

### 1. Source Layer
- **Google BigQuery public dataset**: `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
- Real production GA4 event data from the Google Merchandise Store
- Daily partitioned event export tables
- Nested schema with `event_params`, `items`, `device`, `geo`, `traffic_source`

### 2. Transformation Layer (dbt)
Three-tier dbt model pattern:

**Staging (`stg_`)**: Views that flatten the nested GA4 schema
- Extract event parameters using the `get_event_param` macro
- Type casting and field renaming
- No business logic

**Intermediate (`int_`)**: Tables with business-logic transformations
- `int_sessions`: Session aggregation with funnel flags
- `int_users`: User-level lifetime metrics
- `int_orders`: Deduplicated transactions
- `int_session_funnel`: Strict sequential funnel
- `int_product_events`: Unnested item-level events

**Marts (`mart_`)**: Tables optimized for dashboard consumption
- `mart_product_kpis_daily`: Daily KPIs
- `mart_funnel_performance`: Sequential funnel by date and device
- `mart_retention_cohorts`: Weekly cohort retention
- `mart_customer_rfm`: RFM segmentation
- `mart_segment_performance`: Device, channel, search, purchaser segments
- `mart_product_performance`: Item-level purchase metrics

### 3. Analysis Layer (Python)
- **Data quality report**: Automated source profiling and reconciliation
- **Verified findings**: Descriptive analysis from mart queries
- **Simulated A/B test**: Statistical methodology demonstration (synthetic data)

### 4. Presentation Layer
- **Streamlit dashboard**: Interactive executive analytics cockpit
- **Documentation**: Product case study, experiment design, interview guide

## Data Flow

```
BigQuery Public Data
    │
    ▼
stg_ga4_events (view)
    │
    ├──► int_sessions ──► mart_product_kpis_daily
    │                  ──► mart_funnel_performance
    │                  ──► mart_retention_cohorts
    │                  ──► mart_segment_performance
    │
    ├──► int_users ────► mart_customer_rfm
    │                  ──► mart_segment_performance
    │
    ├──► int_orders ───► mart_product_kpis_daily
    │                  ──► mart_customer_rfm
    │                  ──► mart_product_performance
    │
    ├──► int_session_funnel ──► mart_funnel_performance
    │
    └──► int_product_events ──► mart_product_performance
```

## Authentication

- **Development**: OAuth via `gcloud auth application-default login`
- **CI**: Minimal `dbt parse` only (no BQ credentials needed)
- **Production (optional)**: Service account key file

## Cost Controls

- Date range filtering via `GA4_START_DATE` / `GA4_END_DATE` environment variables
- dbt variables passed through to `_TABLE_SUFFIX` filtering in staging model
- No `SELECT *` in production queries
- Staging materialized as views to avoid storage costs
