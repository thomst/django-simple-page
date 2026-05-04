# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import django

sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../tests'))

from simple_page.__version__ import __version__

os.environ["DJANGO_SETTINGS_MODULE"] = "test_project.settings"
django.setup()


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'django-simple-page'
copyright = '2026, Thomas Leichtfuß'
author = 'Thomas Leichtfuß'
version = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']

# autodoc-configuration
autoclass_content = 'class'
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'exclude-members': 'DoesNotExist,MultipleObjectsReturned,NotUpdated',
    'show-inheritance': True,
}

# intersphinx-config
intersphinx_mapping = {
    'django': ('https://docs.djangoproject.com/en/stable/', 'http://docs.djangoproject.com/en/stable/_objects/'),
    }
