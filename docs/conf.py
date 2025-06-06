import sys

import pkg_resources

extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx", "sphinx.ext.viewcode", "sphinx.ext.napoleon"]

templates_path = ["_templates"]

master_doc = "index"

project = "bottom"
copyright = "2025, numberoverzero"
author = "numberoverzero"

try:
    release = pkg_resources.get_distribution("bottom").version
except pkg_resources.DistributionNotFound:
    print("To build the documentation, The distribution information of bottom")
    print("Has to be available.  Either install the package into your")
    print('development environment or run "setup.py develop" to setup the')
    print("metadata.  A virtualenv is recommended!")
    sys.exit(1)
del pkg_resources
version = ".".join(release.split(".")[:2])

language = "en"
exclude_patterns = ["_build"]

pygments_style = "sphinx"
html_use_smartypants = False
html_static_path = ["_static"]
html_theme = "sphinx_rtd_theme"
html_context = {"favicon": "favicon-cog.ico", "show_sphinx": False}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.11", None),
}


def setup(app):
    app.add_css_file("bottom.css")
