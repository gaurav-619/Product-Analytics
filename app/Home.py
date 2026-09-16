"""
Product Analytics Engine — Streamlit Dashboard
Home page and app configuration.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `from app.utils import ...` works
# regardless of how Streamlit is launched.
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
from app.utils import inject_custom_css

st.set_page_config(
    page_title="Product Analytics Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()

# ── Sidebar ──────────────────────────────────────────────────────────────

st.sidebar.markdown("---")
st.sidebar.caption(
    "📖 [Methodology & Limitations](docs/limitations.md) · "
    "[Metric Definitions](docs/metric_definitions.md)"
)
st.sidebar.markdown("---")
st.sidebar.info(
    "**Portfolio Case Study**\n\n"
    "Built on Google's public, obfuscated GA4 Google Merchandise Store "
    "sample ecommerce dataset. This is an independent project — not "
    "affiliated with Google's merchandise operations."
)

# ── Main Content ─────────────────────────────────────────────────────────

st.title("📊 Product Analytics Engine")
st.markdown("### Growth, Retention & Monetization")

st.markdown("---")

st.markdown(
    """
    > **Data Source:** Google's public, obfuscated GA4 Google Merchandise Store 
    > sample ecommerce dataset via BigQuery.

    This dashboard presents product analytics across the full product lifecycle:
    
    **Acquisition → Activation → Engagement → Monetization → Retention**
    """
)

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        #### 📈 Funnel Analysis
        Where do users drop off in the purchase journey?
        Sequential funnel from session to purchase.
        """
    )

with col2:
    st.markdown(
        """
        #### 🔄 Retention Cohorts
        Do users return after their first visit?
        Weekly activity retention by cohort.
        """
    )

with col3:
    st.markdown(
        """
        #### 💰 Segmentation & Monetization
        Which segments drive the most value?
        Device, channel, search, and RFM analysis.
        """
    )

st.markdown("---")

import json

metadata = {}
metadata_path = Path(__file__).resolve().parent / "data" / "metadata.json"
if metadata_path.exists():
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    except Exception:
        pass

if metadata:
    st.info(
        f"**Portfolio Case Study**\n\n"
        f"Using historical, obfuscated GA4 sample data; not a live production dashboard.\n\n"
        f"🗓️ **Extract Refresh Date:** {metadata.get('export_timestamp_utc', 'Unknown')[:10]}"
    )
else:
    st.info(
        "**Portfolio Case Study**\n\n"
        "Built on Google's public, obfuscated GA4 Google Merchandise Store "
        "sample ecommerce dataset."
    )

st.markdown(
    """
    ### How to Use This Dashboard
    
    1. **Navigate** using the sidebar pages
    2. **Filter** by date range on each page
    3. **Hover** over charts for detailed tooltips
    4. All metrics are computed from dbt marts — see the 
       [Methodology & Limitations](docs/limitations.md) page for caveats
    
    ### Setup Status
    
    If you see "Failed to load local extract" or "table not found" errors, ensure you have either:
    - Generated deployment extracts by running `python src/export_deployment_data.py`
    - **OR** configured `.env` with BigQuery credentials and run `dbt build`
    """
)
