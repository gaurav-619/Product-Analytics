"""
Configuration module for the Product Analytics Engine.

Loads environment variables from a .env file and provides
validated configuration values for BigQuery access and date ranges.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


def _require_env(key: str) -> str:
    """Get a required environment variable or exit with a helpful message."""
    value = os.getenv(key)
    if not value:
        print(
            f"❌ Missing required environment variable: {key}\n"
            f"   Copy .env.example to .env and fill in your values:\n"
            f"   cp .env.example .env",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


# Required configuration
GCP_PROJECT_ID: str = _require_env("GCP_PROJECT_ID")
BQ_DATASET: str = _require_env("BQ_DATASET")
BQ_LOCATION: str = os.getenv("BQ_LOCATION", "US")

# GA4 date range
GA4_START_DATE: str = os.getenv("GA4_START_DATE", "20210101")
GA4_END_DATE: str = os.getenv("GA4_END_DATE", "20210131")

# Derived
FULLY_QUALIFIED_DATASET: str = f"{GCP_PROJECT_ID}.{BQ_DATASET}"

# GA4 source (public dataset — no credentials needed to read)
GA4_SOURCE_TABLE: str = (
    "bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*"
)
