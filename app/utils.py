"""
Utility functions for the Streamlit dashboard.

Handles BigQuery connectivity, cached data loading, and common formatters.
All mart queries are centralized here for maintainability.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Optional dependencies for local development
try:
    from dotenv import load_dotenv
    _project_root = Path(__file__).resolve().parent.parent
    load_dotenv(_project_root / ".env")
except ImportError:
    pass

try:
    from google.cloud import bigquery
    HAS_BQ = True
except ImportError:
    HAS_BQ = False

# Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
BQ_DATASET = os.getenv("BQ_DATASET", "")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")


def _check_config() -> bool:
    """Verify required environment variables are set."""
    if not GCP_PROJECT_ID or not BQ_DATASET:
        if not HAS_BQ:
            # We are on Streamlit Cloud and the parquet files are missing.
            st.error(
                "❌ **Missing Static Data Extracts**\n\n"
                "To fix this, you must run `python src/export_deployment_data.py` on your local laptop, "
                "then commit and push the generated `app/data/` files to GitHub."
            )
        else:
            st.error(
                "❌ Missing environment variables. "
                "Copy `.env.example` to `.env` and set `GCP_PROJECT_ID` and `BQ_DATASET`."
            )
        return False
    return True


@st.cache_resource
def _get_client() -> "bigquery.Client | None":
    """Return a cached BigQuery client."""
    if not HAS_BQ or not GCP_PROJECT_ID:
        return None
    try:
        return bigquery.Client(project=GCP_PROJECT_ID, location=BQ_LOCATION)
    except Exception as e:
        st.error(
            f"❌ BigQuery connection failed: {e}\n\n"
            f"Run: `gcloud auth application-default login`"
        )
        return None


def _fqn(table: str) -> str:
    """Return fully qualified table name."""
    return f"`{GCP_PROJECT_ID}.{BQ_DATASET}.{table}`"


@st.cache_data(ttl=600)
def load_mart(table_name: str) -> pd.DataFrame | None:
    """
    Load a dbt mart table based on the APP_DATA_MODE environment variable.
    Defaults to 'static' deployment mode reading local .parquet files.
    """
    app_mode = os.getenv("APP_DATA_MODE", "static").lower()
    
    if app_mode == "static":
        data_dir = Path(__file__).resolve().parent / "data"
        parquet_path = data_dir / f"{table_name}.parquet"
        
        if parquet_path.exists():
            try:
                return pd.read_parquet(parquet_path)
            except Exception as e:
                st.error(f"❌ Failed to load local extract for `{table_name}`: {e}")
                return None
        else:
            st.error(
                f"❌ **Missing Static Data Extract: {table_name}.parquet**\n\n"
                "You are running in 'static' mode but the data file is missing.\n"
                "Run `python src/export_deployment_data.py` locally and push to GitHub."
            )
            return None

    # Local Development Mode (BigQuery)
    elif app_mode == "bigquery":
        if not _check_config():
            return None

        client = _get_client()
        if client is None:
            return None

        sql = f"SELECT * FROM {_fqn(table_name)}"
        try:
            df = client.query(sql).to_dataframe()
            
            # Clean up raw GA4 obfuscated values for better portfolio presentation
            clean_map = {
                "(none)": "Direct",
                "(data deleted)": "Unknown",
                "<Other>": "Other",
                "(not set)": "Unknown",
            }
            for col in df.select_dtypes(include=['object', 'string']).columns:
                df[col] = df[col].replace(clean_map)
                
            return df
        except Exception as e:
            error_msg = str(e)
            if "Not found" in error_msg:
                st.warning(
                    f"⚠️ Table `{table_name}` not found in dataset `{BQ_DATASET}`. "
                    f"Run `dbt build` first."
                )
            else:
                st.error(f"❌ Query failed for `{table_name}`: {e}")
            return None
    else:
        st.error(f"❌ Invalid APP_DATA_MODE: {app_mode}. Use 'static' or 'bigquery'.")
        return None




def show_setup_instructions():
    """Display setup instructions when data is unavailable."""
    st.info(
        """
        **Setup Required**
        
        This page requires dbt marts to be built. Follow these steps:
        
        1. Configure `.env` with your GCP Project ID and BigQuery dataset
        2. Authenticate: `gcloud auth application-default login`
        3. Build models: `cd dbt_product_analytics && dbt build`
        4. Restart this dashboard
        """
    )


def format_pct(value: float | None) -> str:
    """Format a decimal as a percentage string."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2%}"


