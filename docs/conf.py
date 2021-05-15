# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import pathlib
import sys

from scribe import __version__  # noqa

sys.path.insert(0, str(pathlib.Path(__file__).parent.absolute() / ".."))


# -- Project information -----------------------------------------------------

project = "scribe"
copyright = "2021, Ludovic Tiako"
author = "Ludovic Tiako"
version = __version__
release = __version__

# Enable nitpicky mode - which ensures that all references in the docs resolve.
nitpicky = True
nitpick_ignore = []
for line in open("nitpick-ignore"):
    if line.strip() == "" or line.startswith("#"):
        continue
    dtype, target = line.split(None, 1)
    target = target.strip()
    nitpick_ignore.append((dtype, target))


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",  # this MUST be after napoleon https://github.com/agronholm/sphinx-autodoc-typehints/issues/15  # noqa
    "sphinx.ext.intersphinx",
]
highlight_language = "python3"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "build",
    "Thumbs.db",
    ".DS_Store",
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_title = f"{project} v{release}"
html_theme_options = {"navigation_with_keys": True}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["static"]


# -- Extension configuration -------------------------------------------------
# -- Options for intersphinx extension ---------------------------------------


intersphinx_mapping = {
    "python": ("https://docs.python.org/3.7/", None),
}
