"""exit module."""
from .coordinator import ExitCoordinator, ExitSignal, TrailingStop as CoordinatorTrailingStop
from .trailing_stop import TrailingStop

__all__ = ['ExitCoordinator', 'ExitSignal', 'TrailingStop']
