# Compatibility shim: provide legacy-capitalized package name 'Cthulu'
# and re-export the contents of the 'cthulu' package so tests and older code
# that import `Cthulu.something` continue to work.
import importlib as _importlib
import sys as _sys
import logging as _logging
_logger = _logging.getLogger(__name__) 

_cth = _importlib.import_module('cthulu')

# Copy attributes from cthulu top-level module into this module namespace
for _name in dir(_cth):
    if _name.startswith('_'):
        continue
    try:
        globals()[_name] = getattr(_cth, _name)
    except Exception as e:
        # Best-effort: skip attributes that raise on access
        _logger.debug("Skipping attribute %s during Cthulu shim due to: %s", _name, e, exc_info=True)

# Ensure subpackages like Cthulu.config map to cthulu.config
try:
    _cfg = _importlib.import_module('cthulu.config')
    globals()['config'] = _cfg
    _sys.modules['Cthulu.config'] = _cfg
except Exception as e:
    _logger.debug("Failed to create Cthulu.config shim: %s", e, exc_info=True)

# Register this module in sys.modules with the legacy name to help importlib
_sys.modules['Cthulu'] = _sys.modules.get('Cthulu') or _sys.modules.get('cthulu')
