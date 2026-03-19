"""Make the ``reports3gpp`` directory a proper Python package.

The test suite imports modules via a top‑level ``src`` package. Those modules live
under ``reports3gpp/src``. By turning ``reports3gpp`` into a package we can
re‑export the real implementations from a thin shim located at the repository
root ``src`` directory.
"""
