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
import os
import sys
OUR_MODULE_PATH = os.path.abspath( __file__ )
main_path = os.path.abspath( os.path.join( OUR_MODULE_PATH, '..',
                                '..', 'src' ) )
mhsp2_path = os.path.abspath( os.path.join( OUR_MODULE_PATH, '..',
                                '..', 'src', 'mHSP2' ) )
pymf6_path = os.path.abspath( os.path.join( OUR_MODULE_PATH, '..',
                                '..', 'src', 'pyMF6' ) )
sys.path.append( main_path )
sys.path.append( mhsp2_path )
sys.path.append( pymf6_path )


# -- Project information -----------------------------------------------------

project = 'pyHS2MF6'
copyright = '2021, Nick Martin'
author = 'Nick Martin'

# The full version, including alpha/beta/rc tags
release = '0.1.2'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [ 'sphinx.ext.inheritance_diagram', 
               'sphinx.ext.autodoc', 'sphinx.ext.napoleon', 
               'sphinxfortran.fortran_domain', 
               'sphinxfortran.fortran_autodoc', 'sphinx.ext.githubpages' ]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'agogo'

html_theme_options = {
    "bodyfont": "Optima, sans-serif",
    "headerfont": "Gill Sans, sans-serif"
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']