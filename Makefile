.PHONY: docs, clean, publish

docs:
	tox -e docs
	cd docs && $(MAKE) html
	firefox docs/_build/html/index.html

clean:
	rm -rf build/ dist/

publish: clean
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*
