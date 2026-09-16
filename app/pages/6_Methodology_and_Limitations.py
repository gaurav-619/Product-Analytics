"""
Page 6: Methodology and Limitations
Transparent documentation of analytical approach and constraints.
"""

import streamlit as st
from app.utils import inject_custom_css, render_markdown_doc

st.set_page_config(page_title="Methodology & Limitations", page_icon="📖", layout="wide")
inject_custom_css()
st.title("📖 Methodology & Limitations")

st.info(
    "**Transparency is a core principle of this project.** Every metric, model, "
    "and finding is documented with its assumptions, limitations, and caveats."
)

# ── Data Source ───────────────────────────────────────────────────────────

st.subheader("Data Source")
st.markdown(
    """
    **Dataset:** Google's public, obfuscated GA4 Google Merchandise Store sample 
    ecommerce dataset.
    
    - **Location:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
    - **Type:** Real production data from the [Google Merchandise Store](https://shop.merchandisestore.google/)
    - **Obfuscation:** User identifiers are anonymized (hashed). Revenue and 
      transaction details are from actual purchases.
    - **Time range:** Limited to the dates available in the public dataset
    - **This is NOT proprietary data.** The author has no affiliation with Google's 
      merchandise operations.
    """
)

st.markdown("---")

# ── Modeling Approach ────────────────────────────────────────────────────

st.subheader("Data Modeling Approach")
st.markdown(
    """
    **Framework:** dbt (data build tool) with staging → intermediate → marts pattern
    
    | Layer | Purpose | Materialization |
    |-------|---------|-----------------|
    | **Staging** | Flatten nested GA4 schema, type casting | View |
    | **Intermediate** | Business-logic transformations (sessions, users, orders, funnel) | Table |
    | **Marts** | Analysis-ready aggregations for the dashboard | Table |
    
    **Key design decisions:**
    
    1. **Session identity:** Constructed from `user_pseudo_id` + `ga_session_id` 
       (extracted from `event_params`). Events without a session ID are excluded 
       from session-level models.
    
    2. **Sequential funnel:** Enforces strict temporal ordering (view → cart → 
       checkout → purchase). This is more conservative than presence-based funnels 
       but provides a more accurate picture of the intended purchase flow.
    
    3. **Order deduplication:** Uses `ROW_NUMBER()` over transaction key, keeping 
       the earliest purchase event. Transactions without a valid ID are excluded.
    
    4. **RFM scoring:** Uses `NTILE(5)` quintiles with the max order date as the 
       reference point. Score directionality: lower recency = better; higher 
       frequency/monetary = better.
    """
)

st.markdown("---")

# ── Limitations ──────────────────────────────────────────────────────────

st.subheader("Analytical Limitations")
st.markdown(
    """
    > ⚠️ **Read these before citing any findings from this project.**
    
    **What this project does NOT prove:**
    - **Causality:** The GA4 data is observational. Changes in conversion rates between segments are correlations, not causal proof that changing a feature will improve conversion.
    - **Long-term LTV:** The dataset is limited to 92 days. Lifetime Value (LTV) cannot be accurately computed without years of data or predictive churn models.
    - **Real Experiment Results:** The A/B test module (Product Decisions) uses *simulated, synthetic data* for educational purposes. It does not represent real Google Merchandise Store experiment results.
    
    1. **Obfuscated sample data** — This is a subset of the full Google Merchandise 
       Store dataset. Absolute numbers should not be treated as the store's actual KPIs.
    
    2. **Anonymous users** — `user_pseudo_id` is a device/browser-level identifier. 
       The same person on multiple devices appears as multiple users. No cross-device 
       identity resolution is possible.
    
    3. **Observational analysis only** — All findings describe correlations and 
       associations. No randomized experiment was conducted. **Correlation ≠ causation.**
    
    4. **Limited time window** — Retention and LTV metrics are bounded by the data 
       window. Users may return outside this window. Treat LTV as a "limited-period 
       revenue proxy," not a true lifetime estimate.
    
    5. **Channel attribution** — `traffic_source` in GA4 represents first-touch 
       attribution. It does not capture the full multi-touch journey.
    
    6. **Selection bias** — Users who search may have fundamentally different intent 
       than non-searchers. The search adoption analysis cannot control for this.
    
    7. **No qualitative context** — No user interviews, surveys, support tickets, 
       or session recordings are available. Quantitative findings should be 
       triangulated with qualitative research.
    
    8. **Transaction completeness** — Some purchase events may have NULL transaction 
       IDs or revenue. These are excluded from the orders model, potentially 
       understating revenue.
    
    9. **Acquisition attributes** — First device category and source/medium are from 
       the user's earliest observed session, which may not be their true first visit.
    
    10. **Not streaming** — This is a batch analytics project using historical daily 
        event exports. It does not represent real-time data.
    """
)

st.markdown("---")

# ── Statistical Methods ──────────────────────────────────────────────────

st.subheader("Statistical Methods")
st.markdown(
    """
    **Funnel and Retention Analysis:**
    - All funnel rates are descriptive statistics
    - Retention rates are observed activity retention within the data window
    - No statistical significance tests are applied to observational differences
    
    **RFM Segmentation:**
    - Quintile-based scoring using `NTILE(5)`
    - Segment labels are descriptive categories, not predictive classifications
    - The model does not use machine learning or predict future behavior
    """
)

st.markdown("---")

st.subheader("Metric Definitions & Data Dictionary")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]

render_markdown_doc(str(PROJECT_ROOT / "docs" / "metric_definitions.md"), "📖 View Metric Definitions")
render_markdown_doc(str(PROJECT_ROOT / "docs" / "data_dictionary.md"), "📖 View Data Dictionary")
