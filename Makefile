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
	uv sync --all-extras --group dev

lint:
	uv run --group lint ruff check --fix
	uv run --group lint ty check -v

test: lint
	rm -rf .coverage .pytest_cache

	# https://docs.python.org/3/library/devmode.html#effects-of-the-python-development-mode
	# show all warnings, enable asyncio debug mode
	uv run --group test python -X dev -m coverage run --branch --source=src/bottom -m pytest -vvv -s
	uv run --group test coverage report -m

docs:
	@echo RUNNING DOCS
	rm -rf docs/_build
	uv run --group docs -m sphinx -W -n --keep-going -b linkcheck -D linkcheck_timeout=1 docs/ docs/_build/linkcheck
	uv run --group docs -m sphinx -W -n --keep-going -T -b html -d docs/_build/doctrees -D language=en docs/ docs/_build/html

docs-view: docs
	${BROWSER} docs/_build/html/index.html

build: lint test
	rm -rf dist/
	uv build
	uv run --group dist twine check dist/*

publish: lint test build docs
	uv run --group dist twine upload --repository bottom dist/*

pr-check: lint test build docs docs-view
	@echo "please review the rendered docs before creating a PR"
