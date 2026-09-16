# Interview Guide

## 90-Second Explanation

> "I built an end-to-end product analytics engine using real ecommerce event data
> from the Google Merchandise Store — their public GA4 dataset in BigQuery. I used
> dbt to transform nested event-level data into clean session, user, and order models,
> then built mart tables for funnel analysis, cohort retention, RFM customer
> segmentation, and daily KPIs. The Streamlit dashboard lets stakeholders explore
> conversion funnels, identify where users drop off, compare device and channel
> segments, and see which customer segments drive the most revenue. Because the
> GA4 dataset is purely observational, I designed a rigorous experiment proposal 
> and built a visibly separate synthetic simulation module to demonstrate my 
> capabilities in A/B test design, statistical power analysis, and causal inference.
> The entire pipeline is tested, documented, and version-controlled."

---

## 3–5 Minute Walkthrough

### Opening (30 seconds)
"This project answers a simple question that every PM cares about: Where are we
losing users, and what should we build next to grow revenue?"

### Data & Engineering (60 seconds)
"I used Google's public GA4 dataset — real clickstream data from the Google
Merchandise Store. The challenge is that GA4 data is deeply nested — event parameters,
items arrays, device structs. I built a dbt pipeline that flattens this into clean
analytical models: sessions, users, orders, and a strict sequential funnel."

### Analysis (60 seconds)
"The funnel analysis shows where the biggest drop-offs happen. I compare this across
devices — for instance, mobile vs desktop conversion. I built RFM segmentation to
identify high-value customers vs. at-risk ones. The retention cohort analysis shows
whether users come back after their first visit."

### Decisions (60 seconds)
"I turn findings into actionable proposals. For example, if I see that sessions with
site search convert at a higher rate, I don't claim search causes conversion — that's
an association. Instead, I design a proper A/B test to validate the hypothesis. The
experiment design includes sample size calculations, guardrail metrics, and decision rules."

### Close (30 seconds)
"Everything is documented: metric definitions, data quality checks, limitations, and
an interview guide. The project demonstrates the full product analyst workflow from
raw data to stakeholder recommendation."

---

## 12 Likely Interview Questions

### 1. "Why did you choose this dataset?"
"I wanted real production data from a recognizable brand. The GA4 public dataset from
the Google Merchandise Store is real clickstream and transaction data with a complex
nested schema — it's the closest thing to working with actual company data without
needing proprietary access."

### 2. "Walk me through your data model."
"I follow the dbt staging-intermediate-marts pattern. Staging flattens the nested GA4
schema. Intermediate models create business entities: sessions, users, orders, and a
sequential funnel. Marts aggregate these for the dashboard — daily KPIs, funnel
performance, retention cohorts, RFM segments, and product performance."

### 3. "How do you construct a session from GA4 events?"
"GA4 stores a `ga_session_id` inside the nested `event_params` array. I extract it
using a custom macro and concatenate it with `user_pseudo_id` to create a composite
`session_key`. Events without a session ID are excluded from session-level analysis."

### 4. "Why did you use a strict sequential funnel?"
"A non-sequential funnel counts any session with a purchase as converting, even if the
user skipped steps. The sequential funnel enforces view → cart → checkout → purchase
in temporal order. This gives a more accurate picture of the intended journey and
reveals where users genuinely drop off in the designed flow."

### 5. "How do you handle revenue deduplication?"
"The same purchase event can fire multiple times with the same transaction ID. I use
`ROW_NUMBER()` partitioned by the transaction key, ordered by timestamp, and keep only
the first occurrence. I also have a reconciliation test that compares total order
revenue to source purchase revenue within a tolerance."

### 6. "What data quality checks do you have?"
"Three layers: dbt schema tests (unique, not_null, accepted values), custom SQL tests
(non-negative revenue, revenue reconciliation), and a Python quality report script
that profiles the source data for null rates, duplicates, and event inventory."

### 7. "You found that search sessions convert higher. Is search driving that?"
"No — that's an observed association, not a causal finding. Users who search likely
have higher purchase intent to begin with. I explicitly label this as an association
and propose a randomized experiment to test whether making search more prominent would
causally increase conversion."

### 8. "Walk me through your experiment design."
"I propose an A/B test where we randomize at the user level, showing a more prominent
search bar to the treatment group. The primary metric is session conversion rate, with
search adoption rate as secondary. I include sample size calculations, a two-week
minimum duration, SRM checks, and pre-registered decision rules."

### 9. "What are the biggest limitations of this analysis?"
"First, the data is obfuscated and sampled — absolute numbers aren't the store's real
KPIs. Second, user_pseudo_id is device-level, so cross-device journeys are missed.
Third, all findings are observational — correlation, not causation. Fourth, retention
is bounded by the data window. And fifth, there's no qualitative context to explain
the quantitative patterns."

### 10. "How would you apply this to a mobile game?"
"The analytical framework is identical. The onboarding funnel becomes install →
tutorial → first action → first purchase. D1/D7/D30 retention replaces weekly cohorts.
RFM segments become whale/dolphin/minnow classification. The statistical methods —
cohort analysis, experiment design, power analysis — transfer directly."

### 11. "What would you do differently with more data?"
"Four things: First, implement cross-device identity resolution for better user
attribution. Second, use a longer time window for reliable LTV and retention analysis.
Third, run actual A/B tests instead of just proposing them. Fourth, integrate
qualitative data — user surveys, support tickets, session recordings — to triangulate
the quantitative findings."

### 12. "How would you present this to a VP of Product?"
"I'd lead with the business question, not the methodology. 'We're losing X% of users
between add-to-cart and checkout — here's what that looks like in revenue terms.' Then
I'd show the segment breakdown and propose a specific experiment. The dashboard is
designed for this kind of stakeholder conversation — each page ends with 'So what?'
observations tied to the data."

---

## Resume Bullets (Fill After Running Queries)

> Replace `[placeholders]` with actual values from `verified_findings_generated.md`

1. Built an end-to-end product analytics pipeline on [X] million GA4 events using
   dbt, BigQuery, and Python — analyzing [Y] sessions and [Z] transactions across
   funnel, retention, segmentation, and monetization dimensions.

2. Identified that [describe the largest funnel drop-off from verified findings]
   representing the primary conversion friction point, and designed a randomized
   experiment proposal with sample size calculations to validate the intervention.

3. Developed an interactive Streamlit executive dashboard surfacing daily KPIs,
   sequential funnel analysis, cohort retention heatmaps, and RFM customer
   segmentation — demonstrating end-to-end analytical ownership from raw event data
   to stakeholder-ready product decisions.

---

## LinkedIn Portfolio Description

> **Product Analytics Engine: Growth, Retention & Monetization**
>
> End-to-end product analytics case study built on real GA4 ecommerce data from the
> Google Merchandise Store public dataset. Demonstrates the full product analyst
> workflow: data modeling with dbt + BigQuery, sequential funnel analysis, cohort
> retention, RFM customer segmentation, experiment design with statistical power
> analysis, and an interactive Streamlit dashboard.
>
> Stack: BigQuery · dbt · Python · Streamlit · Plotly · SQL
>
> [Link to GitHub repo]
