.PHONY: setup dbt-debug dbt-build app test lint clean

setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Setup complete. Activate with: source venv/bin/activate (Linux/Mac) or .\\venv\\Scripts\\Activate.ps1 (Windows)"

dbt-debug:
	cd dbt_product_analytics && dbt debug

dbt-build:
	cd dbt_product_analytics && dbt deps && dbt build

app:
	streamlit run app/Home.py

test:
	python -m pytest tests/ -v

simulate-experiment:
	python -m src.simulation.generate_checkout_experiment
	python -m src.simulation.analyze_checkout_experiment

test-experiment:
	pytest tests/test_checkout_experiment.py

lint:
	ruff check src/ app/ tests/

clean:
	rm -rf dbt_product_analytics/target/ dbt_product_analytics/dbt_packages/ dbt_product_analytics/logs/
	rm -rf artifacts/
	rm -f docs/data_quality_report_generated.md docs/verified_findings_generated.md
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned generated files"
