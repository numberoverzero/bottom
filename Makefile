.PHONY: help clean dev lint test docs docs-view build publish pr-check

PY_VERSION = 3.12
BROWSER ?= browser

help:
	@echo "Available targets:"
	@echo "  help: this help text"
	@echo "  dev: configure dev environment; recreates .venv"
	@echo "  lint: linting, formatting, and type checking"
	@echo "  test: run unit tests"
	@echo "  docs: build docs locally"
	@echo "  build: build .tgz and .whl packages"
	@echo "  publish: upload built .tgz and .whl to public PyPi via twine"
	@echo "  pr-check: please run before submitting a pr"

dev:
	rm -rf .venv
	python${PY_VERSION} -m venv .venv --copies
	.venv/bin/pip install -U pip
	.venv/bin/pip install -e . --group dev

lint:
	.venv/bin/pip install -q --group lint
	.venv/bin/ruff check --fix
	.venv/bin/ty check

test: lint
	rm -rf .coverage .pytest_cache
	.venv/bin/pip install -q --group test
	# https://docs.python.org/3/library/devmode.html#effects-of-the-python-development-mode
	# show all warnings, enable asyncio debug mode
	.venv/bin/python -X dev -m coverage run --branch --source=src/bottom -m pytest -vvv -s
	.venv/bin/coverage report -m

docs:
	@echo RUNNING DOCS
	rm -rf docs/_build
	.venv/bin/pip install -q --group docs
	.venv/bin/python -m sphinx -b linkcheck -D linkcheck_timeout=1 docs/ docs/_build/linkcheck
	.venv/bin/python -m sphinx -T -b html -d docs/_build/doctrees -D language=en docs/ docs/_build/html

docs-view: docs
	${BROWSER} docs/_build/html/index.html

build: lint test
	rm -rf dist/
	.venv/bin/pip install -q --group dist
	.venv/bin/python -m build
	.venv/bin/twine check dist/*

publish: lint test build docs
	.venv/bin/twine upload dist/*

pr-check: lint test build docs docs-view
	@echo "please review the rendered docs before creating a PR"
