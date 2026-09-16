"""
Page 1: Executive Summary
High-level KPIs and trend overview.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.utils import (
    load_mart,
    show_setup_instructions,
    format_pct,
    format_currency,
    format_number,
    add_methodology_note,
    inject_custom_css,
    apply_global_filters,
)

st.set_page_config(page_title="Executive Summary", page_icon="📈", layout="wide")
inject_custom_css()
st.title("📈 Executive Summary")

st.info(
    "**This is a historical case study (Nov 2020 - Jan 2021), not a live monitoring dashboard.** "
    "Trend changes reflect real seasonal patterns in the observed period."
)

# Load data
df = load_mart("mart_product_kpis_daily")

if df is None or df.empty:
    show_setup_instructions()
    st.stop()

# Apply Global Filters (Date, Device, Medium)
df = apply_global_filters(df, "report_date")

if df.empty:
    st.warning("No data found for this segment combination.")
    st.stop()

# ── KPI Cards ────────────────────────────────────────────────────────────

total_sessions = df["total_sessions"].sum()
total_orders = df["total_orders"].sum()
total_revenue = df["total_revenue_usd"].sum()
overall_cvr = total_orders / total_sessions if total_sessions > 0 else 0
overall_aov = total_revenue / total_orders if total_orders > 0 else 0

# Calculate Period-over-Period (PoP) based on the last 7 days vs previous 7 days in the filtered data
df_sorted = df.sort_values("report_date")
max_date = df_sorted["report_date"].max()
last_7 = df_sorted[df_sorted["report_date"] > (max_date - pd.Timedelta(days=7))]
prev_7 = df_sorted[(df_sorted["report_date"] <= (max_date - pd.Timedelta(days=7))) & (df_sorted["report_date"] > (max_date - pd.Timedelta(days=14)))]

l7_sessions = last_7["total_sessions"].sum()
p7_sessions = prev_7["total_sessions"].sum()
session_delta = ((l7_sessions - p7_sessions) / p7_sessions * 100) if p7_sessions > 0 else 0

l7_orders = last_7["total_orders"].sum()
p7_orders = prev_7["total_orders"].sum()
order_delta = ((l7_orders - p7_orders) / p7_orders * 100) if p7_orders > 0 else 0

l7_revenue = last_7["total_revenue_usd"].sum()
p7_revenue = prev_7["total_revenue_usd"].sum()
revenue_delta = ((l7_revenue - p7_revenue) / p7_revenue * 100) if p7_revenue > 0 else 0

l7_cvr = l7_orders / l7_sessions if l7_sessions > 0 else 0
p7_cvr = p7_orders / p7_sessions if p7_sessions > 0 else 0
cvr_delta = (l7_cvr - p7_cvr) * 100 # Absolute point change for rates

l7_aov = l7_revenue / l7_orders if l7_orders > 0 else 0
p7_aov = p7_revenue / p7_orders if p7_orders > 0 else 0
aov_delta = ((l7_aov - p7_aov) / p7_aov * 100) if p7_aov > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Sessions", format_number(total_sessions), f"{session_delta:.1f}%", delta_color="off")
col2.metric("Total Orders", format_number(total_orders), f"{order_delta:.1f}%", delta_color="off")
col3.metric("Total Revenue", format_currency(total_revenue), f"{revenue_delta:.1f}%", delta_color="off")
col4.metric("Session CVR", format_pct(overall_cvr), f"{cvr_delta:.2f}pp", delta_color="off")
col5.metric("AOV", format_currency(overall_aov), f"{aov_delta:.1f}%", delta_color="off")

st.caption("Week-over-week change (within Nov 2020 - Jan 2021 observation window)")

# Seasonal decline dynamic caption
# Find the peak 7-day revenue period in the dataset
df_rolling = df_sorted.set_index("report_date").rolling("7D")["total_revenue_usd"].sum()
peak_date = df_rolling.idxmax() if not df_rolling.empty else None

if revenue_delta < 0:
    st.info(
        f"**Note on trends:** Revenue appears to decline by {abs(revenue_delta):.1f}% in the final displayed week. "
        "Because the GA4 sample ends on January 31, 2021, the final weekly period may contain incomplete data and should not be interpreted as a confirmed decline."
    )

st.markdown("---")

# ── Daily Trends ─────────────────────────────────────────────────────────

st.subheader("Daily Trends")

tab1, tab2, tab3 = st.tabs(["Sessions & Users", "Revenue & Orders", "Conversion"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["report_date"], y=df["total_sessions"],
        name="Sessions", mode="lines+markers",
        line=dict(color="#00F0FF", width=3), # Cyan
    ))
    fig.add_trace(go.Scatter(
        x=df["report_date"], y=df["daily_active_users"],
        name="Active Users", mode="lines+markers",
        line=dict(color="#B388FF", width=3), # Purple
    ))
    fig.update_layout(
        title="Daily Sessions & Active Users",
        xaxis_title="Date", yaxis_title="Count",
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["report_date"], y=df["total_revenue_usd"],
        name="Revenue (USD)", marker_color="#00F0FF",
        opacity=0.8
    ))
    fig.add_trace(go.Scatter(
        x=df["report_date"], y=df["total_orders"],
        name="Orders", mode="lines+markers",
        line=dict(color="#FF4081", width=3), yaxis="y2", # Pink/Magenta
    ))
    fig.update_layout(
        title="Daily Revenue & Orders",
        xaxis_title="Date",
        yaxis=dict(title="Revenue (USD)", gridcolor="rgba(255,255,255,0.1)"),
        yaxis2=dict(title="Orders", overlaying="y", side="right"),
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = px.line(
        df, x="report_date", y="session_conversion_rate",
        title="Daily Session Conversion Rate",
        labels={"session_conversion_rate": "Conversion Rate", "report_date": "Date"},
    )
    fig.update_traces(line_color="#00E676", line_width=3) # Vibrant Green
    fig.update_yaxes(tickformat=".2%", gridcolor="rgba(255,255,255,0.1)")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

# ── So What? ─────────────────────────────────────────────────────────────

st.subheader("Key Observations")

min_d = df["report_date"].min().strftime("%Y-%m-%d")
max_d = df["report_date"].max().strftime("%Y-%m-%d")

# Dynamic Headline Insight Generation
headline = ""
if revenue_delta > 5:
    headline = f"🚀 **Strong Recent Growth:** Revenue is up {revenue_delta:.1f}% in the last 7 days compared to the prior week."
elif revenue_delta < -5:
    headline = f"⚠️ **Recent Contraction:** Revenue is down {abs(revenue_delta):.1f}% in the last 7 days. Check funnel drops."
else:
    headline = f"⚖️ **Stable Performance:** Revenue is relatively flat ({revenue_delta:.1f}%) week-over-week."

st.markdown(headline)

st.markdown(
    f"Over the selected period ({min_d} to {max_d}), "
    f"there were **{format_number(total_sessions)} sessions** resulting in "
    f"**{format_number(total_orders)} orders** and "
    f"**{format_currency(total_revenue).replace('$', r'\$')} in revenue**. "
    f"The overall session conversion rate was **{format_pct(overall_cvr)}** "
    f"with an average order value of **{format_currency(overall_aov).replace('$', r'\$')}**."
)
st.caption(
    "These are descriptive statistics for the selected observation period. "
    "They should not be extrapolated without considering seasonality and data completeness."
)

add_methodology_note()
