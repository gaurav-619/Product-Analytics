"""
Page 4: Segmentation and Monetization
Device, channel, search adoption, RFM, and product analysis.
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
)

st.set_page_config(page_title="Segmentation & Monetization", page_icon="💰", layout="wide")
inject_custom_css()
st.title("💰 Segmentation & Monetization")

st.info(
    "**Portfolio Case Study** — Google's public, obfuscated GA4 sample dataset. "
    "Search adoption comparisons show *association*, not causation."
)

# ── Segment Performance ──────────────────────────────────────────────────

st.subheader("Segment Performance")

seg_df = load_mart("mart_segment_performance")

if seg_df is not None and not seg_df.empty:
    segment_type = st.selectbox(
        "Segment Type",
        options=seg_df["segment_type"].unique(),
        index=0,
    )

    seg_filtered = seg_df[seg_df["segment_type"] == segment_type].copy()

    # Comparison chart
    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            seg_filtered,
            x="segment_value", y="session_conversion_rate",
            title=f"Session Conversion Rate by {segment_type}",
            labels={"session_conversion_rate": "Conversion Rate", "segment_value": "Segment"},
            text_auto=".2%",
        )
        fig.update_yaxes(tickformat=".2%", gridcolor="rgba(255,255,255,0.1)")
        fig.update_traces(marker_color="#00F0FF", opacity=0.8) # Cyan
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            seg_filtered,
            x="segment_value", y="total_revenue_usd",
            title=f"Total Revenue by {segment_type}",
            labels={"total_revenue_usd": "Revenue (USD)", "segment_value": "Segment"},
            text_auto="$,.0f",
        )
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
        fig.update_traces(marker_color="#B388FF", opacity=0.8) # Purple
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # Detail table
    display_cols = [
        "segment_value", "unique_users", "total_sessions",
        "purchase_sessions", "total_revenue_usd",
        "session_conversion_rate", "avg_order_value_usd",
    ]
    st.dataframe(
        seg_filtered[display_cols].rename(columns={
            "segment_value": "Segment",
            "unique_users": "Users",
            "total_sessions": "Sessions",
            "purchase_sessions": "Purchase Sessions",
            "total_revenue_usd": "Revenue (USD)",
            "session_conversion_rate": "Session CVR",
            "avg_order_value_usd": "AOV (USD)",
        }),
        use_container_width=True,
        hide_index=True,
    )

    if segment_type == "search_adoption":
        st.warning(
            "⚠️ **Correlation, not causation:** The difference between search and "
            "non-search sessions is an observed association. Users who search may "
            "have higher purchase intent to begin with. A randomized experiment is "
            "needed to establish a causal relationship. See the Experiment Design document."
        )
else:
    show_setup_instructions()

st.markdown("---")

# ── RFM Segmentation ────────────────────────────────────────────────────

st.subheader("Customer Segmentation (RFM)")

rfm_df = load_mart("mart_customer_rfm")

if rfm_df is not None and not rfm_df.empty:
    # Segment distribution
    rfm_summary = rfm_df.groupby("rfm_segment").agg(
        customers=("user_pseudo_id", "count"),
        total_revenue=("monetary_value_usd", "sum"),
        avg_frequency=("frequency", "mean"),
        avg_recency=("recency_days", "mean"),
    ).reset_index().sort_values("total_revenue", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.treemap(
            rfm_summary,
            path=["rfm_segment"],
            values="customers",
            color="total_revenue",
            title="Customer Distribution by RFM Segment",
            color_continuous_scale="Tealgrn"
        )
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        
        # Use Streamlit 1.35+ on_select functionality
        selected = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
        selected_segments = []
        if selected and "selection" in selected and "points" in selected["selection"]:
            points = selected["selection"]["points"]
            if points:
                selected_segments = [p.get("id") or p.get("label") for p in points]
                
    with col2:
        fig_bar = px.bar(
            rfm_summary,
            x="rfm_segment", y="total_revenue",
            title="Revenue by RFM Segment",
            labels={"total_revenue": "Revenue (USD)", "rfm_segment": "Segment"},
            text_auto="$,.0f",
        )
        fig_bar.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
        fig_bar.update_traces(marker_color="#FF4081", opacity=0.8) # Magenta
        fig_bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    # Detail table filtering
    display_summary = rfm_summary.copy()
    if selected_segments:
        # Filter down to the clicked segment
        display_summary = display_summary[display_summary["rfm_segment"].isin(selected_segments)]
        
    st.dataframe(
        display_summary.rename(columns={
            "rfm_segment": "Segment",
            "customers": "Customers",
            "total_revenue": "Revenue (USD)",
            "avg_frequency": "Avg Frequency",
            "avg_recency": "Avg Recency (days)",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "RFM scores use NTILE(5) quintiles. Lower recency = better (more recent). "
        "Higher frequency and monetary = better. See docs/metric_definitions.md."
    )
else:
    st.warning("⚠️ RFM data not available. Run `dbt build` first.")

st.markdown("---")

# ── Revenue Concentration ───────────────────────────────────────────────

st.subheader("Revenue Concentration")

if rfm_df is not None and not rfm_df.empty:
    # Filter only purchasing customers
    purchasers = rfm_df[rfm_df["monetary_value_usd"] > 0].copy()
    if not purchasers.empty:
        # Sort descending by revenue
        purchasers = purchasers.sort_values("monetary_value_usd", ascending=False).reset_index(drop=True)
        
        # Calculate cumulative revenue percentage
        total_rev = purchasers["monetary_value_usd"].sum()
        purchasers["cumulative_revenue"] = purchasers["monetary_value_usd"].cumsum()
        purchasers["cumulative_revenue_pct"] = purchasers["cumulative_revenue"] / total_rev
        
        # Calculate percentile of purchasers
        purchasers["customer_percentile"] = (purchasers.index + 1) / len(purchasers)
        
        fig_conc = px.line(
            purchasers,
            x="customer_percentile", y="cumulative_revenue_pct",
            title="Cumulative Revenue by Top Purchasers",
            labels={
                "customer_percentile": "Percent of Purchasing Customers (Ranked by Revenue)",
                "cumulative_revenue_pct": "Cumulative % of Total Revenue",
            }
        )
        fig_conc.update_traces(line_color="#00F0FF", line_width=4)
        
        # Find exactly where top 10% is reached
        top_10_idx = int(len(purchasers) * 0.1) - 1
        if top_10_idx >= 0:
            top_10_rev_share = purchasers.iloc[top_10_idx]["cumulative_revenue_pct"]
            fig_conc.add_annotation(
                x=0.1, y=top_10_rev_share,
                text=f"Top 10% of purchasers drive {format_pct(top_10_rev_share)} of revenue",
                showarrow=True, arrowhead=2, ax=60, ay=30
            )
            
        fig_conc.update_xaxes(tickformat=".0%", gridcolor="rgba(255,255,255,0.1)")
        fig_conc.update_yaxes(tickformat=".0%", gridcolor="rgba(255,255,255,0.1)")
        fig_conc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        
        st.plotly_chart(fig_conc, use_container_width=True)
        
        st.caption("Only includes users with at least one purchase. Non-purchasers are excluded to avoid zero-distortion.")

st.markdown("---")

# ── Product Performance ──────────────────────────────────────────────────

st.subheader("Top Products by Revenue")

prod_df = load_mart("mart_product_performance")

if prod_df is not None and not prod_df.empty:
    top_n = st.slider("Number of products to display", 5, 50, 20)
    top_products = prod_df.head(top_n)

    fig = px.bar(
        top_products,
        x="total_item_revenue_usd", y="item_name",
        orientation="h",
        title=f"Top {top_n} Products by Revenue",
        labels={"total_item_revenue_usd": "Revenue (USD)", "item_name": "Product"},
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed"), 
        height=max(400, top_n * 25),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)")
    )
    fig.update_traces(marker_color="#00E676", opacity=0.8) # Green
    st.plotly_chart(fig, use_container_width=True)

    # Detail table
    display_cols = [
        "item_name", "item_category", "total_units_sold",
        "unique_purchasers", "total_item_revenue_usd", "avg_revenue_per_unit_usd",
    ]
    available_cols = [c for c in display_cols if c in top_products.columns]
    st.dataframe(
        top_products[available_cols],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("⚠️ Product data not available. Run `dbt build` first.")

add_methodology_note()
