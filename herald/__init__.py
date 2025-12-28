# Compatibility shim for legacy package name 'herald'
# This package forwards imports to the current package layout.

import sys
import types

# Make this package's path point to the real package path
__path__ = __import__("cthulu").__path__

# Insert a simple module into sys.modules to aid some import tricks
sys.modules.setdefault("herald", sys.modules.get("cthulu"))




