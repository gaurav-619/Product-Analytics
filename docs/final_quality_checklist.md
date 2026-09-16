# Final Quality Checklist

Pre-publish quality gates for the Product Analytics Engine repository.

---

## Technical

- [ ] Python virtual environment setup works (`python -m venv venv`)
- [ ] Dependencies install successfully (`pip install -r requirements.txt`)
- [ ] `python -m compileall src/ app/ tests/` passes with no errors
- [ ] dbt dependencies install (`dbt deps`)
- [ ] `dbt debug` passes with no errors
- [ ] `dbt build` passes — all models created, all tests passing
- [ ] `python -m src.data_quality.generate_quality_report` runs
- [ ] `python -m src.analysis.generate_verified_findings` runs
- [ ] `python -m src.simulation.generate_checkout_experiment` runs
- [ ] `python -m src.simulation.analyze_checkout_experiment` runs
- [ ] `pytest tests/test_checkout_experiment.py` passes
- [ ] `streamlit run app/Home.py` launches without errors
- [ ] All 6 dashboard pages load and display data

---

## Product Analytics

- [ ] Every displayed metric has a documented definition (see `docs/metric_definitions.md`)
- [ ] Funnel is sequential and session-based
- [ ] Revenue is deduplicated at transaction grain
- [ ] Retention is clearly limited to the ~92-day dataset window
- [ ] RFM is descriptive, not predictive
- [ ] GA4 findings use descriptive/observational language (no causal claims)
- [ ] Experiment proposal explains causal limitation of observational data
- [ ] Synthetic results are clearly labeled and visually separated from GA4 data

---

## Portfolio & Professionalism

- [ ] README is scannable in under 3 minutes
- [ ] Screenshots have correct relative paths and alt text (after capture)
- [ ] Architecture diagram renders (Mermaid in README)
- [ ] dbt lineage instructions are clear
- [ ] No hard-coded or fabricated findings
- [ ] No secrets, credentials, or personal data in any committed file
- [ ] No references to CookiePulse, Cookie Cats, or other projects
- [ ] No mentions of Claude, ChatGPT, AI assistance, or prompts
- [ ] No absolute local paths in committed files
- [ ] No localhost links in README or documentation
- [ ] GitHub repository has a clear MIT license
- [ ] Resume bullets reference real capabilities, not fabricated numbers
- [ ] Interview explanation is consistent with the repository contents
- [ ] `.gitignore` blocks `.env`, `venv/`, credentials, generated artifacts
- [ ] CI workflow does not require real GCP credentials

---

## Pre-Commit Verification Commands

```powershell
# Check for old project references
Get-ChildItem -Recurse -File | Select-String -Pattern "CookiePulse|cookiepulse|cookie_pulse|Cookie.Cats" -CaseSensitive:$false

# Check Python syntax
python -m compileall src/ app/ tests/

# Run tests
pytest tests/ -v

# Check git status
git status
git diff --check
```
