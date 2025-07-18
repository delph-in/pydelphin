#!/usr/bin/env python3

# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.join(os.path.abspath('.'), '_extensions'))
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

import delphin.__about__

project = delphin.__about__.__title__
copyright = u'2020, Michael Wayne Goodman'
author = delphin.__about__.__author__

# The short X.Y version
version = '.'.join(delphin.__about__.__version_info__[:2])
# The full version, including alpha/beta/rc tags
release = delphin.__about__.__version__


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.napoleon',
    'sphinx_copybutton',
    'wiki',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = ['env', u'_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

from sphinx.highlighting import lexers

from delphin.highlight import SimpleMRSLexer, TDLLexer

lexers['tdl'] = TDLLexer(startinline=True)
lexers['simplemrs'] = SimpleMRSLexer(startinline=True)

# Global definitions
rst_prolog = """
.. role:: python(code)
   :language: python

.. default-role:: python
"""

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'
#html_theme = 'classic'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'PyDelphindoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'PyDelphin.tex', u'PyDelphin Documentation',
     u'Michael Wayne Goodman', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'pydelphin', u'PyDelphin Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'PyDelphin', u'PyDelphin Documentation',
     author, 'PyDelphin', 'One line description of project.',
     'Miscellaneous'),
]


# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    # 'httpx': ('https://www.python-httpx.org/', None),
    'falcon': ('https://falcon.readthedocs.io/en/2.0.0/', None)
}

# -- Options for Napoleon extension ------------------------------------------

napoleon_use_rtype = False


# -- Options for autodoc extension -------------------------------------------

# disable type hints

autodoc_typehints = 'signature'


# -- Options for sphinx_copybutton extension ---------------------------------

copybutton_prompt_text = (
    r">>> "              # regular Python prompt
    r"|\.\.\. "          # Python continuation prompt
    r"|\$ "              # Basic shell
    r"|In \[\d*\]: "     # Jupyter notebook
)
copybutton_prompt_is_regexp = True


# -- Options for wikis -------------------------------------------------------

wiki_url = 'https://github.com/delph-in/docs/wiki/'
