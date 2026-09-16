# Metric Definitions

All metrics in this project are defined below with their grain, formula, and caveats.

---

## User and Session Metrics

### Active User
- **Definition:** A distinct `user_pseudo_id` with at least one event in the period
- **Grain:** Daily (in mart_product_kpis_daily)
- **Caveat:** `user_pseudo_id` is device/browser-level. Same person on multiple devices = multiple users.

### Session
- **Definition:** A group of events sharing the same `session_key` (user_pseudo_id + ga_session_id)
- **Grain:** One per unique session_key
- **Caveat:** Events without a `ga_session_id` are excluded from session-level analysis

### Purchaser
- **Definition:** A distinct `user_pseudo_id` with at least one `purchase` event in the period
- **Grain:** Daily (in KPIs), lifetime (in int_users)

---

## Conversion Metrics

### Session Conversion Rate
- **Numerator:** Sessions with at least one purchase event
- **Denominator:** Total sessions
- **Formula:** `SAFE_DIVIDE(purchase_sessions, total_sessions)`
- **Caveat:** Non-sequential presence-based metric

### User Conversion Rate
- **Numerator:** Distinct purchasers (users with purchase event)
- **Denominator:** Total distinct active users
- **Formula:** `SAFE_DIVIDE(daily_purchasers, daily_active_users)`

---

## Funnel Metrics

### Sequential Funnel Stage Rates
Each rate measures the proportion of sessions progressing from one step to the next, enforcing strict temporal ordering within the session.

| Step Transition | Numerator | Denominator |
|----------------|-----------|-------------|
| Session → Product View | Sessions with `view_item` | All sessions |
| Product View → Add to Cart | Sessions with `add_to_cart` AFTER `view_item` | Sessions with `view_item` |
| Add to Cart → Checkout | Sessions with `begin_checkout` AFTER `add_to_cart` | Sessions with `add_to_cart` (after view) |
| Checkout → Purchase | Sessions with `purchase` AFTER `begin_checkout` | Sessions with `begin_checkout` (after cart) |

- **Caveat:** This strict sequential funnel is more conservative than presence-based. Sessions where a user adds to cart without viewing a product page are excluded from the cart step.

### Cart Abandonment Rate
- **Formula:** `1 - (sessions_begin_checkout / sessions_add_to_cart)` (sequential)
- **Caveat:** Only counts abandonment in the sequential funnel

---

## Revenue Metrics

### Order Revenue (USD)
- **Source:** `COALESCE(ecommerce_purchase_revenue_in_usd, ecommerce_purchase_revenue, 0)`
- **Grain:** Per deduplicated transaction in int_orders
- **Caveat:** Some purchase events may have NULL revenue. These contribute $0 to totals.

### Average Order Value (AOV)
- **Numerator:** Total revenue (USD)
- **Denominator:** Total orders (distinct transaction keys)
- **Formula:** `SAFE_DIVIDE(total_revenue_usd, total_orders)`

### Revenue Per Session
- **Numerator:** Total revenue (USD)
- **Denominator:** Total sessions
- **Formula:** `SAFE_DIVIDE(total_revenue_usd, total_sessions)`

---

## Retention Metrics

### Weekly Activity Retention Rate
- **Definition:** Proportion of users in a cohort who had at least one session in a given week
- **Cohort:** Defined by the ISO week of a user's first observed session
- **Week 0:** The cohort week itself (always 100%)
- **Week N:** N weeks after the cohort week
- **Formula:** `SAFE_DIVIDE(retained_users, cohort_size)`
- **Caveat:** This is observed activity retention within the data window. It is NOT a lifetime retention estimate. Users who return outside the window are not counted.

### Repeat Purchase Rate
- **Definition:** Proportion of purchasers with more than one order
- **Available in:** `int_users` (order_count > 1 / total purchasers)
- **Caveat:** Bounded by the data window

---

## RFM Metrics

### Recency
- **Definition:** Days between the customer's last order and the analysis reference date
- **Reference date:** `MAX(order_date)` in the dataset
- **Scoring:** `NTILE(5)` — Score 5 = most recent (lowest recency_days)
- **Caveat:** Not calculated from current date since data is historical

### Frequency
- **Definition:** Count of distinct orders per customer
- **Scoring:** `NTILE(5)` — Score 5 = most frequent

### Monetary Value
- **Definition:** Total order revenue (USD) per customer
- **Scoring:** `NTILE(5)` — Score 5 = highest value

### RFM Segments

| Segment | Rule |
|---------|------|
| Champions | R≥4, F≥4, M≥4 |
| Loyal Customers | F≥4, R≥3 |
| Potential Loyalists | R≥4, 2≤F≤3 |
| Recent Customers | R≥4, F=1 |
| At Risk | R≤2, F≥3 |
| Occasional Customers | Everyone else |

---

## Limited-Period LTV Proxy

- **Definition:** Total revenue per user within the observation window
- **Available in:** `int_users.total_revenue_usd`
- **⚠️ This is NOT true Lifetime Value.** It is a revenue proxy bounded by the data window. True LTV requires longer observation periods, churn modeling, and discount rate assumptions.

---

## Search Adoption Metrics

### Search Session
- **Definition:** A session containing a `view_search_results` event (has_search = TRUE)
- **Logic:** Derived from the `has_search` flag in `int_sessions`
- **⚠️ Association only:** Higher conversion in search sessions does not mean search *causes* conversion. Users who search may have higher purchase intent to begin with.

### Search Adoption Rate
- **Formula:** `SAFE_DIVIDE(sessions_with_search, total_sessions)`

---

## Notes

- All rates use `SAFE_DIVIDE` to prevent division-by-zero errors
- Revenue is consistently in USD throughout the marts
- Daily KPIs sum session-level metrics; user-day counts may exceed distinct users when a user is active on multiple days
