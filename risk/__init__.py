"""Risk management module - Unified Architecture

Single source of truth for all risk evaluation logic.

New structure:
- evaluator.py: Unified risk evaluation (consolidates all previous risk logic)

Legacy modules (deprecated, will be removed):
- manager.py: Replaced by evaluator.py
- position/risk_manager.py: Merged into evaluator.py
"""

from .evaluator import RiskEvaluator, RiskLimits, DailyRiskTracker

# Legacy import for backward compatibility during transition
try:
    from .manager import RiskManager
except ImportError:
    RiskManager = None

__all__ = ["RiskEvaluator", "RiskLimits", "DailyRiskTracker", "RiskManager"]




