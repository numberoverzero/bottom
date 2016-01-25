import sys
import alabaster
import pkg_resources

extensions = [
    'alabaster',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon'
]

default_role = "any"

templates_path = ['_templates']
source_suffix = '.rst'

master_doc = 'index'

project = 'bottom'
copyright = '2016, Joe Cross'
author = 'Joe Cross'


try:
    release = pkg_resources.get_distribution('bottom').version
except pkg_resources.DistributionNotFound:
    print('To build the documentation, The distribution information of bottom')
    print('Has to be available.  Either install the package into your')
    print('development environment or run "setup.py develop" to setup the')
    print('metadata.  A virtualenv is recommended!')
    sys.exit(1)
del pkg_resources
version = '.'.join(release.split('.')[:2])

language = 'en'

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme = 'alabaster'

html_theme_options = {
    'github_user': 'numberoverzero',
    'github_repo': 'bottom',
    'github_banner': True,
    'travis_button': True,
    'show_powered_by': False,
    'analytics_id': 'UA-65843067-2'
}
html_theme_path = [alabaster.get_path()]
html_static_path = []
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html'
    ]
}
