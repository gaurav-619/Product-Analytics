# Analytical Limitations

> ⚠️ **Read this before citing any findings from this project.**

---

## 1. Obfuscated Sample Data

The dataset is a **subset** of the full Google Merchandise Store data. Google has
obfuscated user identifiers and may have sampled or filtered the data. Absolute
numbers (total users, total revenue) should not be treated as the store's actual
KPIs. Proportions and rates are more reliable than absolute values, but even
these may differ from the full dataset.

## 2. Anonymous Users

`user_pseudo_id` is a device/browser-level identifier (derived from the GA client
ID cookie). Limitations:

- The same person on multiple devices appears as **multiple users**
- Clearing cookies creates a new `user_pseudo_id`
- No cross-device identity resolution is possible
- User counts are likely **overcounted**
- Session and purchase attribution to users is approximate

## 3. Observational Analysis — Correlation ≠ Causation

All findings in this project describe **observed associations**, not causal
relationships. Specifically:

- Search adoption and conversion: Users who search may have **higher intent** to
  begin with. Search does not necessarily *cause* higher conversion.
- Device differences: Lower mobile conversion may reflect demographic, behavioral,
  or UX differences — we cannot isolate the cause.
- Channel performance: Source/medium attribution is first-touch only and does not
  capture the full multi-touch journey.

**A randomized controlled experiment is required to establish causation.**

## 4. Limited Time Window

All metrics are bounded by the configured date range (`GA4_START_DATE` to
`GA4_END_DATE`). Implications:

- **Retention:** Users who return outside the window are not counted as retained.
  Week 4+ retention may appear artificially low for later cohorts.
- **LTV:** `total_revenue_usd` in `int_users` is a limited-period revenue proxy,
  not a true Lifetime Value estimate. True LTV requires longer observation,
  churn modeling, and discount rate assumptions.
- **Seasonality:** Short time ranges may not capture seasonal patterns (e.g.,
  holiday shopping).

## 5. Channel Attribution Caveats

`traffic_source` in GA4 represents **first-touch attribution** — the source that
first brought the user to the property. It does NOT:

- Capture subsequent touchpoints (display ads, email, organic return visits)
- Account for view-through attribution
- Represent the source of the specific converting session

This is a known limitation of the GA4 public dataset schema.

## 6. Transaction Completeness

Some purchase events may have:

- NULL `transaction_id` → excluded from `int_orders`
- NULL `ecommerce_purchase_revenue` → treated as $0
- Duplicate `transaction_id` across multiple purchase events → deduplicated

Total revenue in `int_orders` may **understate** actual revenue if purchase events
lack identifiers or revenue values.

## 7. Acquisition Attributes

First device category and source/medium in `int_users` are taken from the user's
**earliest observed session** in the data window. This may not be their true first
visit if it occurred before the data window starts.

## 8. Sequential Funnel Strictness

The `int_session_funnel` model enforces strict temporal ordering:
`view_item → add_to_cart → begin_checkout → purchase`. This is a deliberate
analytical choice that excludes:

- Users who add to cart from a list view without clicking into a product page
- Users who return to a saved cart and complete checkout
- Cross-session purchase journeys

For non-sequential presence-based funnel flags, use `int_sessions` instead.

## 9. No Qualitative Context

This analysis is purely quantitative. We lack:

- User interviews or surveys
- Session recordings or heatmaps
- Customer support ticket analysis
- Product team context on recent changes
- Competitive intelligence

Quantitative findings should always be **triangulated with qualitative research**
before making product decisions.

## 10. Not Real-Time

This is a **batch analytics** project using historical daily event exports. It
does not represent real-time data. The pipeline is designed for periodic (daily)
batch execution, not streaming analysis.
