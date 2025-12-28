"""Compatibility shim package named ``cthulu``.

This package points its import path to the project root so that imports
like ``cthulu.connector`` resolve to the modules in the repo (which live
in the directory named ``cthulu``). This keeps the original filesystem
layout while satisfying imports that use the single-H name.
"""
import os

# Make this package's search path include the project root (parent dir).
# That allows `import cthulu.connector` to find `connector/` under the
# repository root even though the folder is named `cthulu`.
__path__ = [os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))]

