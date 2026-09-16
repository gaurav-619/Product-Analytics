"""
Page 3: Retention Cohorts
Weekly activity retention analysis.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from app.utils import (
    load_mart,
    show_setup_instructions,
    format_pct,
    format_number,
    add_methodology_note,
    inject_custom_css,
    apply_global_filters,
)

st.set_page_config(page_title="Retention Cohorts", page_icon="🔄", layout="wide")
inject_custom_css()
st.title("🔄 Retention Cohorts")

st.info(
    "**Activity retention:** A user is counted as 'retained' in a given week if they "
    "had at least one session. This is observed within the data window — users may "
    "return outside this window."
)

# Load data
df = load_mart("mart_retention_cohorts")

if df is None or df.empty:
    show_setup_instructions()
    st.stop()

# There are no device/medium filters on mart_retention_cohorts since it's aggregated by cohort.
# But we can still use apply_global_filters for date if we have report_date. 
# We actually just use the raw df for retention, but let's just make sure cohort_week is datetime.
df["cohort_week"] = pd.to_datetime(df["cohort_week"])

# ── Retention Heatmap ────────────────────────────────────────────────────

st.subheader("Retention Heatmap")

max_week = st.slider(
    "Max weeks to display",
    min_value=1,
    max_value=int(df["activity_week_index"].max()),
    value=min(8, int(df["activity_week_index"].max())),
)

heatmap_df = df[df["activity_week_index"] <= max_week].copy()

# Pivot for heatmap
pivot = heatmap_df.pivot_table(
    index="cohort_week",
    columns="activity_week_index",
    values="retention_rate",
    aggfunc="mean",
)

# Format cohort labels
pivot.index = pivot.index.strftime("%Y-%m-%d")

fig = go.Figure(data=go.Heatmap(
    z=pivot.values,
    x=[f"Week {c}" for c in pivot.columns],
    y=pivot.index,
    colorscale="Tealgrn", # Premium cyan/green gradient
    text=np.round(pivot.values * 100, 1),
    texttemplate="%{text}%",
    textfont={"size": 10},
    hoverongaps=False,
    colorbar=dict(title="Retention %", tickformat=".0%"),
    zmin=0, zmax=1,
))
fig.update_layout(
    title="Weekly Retention Rate by Cohort",
    xaxis_title="Weeks Since First Session",
    yaxis_title="Cohort Week",
    height=max(400, len(pivot) * 40),
    yaxis=dict(autorange="reversed"),
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Aggregate Retention Curve ────────────────────────────────────────────

st.subheader("Aggregate Retention Curve")

agg_retention = df.groupby("activity_week_index").agg(
    total_retained=("retained_users", "sum"),
    total_cohort=("cohort_size", "sum"),
).reset_index()
agg_retention["retention_rate"] = agg_retention["total_retained"] / agg_retention["total_cohort"]

fig = px.line(
    agg_retention[agg_retention["activity_week_index"] <= max_week],
    x="activity_week_index",
    y="retention_rate",
    title="Aggregate Retention Curve (All Cohorts)",
    labels={
        "activity_week_index": "Weeks Since First Session",
        "retention_rate": "Retention Rate",
    },
    markers=True,
)
fig.update_yaxes(tickformat=".0%", rangemode="tozero", gridcolor="rgba(255,255,255,0.1)")
fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)")
fig.update_traces(line_color="#00F0FF", line_width=4, marker=dict(size=8, color="#B388FF"))
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
# ── Stabilization Rule ───────────────────────────────────────────────────

# Rule: first cohort week where week-over-week change in retention rate is < 1% for two consecutive weeks.
# We look at agg_retention['retention_rate']
agg_retention = agg_retention.sort_values("activity_week_index")
agg_retention["retention_diff"] = agg_retention["retention_rate"].diff().abs()

stabilization_week = None
for i in range(2, len(agg_retention)):
    diff1 = agg_retention.iloc[i-1]["retention_diff"]
    diff2 = agg_retention.iloc[i]["retention_diff"]
    if diff1 < 0.01 and diff2 < 0.01:
        stabilization_week = agg_retention.iloc[i-1]["activity_week_index"]
        break

if stabilization_week:
    stab_val = agg_retention[agg_retention["activity_week_index"] == stabilization_week]["retention_rate"].iloc[0]
    fig.add_annotation(
        x=stabilization_week,
        y=stab_val,
        text=f"Stabilizes around Week {stabilization_week}",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-40
    )
else:
    # If no stabilization point found, annotate the last week
    last_idx = agg_retention.iloc[-1]["activity_week_index"]
    last_val = agg_retention.iloc[-1]["retention_rate"]
    fig.add_annotation(
        x=last_idx,
        y=last_val,
        text="Did not stabilize within 92-day window",
        showarrow=True,
        arrowhead=2,
        ax=-40,
        ay=-40
    )

st.plotly_chart(fig, use_container_width=True)

# ── Cohort Sizes ─────────────────────────────────────────────────────────

st.subheader("Cohort Sizes")

cohort_sizes = df[df["activity_week_index"] == 0][["cohort_week", "cohort_size"]].copy()
cohort_sizes["cohort_week"] = cohort_sizes["cohort_week"].dt.strftime("%Y-%m-%d")

fig2 = px.bar(
    cohort_sizes,
    x="cohort_week", y="cohort_size",
    title="Users per Cohort (Week of First Session)",
    labels={"cohort_week": "Cohort Week", "cohort_size": "Users"},
)
fig2.update_traces(marker_color="#FF4081", opacity=0.8)
fig2.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
fig2.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig2, use_container_width=True)

# ── So What? ─────────────────────────────────────────────────────────────

st.subheader("Key Observations")

week1 = agg_retention[agg_retention["activity_week_index"] == 1]
if not week1.empty:
    w1_rate = week1.iloc[0]["retention_rate"]
    st.markdown(
        f"The aggregate **Week 1 retention rate** (users returning the week after "
        f"their first session) is **{format_pct(w1_rate)}**. "
    )
    if stabilization_week:
        st.markdown(
            f"Retention stabilizes around **Week {stabilization_week}**, meaning the rate of "
            f"user drop-off falls below 1 percentage point week-over-week."
        )
    else:
        st.markdown(
            "Retention did not clearly stabilize within the observed 92-day window. Users continue "
            "to drop off week-over-week through the end of the available data."
        )
else:
    st.markdown("Week 1 retention data is not available for the selected period.")

st.caption(
    "This is observed activity retention within the data window. "
    "Users who return outside the data window are not counted. "
    "**Observation Window Limitation:** The dataset spans a maximum of 92 days, "
    "so long-term retention beyond ~12 weeks cannot be computed. "
    "See docs/limitations.md for retention analysis caveats."
)

add_methodology_note()
