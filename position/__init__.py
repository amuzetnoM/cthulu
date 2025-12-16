"""
Position Management Module

Real-time position tracking, monitoring, and exit detection.
"""

"""Position package exports.

Note: avoid importing submodules at package import time to prevent circular
imports (the `manager` module imports `execution.engine` which imports
other parts of the package). Import concrete classes from their modules
where needed, for example `from herald.position.manager import PositionManager`.
"""

__all__ = [
    # Intentionally empty to avoid eager imports
]
