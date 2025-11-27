# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# -- Project information -----------------------------------------------------
project = "bme280pi"
author = "MarcoAndreaBuchmann"
master_doc = "index"

import tomllib  # Python 3.11+ (or use 'tomli' on older versions)

with open(os.path.abspath("../../pyproject.toml"), "rb") as f:
    data = tomllib.load(f)
release = data["project"]["version"]

version = release

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "IPython.sphinxext.ipython_console_highlighting",
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.jquery",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
]

# Nice typehints style
autodoc_typehints = "description"
autodoc_typehints_description_target = "all"

# Force MathJax 3 from CDN (this works 100% of the time)
html_js_files = [
    "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js",
]

# Best MathJax 3 config (modern, fast, beautiful)
mathjax3_config = {
    "tex": {"inlineMath": [["$", "$"], ["\\(", "\\)"]]},
    "svg": {"fontCache": "global"},
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns: list[str] = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
html_static_path = ["_static"]

html_title = "hftbacktest"
html_extra_path = ["_html"]

add_module_names = False
autosummary_generate = True
autodoc_typehints = "description"
keep_warnings = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.10/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}
