sources_dev = pyconfigloader
sources_test = tests

.PHONY: tests format lint unittest coverage pre-commit clean

tests: format lint unittest

pre-commit:
	poetry run pre-commit run --all-files

format:
	poetry run ruff format $(sources_dev) $(sources_test)

lint:
	#poetry run ruff check --add-noqua $(sources)
	poetry run ruff check --fix $(sources_dev) $(sources_test)
	poetry run mypy --ignore-missing-imports $(sources_dev) $(sources_test)

quality:
	poetry run ruff check --output-file ruff-lint-report.txt --exit-zero $(sources_dev) $(sources_test)
	poetry run pylint --output pylint-report.json --exit-zero $(sources_dev)

unittest:
	poetry run pytest -vl --junit-xml="pytest-report.xml"

coverage:
	poetry run pytest --cov=$(sources_dev) --cov-branch --cov-report=term-missing --cov-report=xml:coverage.xml tests

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	rm -rf *.egg-info
	rm -rf .tox dist site
	rm -rf coverage.xml .coverage
	rm -f pylint-report.txt pytest-report.txt pylint-report.json
	find -type d -name __pycache__ -exec rm -r {} +
