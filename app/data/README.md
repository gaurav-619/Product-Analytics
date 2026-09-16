# Streamlit Deployment Data Extracts

These static Parquet files power the public portfolio Streamlit deployment. 
They are highly aggregated, non-sensitive extracts from the dbt models, allowing the dashboard to run without BigQuery credentials.

**Source Dataset:** Google's public, obfuscated GA4 sample dataset.
**Security:** No raw event data, user IDs, or transaction IDs are included.