def format_currency(value: float | None) -> str:
    """Format a number as USD currency."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"${value:,.2f}"


def format_number(value: float | int | None) -> str:
    """Format a number with commas."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.0f}"


def add_methodology_note():
    """Add a standard methodology reference to the page."""
    st.markdown("---")
    st.caption(
        "📖 All metrics are derived from dbt marts querying Google's public, obfuscated "
        "GA4 sample dataset. See **Methodology & Limitations** page for caveats, "
        "definitions, and data quality notes."
    )

def inject_custom_css():
    """Inject premium CSS styling into the Streamlit app."""
    st.markdown(
        """
        <style>
        /* Glassmorphism Metric Cards */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 240, 255, 0.15);
            border-color: rgba(0, 240, 255, 0.4);
        }
        
        /* Metric Label Styling */
        [data-testid="stMetricLabel"] {
            font-size: 1.05rem !important;
            color: #A0ABC0 !important;
            font-weight: 500 !important;
        }
        
        /* Metric Value Styling */
        [data-testid="stMetricValue"] {
            font-size: 2.2rem !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
        }
        
        /* Hide Top Anchor Links */
        .st-emotion-cache-12fmjuu { display: none; }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #0E1117 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Global charting colors
CHART_COLORS = {
    "control": "#636EFA",
    "treatment": "#EF553B",
    "good": "#2ECC71",
    "risk": "#E74C3C",
    "neutral": "#95A5A6",
    "primary": "#00F0FF",
    "secondary": "#B388FF",
    "accent1": "#FF4081",
    "accent2": "#00E676"
}

def render_markdown_doc(path: str, expander_label: str = None, expanded: bool = False):
    """Safely render a markdown document from the repository."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if expander_label:
            with st.expander(expander_label, expanded=expanded):
                st.markdown(content)
        else:
            st.markdown(content)
    except FileNotFoundError:
        if expander_label:
            with st.expander(expander_label, expanded=expanded):
                st.warning(f"Documentation file not found: {path}")
        else:
            st.warning(f"Documentation file not found: {path}")


def apply_global_filters(df: pd.DataFrame, df_date_col: str = "report_date") -> pd.DataFrame:
    """Apply global date, device, and traffic filters from the sidebar."""
    
    st.sidebar.info("📊 **Data source:** Google's public, obfuscated GA4 sample dataset (Nov 2020 – Jan 2021).")
    st.sidebar.markdown("### 🔍 Global Filters")
    
    # 1. Date Filter
    if df_date_col in df.columns:
        # Ensure datetime type
        if not pd.api.types.is_datetime64_any_dtype(df[df_date_col]):
            df[df_date_col] = pd.to_datetime(df[df_date_col])
            
        min_date = df[df_date_col].min().date()
        max_date = df[df_date_col].max().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if len(date_range) == 2:
            df = df[
                (df[df_date_col].dt.date >= date_range[0])
                & (df[df_date_col].dt.date <= date_range[1])
            ]
            
    # 2. Device Category Filter
    if "device_category" in df.columns:
        devices = sorted([str(d) for d in df["device_category"].dropna().unique()])
        selected_devices = st.sidebar.multiselect(
            "📱 Device Category", 
            options=devices,
            default=devices,
            help="Filter by user device type"
        )
        if selected_devices:
            df = df[df["device_category"].isin(selected_devices)]
        else:
            return pd.DataFrame(columns=df.columns) # Empty if nothing selected
            
    # 3. Traffic Medium Filter
    if "acquisition_medium" in df.columns:
        mediums = sorted([str(m) for m in df["acquisition_medium"].dropna().unique()])
        selected_mediums = st.sidebar.multiselect(
            "🚦 Traffic Medium", 
            options=mediums,
            default=mediums,
            help="Filter by acquisition channel"
        )
        if selected_mediums:
            df = df[df["acquisition_medium"].isin(selected_mediums)]
        else:
            return pd.DataFrame(columns=df.columns)
            
    return df
