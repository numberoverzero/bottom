.PHONY: docs, publish

docs:
	tox -e docs
	cd docs && $(MAKE) html
	firefox docs/_build/html/index.html

publish:
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*
