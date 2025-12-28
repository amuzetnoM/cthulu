__all__ = [
    "config",
    "connector",
    "execution",
    "indicators",
    "market",
    "persistence",
    "position",
    "risk",
    "strategy",
    "utils",
]

# Lazy imports to avoid heavy import-time side-effects
_LAZY_IMPORTS = {
    "config": "cthulu.config",
    "connector": "cthulu.connector",
    "execution": "cthulu.execution",
    "indicators": "cthulu.indicators",
    "market": "cthulu.market",
    "persistence": "cthulu.persistence",
    "position": "cthulu.position",
    "risk": "cthulu.risk",
    "strategy": "cthulu.strategy",
    "utils": "cthulu.utils",
}

def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name])
        globals()[name] = module
        return module
    raise AttributeError(name)


# Back-compat shim for legacy package name 'herald'
def _install_herald_shim():
    try:
        import types
        pkg_name = "herald"
        if pkg_name in sys.modules:
            return
        mod = types.ModuleType(pkg_name)
        mod.__path__ = __path__
        sys.modules[pkg_name] = mod
    except Exception:
        pass

_install_herald_shim()

def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_IMPORTS.keys()))




