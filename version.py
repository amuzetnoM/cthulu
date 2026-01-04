"""
Cthulu Version Information

Android Native Edition
"""

__version__ = "1.0.0-beta"
__version_info__ = (1, 0, 0, "beta")
__edition__ = "Android Native"
__codename__ = "Termux"

VERSION = __version__
EDITION = __edition__

def get_version_string() -> str:
    """Get formatted version string."""
    return f"Cthulu v{__version__} ({__edition__})"

def get_version_tuple() -> tuple:
    """Get version as tuple."""
    return __version_info__
