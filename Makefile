.PHONY: docs

docs:
	tox -e docs
	cd docs && $(MAKE) html
	firefox docs/_build/html/index.html
