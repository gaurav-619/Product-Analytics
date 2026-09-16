# Experiment Design: Mobile Checkout Simplification

## 1. Context and Observed GA4 Signal
Observational analysis of the GA4 dataset revealed a significant drop-off between `begin_checkout` and `purchase`. Specifically, mobile users exhibit a lower checkout completion rate compared to desktop users.

## 2. Causal Limitation of Observational Data
The observed gap is descriptive. It does **not** prove that the mobile checkout design causes abandonment. Mobile users may simply have lower purchase intent, or they may use mobile for browsing and desktop for buying. To establish causality, we must run a controlled experiment.

## 3. Product Problem
The current mobile checkout flow requires users to navigate multiple dense form fields and accordions, potentially creating cognitive overload and physical friction on small screens.

## 4. Hypothesis
"If we simplify mobile checkout, then purchase completion among eligible mobile checkout users will increase, because fewer required steps reduce user effort before payment."

## 5. Control and Treatment
- **Control:** The existing mobile checkout flow.
- **Treatment:** A simplified mobile checkout flow with fewer required form fields, a clearer order-price summary, and a faster payment path (e.g., exposed digital wallets).

## 6. Population and Eligibility
- **Target Population:** Anonymous mobile users.
- **Eligibility Rule:** A user becomes eligible when their device category is `mobile`, they trigger the `begin_checkout` event, and they have not previously been assigned to this experiment.

## 7. Randomization and Assignment Persistence
- Random 50/50 assignment.
- Assignment occurs at the user level (`user_pseudo_id`).
- Assignment must persist across sessions to avoid treatment contamination.
- Assignment must occur exactly at the moment of `begin_checkout` exposure, before any outcomes are measured.

## 8. Primary Metric
- **Converted Purchase:** Binary metric (0 or 1). Did the eligible user successfully complete a purchase?

## 9. Secondary Metrics
- **Revenue per User:** The total purchase value generated per eligible user.
- **Checkout Duration:** The time elapsed between `begin_checkout` and `purchase`.

## 10. Guardrails
- **Payment Error Rate:** The proportion of users experiencing a payment decline or validation error.
- **Refund/Cancellation Rate:** The proportion of orders that are subsequently cancelled or refunded.

## 11. Sample Size and Duration Approach
Using a baseline conversion rate of ~5.0%, a minimum practical lift of 0.5 percentage points (MDE), 80% power, and an alpha of 0.05, we require approximately 20,000+ eligible users per variant. Assuming current traffic volumes, this requires running the experiment for 3-4 weeks.

## 12. Analysis Plan
- Run a Sample Ratio Mismatch (SRM) check (Chi-square test) to verify the 50/50 split.
- Compare the primary metric using a two-proportion z-test.
- Calculate 95% confidence intervals for the absolute difference.
- Compare secondary and guardrail metrics using absolute differences.

## 13. Decision Rules
- **Ship:** Conversion lift is positive and statistically significant (CI lower bound > 0), lift meets the MDE, and guardrails are not materially worsened.
- **Iterate:** Conversion improves, but payment errors or refunds increase unacceptably.
- **Stop:** Conversion lift is negative or zero.
- **Inconclusive:** Uncertainty remains too high (e.g., wide confidence intervals overlapping zero).

## 14. Risks
- **Sample Ratio Mismatch (SRM):** Ensure logging fires reliably on both variants.
- **Tracking Gaps:** QA event payloads before launch.
- **Novelty Effects:** Monitor metrics week-over-week.
- **Multiple Comparisons:** Stick to the pre-registered primary metric for decisions.
- **Treatment Contamination:** Ensure persistent cookies.
- **Refund/Payment Effects:** Guardrails prevent shipping a broken payment gateway.

## 15. Required Event Tracking
See the Production Experiment Tracking Specification, rendered below, for full telemetry requirements.

## 16. Limitations
This document details a proposed experiment. The simulation pipeline generates synthetic data based on this design to demonstrate evaluation capabilities.
