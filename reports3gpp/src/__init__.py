"""Package marker for the project's source modules.

The test suite expects to import modules via ``src.<module>`` while the current
working directory during test execution is ``reports3gpp``. Adding this file
turns the ``reports3gpp/src`` directory into a proper Python package, allowing
imports such as ``src.downloader`` and ``src.html_parser`` to resolve correctly.
"""
"""Package marker for the project's source modules.

The test suite imports modules using ``src.<module>`` while the current working
directory during test execution is ``reports3gpp``. Adding this ``__init__``
file makes the ``src`` directory a proper Python package so that imports such
as ``src.downloader`` resolve correctly.
"""
"""Top-level package for the 3GPP report generator.

This file makes the ``src`` directory a proper Python package so that test
modules can import ``src.downloader``, ``src.html_parser`` and other modules
using absolute imports.
"""
