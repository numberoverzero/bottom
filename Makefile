.PHONY: help clean dev lint test docs build publish

PY_VERSION = 3.11
BROWSER ?= browser

help:
	@echo "Available targets:"
	@echo "  help: this help text"
	@echo "  clean: remove build artifacts"
	@echo "  dev: configure dev environment; recreates .venv"
	@echo "  lint: linting, formatting, and type checking"
	@echo "  test: unit and integ tests "
	@echo "  docs: build docs and open them in a browser"
	@echo "  build: build .tgz and .whl packages"
	@echo "  publish: upload built .tgz and .whl to public PyPi via twine"

clean:
	rm -rf dist/ docs/_build

dev:
	rm -rf .venv
	python${PY_VERSION} -m venv .venv --copies
	.venv/bin/pip install -U pip
	.venv/bin/pip install -e . --group dev

lint:
	.venv/bin/pip install -q --group lint
	.venv/bin/ruff check --fix
	.venv/bin/ty check

test:
	.venv/bin/pip install -q --group test
	.venv/bin/coverage run --branch --source=src/bottom -m pytest
	.venv/bin/coverage report -m

docs: clean
	.venv/bin/pip install -q --group docs
	cd docs && $(MAKE) html
	${BROWSER} docs/_build/html/index.html
	# TODO test the command that will be run by readthedocs
	# sphinx-build -W -b html -d {envtmpdir}/doctrees . {envtmpdir}/html

build: clean
	.venv/bin/pip install -q --group dist
	.venv/bin/python -m build

publish: build
	.venv/bin/twine upload dist/*
