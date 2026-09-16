"""
BigQuery client utility for the Product Analytics Engine.

Provides a cached BigQuery client and helper functions
for querying both the public GA4 source and the dbt target dataset.
"""

import pandas as pd
from google.cloud import bigquery

from src.config import GCP_PROJECT_ID, BQ_LOCATION

# Module-level cached client
_client: bigquery.Client | None = None


def get_client() -> bigquery.Client:
    """
    Return a cached BigQuery client.

    Authentication order:
    1. Application Default Credentials (gcloud auth application-default login)
    2. Service account key file (GOOGLE_APPLICATION_CREDENTIALS env var)
    """
    global _client
    if _client is None:
        try:
            _client = bigquery.Client(
                project=GCP_PROJECT_ID,
                location=BQ_LOCATION,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create BigQuery client. "
                f"Run: gcloud auth application-default login\n"
                f"Error: {e}"
            ) from e
    return _client


def query_to_dataframe(sql: str) -> pd.DataFrame:
    """
    Execute a SQL query and return results as a pandas DataFrame.

    Args:
        sql: A valid BigQuery SQL query string.

    Returns:
        pandas DataFrame with query results.
        Empty DataFrame if the query returns no rows.
    """
    client = get_client()
    try:
        result = client.query(sql).to_dataframe()
        return result
    except Exception as e:
        print(f"⚠️  BigQuery query failed: {e}")
        return pd.DataFrame()


def table_exists(dataset: str, table_name: str) -> bool:
    """Check if a table exists in the target dataset."""
    client = get_client()
    table_ref = f"{GCP_PROJECT_ID}.{dataset}.{table_name}"
    try:
        client.get_table(table_ref)
        return True
    except Exception:
        return False
