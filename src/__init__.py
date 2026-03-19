"""Top‑level ``src`` package shim.

The project's implementation lives in ``reports3gpp/src``. By extending the
package ``__path__`` to include that directory we expose the actual modules
under the ``src`` namespace, satisfying the test suite which imports
``src.downloader`` and ``src.html_parser``.
"""

from pathlib import Path

# The actual source directory is ``reports3gpp/src`` relative to the workspace root.
_real_src = Path(__file__).resolve().parent.parent / "reports3gpp" / "src"
if _real_src.is_dir():
    __path__.append(str(_real_src))
