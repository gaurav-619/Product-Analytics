# Simulated Experiment Methodology

> **SIMULATED EXPERIMENT DATA**  
> This document explains the educational demonstration of experimentation analysis. This is not GA4 data and is not evidence of real business impact.

## 1. Why Synthetic Data?
The core dataset used in this portfolio is Google's public GA4 ecommerce dataset. This real-world dataset represents historical, observational data. 

While observational data is excellent for descriptive analytics (e.g., funnel drop-offs, user segmentation), it **does not contain verified randomized treatment and control assignments**. Claiming that observational data proves a product change caused a metric increase is a fundamental analytical error.

To demonstrate rigorous A/B testing capabilities—including experiment design, statistical power analysis, guardrail evaluation, and causal inference—I built a visibly separate synthetic experiment module. This ensures the integrity of the observational pipeline while still showcasing Product Science skills.

## 2. Observational vs. Causal Inference
- **Observational Analysis (GA4 Data):** "We observe that users who engage with site search convert at a 3x higher rate." This is correlation. Users who search likely have higher purchase intent.
- **Causal Experimentation (Synthetic Data):** "We randomly assigned users to see a simplified checkout. We controlled for all outside variables. Therefore, the observed lift in conversion was *caused* by the simplification."

## 3. Key Concepts Demonstrated
The simulation script (`analyze_checkout_experiment.py`) evaluates the synthetic data using standard industry practices:

- **Random Assignment:** Ensures the Control and Treatment groups are statistically identical before the intervention.
- **Sample Ratio Mismatch (SRM):** A Chi-square test is run to verify the intended 50/50 allocation actually occurred.
- **Primary Metric:** A predefined success metric (e.g., Conversion Rate) evaluated using a two-proportion z-test.
- **Confidence Intervals:** 95% CIs are calculated to show the probable range of the true absolute lift.
- **Guardrails:** Secondary metrics (e.g., Payment Errors, Refunds) that must not significantly degrade. A positive primary lift with failing guardrails requires iteration, not launch.
- **Practical Significance (MDE):** Statistical significance (p < 0.05) is not enough. The lift must also exceed a Minimum Detectable Effect (MDE) to justify the engineering and maintenance costs of shipping.

## 4. Why p-value alone is not enough
The decision matrix in the analysis script evaluates multiple conditions before recommending a "Ship" decision:
1. Is the lift positive?
2. Is the 95% confidence interval lower bound > 0? (Statistical significance)
3. Does the lift exceed the Minimum Practical Lift? (Practical significance)
4. Did the payment error rate stay within the threshold? (Guardrail)
5. Did the refund rate stay within the threshold? (Guardrail)

A low p-value only proves that the groups are different. It does not prove the difference is large enough to matter, nor does it guarantee the change didn't break something else.

## 5. Disclaimer
All results generated in the `artifacts/simulated_experiment/` directory are deterministic synthetic outputs. They cannot be used as claims of business impact.
