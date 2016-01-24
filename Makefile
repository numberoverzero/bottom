.PHONY: docs

docs:
	cd docs && $(MAKE) html
	firefox docs/_build/html/index.html
