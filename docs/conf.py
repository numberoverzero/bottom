import importlib.metadata
import sys
import typing as t

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]

master_doc = "index"

project = "bottom"
copyright = "2025, numberoverzero"
author = "numberoverzero"

try:
    release = importlib.metadata.version("bottom")
except importlib.metadata.PackageNotFoundError:
    print("To build the documentation, The distribution information of bottom")
    print("Has to be available.  Either install the package into your")
    print('development environment or run "setup.py develop" to setup the')
    print("metadata.  A virtualenv is recommended!")
    sys.exit(1)
del importlib.metadata
version = ".".join(release.split(".")[:2])

language = "en"
exclude_patterns = ["_build"]

pygments_style = "sphinx"
html_use_smartypants = False
html_static_path = ["_static"]
html_theme = "sphinx_rtd_theme"
html_context = {"favicon": "favicon-cog.ico", "show_sphinx": False}

intersphinx_mapping = {
    "py": ("https://docs.python.org/3.12", None),
}

linkcheck_timeout = 5
linkcheck_retries = 2
linkcheck_allowed_redirects = {
    r"https://github\.com/.*": r"https://github\.com/login\?return_to=.*",
}
linkcheck_anchors_ignore_for_url = [
    "https://pypi.org/project/.*",
]
# https://www.useragents.me/
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.10 Safari/605.1.1"

nitpick_ignore = [
    ("py:class", "_asyncio.Task"),
    ("py:class", "P"),
    ("py:class", "R"),
    ("py:class", "t.Callable"),
    ("py:class", "util.Decorator"),
    ("py:class", "ClientMessageHandler"),
    ("py:class", "Component"),
    ("py:class", "ComputedStr"),
]


def setup(app: Sphinx) -> None:
    app.add_css_file("bottom.css")
