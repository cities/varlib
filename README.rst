varlib
======

.. image:: https://travis-ci.org/cities/varlib.svg
   :target: https://travis-ci.org/cities/varlib


.. image:: https://coveralls.io/repos/github/cities/varlib/badge.svg?branch=master
   :target: https://coveralls.io/github/cities/varlib?branch=master

A variable library Python package with CLI and test suite included with the following features:

- Succinct variable definitions in yaml format
- Automatic detecting variable dependencies and building of a dependency graph
- Automatic dependency checking for variables and computing variable and their dependencies on demand
- Lazy re-computating - recompute a variable only if necessary (the first time, on update of dependencies, or when forced)
   
**Work-in-progress** some features may not be working yet.

Installation
-------------

To use varlib, do the following, preferably in
a virtual environment. Clone the repo.

.. code-block:: console

    git clone https://github.com/cities/varlib 
    cd varlib

Then install in locally editable (``-e``) mode and run the tests.

.. code-block:: console

    pip install -e .[test]
    py.test

The python notebook in example/demo.ipynb demostrates the main functions of the package.

Finally, give the command line program a try.

.. code-block:: console

    varlib --help
    varlib example/variables.py

Acknowledgements
----------------

- python package pyskel by Sean Gillies <http://github.com/mapbox/pyskel> was used to initialize this package.

