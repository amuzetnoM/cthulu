from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class ExitDecision:
    should_exit: bool
    strategy_name: str
    reason: str
    priority: int
    exit_price: Optional[float] = None
    partial_volume: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: dict = None


class ExitStrategyManager:
    """Simple orchestrator for exit strategies; evaluates in priority order and returns the highest priority decision."""

    def __init__(self):
        self.strategies = []

    def register(self, strategy):
        self.strategies.append(strategy)
        # Sort ascending by priority (lower number = higher urgency)
        self.strategies.sort(key=lambda x: getattr(x, 'priority', 50))

    def evaluate_exit(self, position, current_data=None) -> Optional[ExitDecision]:
        """Run strategies in priority order and return first exit decision.

        Args:
            position: PositionInfo
            current_data: optional market data dictionary
        """
        current_data = current_data or {}
        best_decision = None
        for strat in self.strategies:
            try:
                decision = strat.should_exit(position, current_data)
                if decision is not None:
                    # Wrap in ExitDecision dataclass
                    ed = ExitDecision(
                        should_exit=True,
                        strategy_name=str(decision.strategy_name),
                        reason=decision.reason,
                        priority=getattr(decision, 'priority', getattr(strat, 'priority', 50)),
                        exit_price=getattr(decision, 'price', None),
                        partial_volume=getattr(decision, 'partial_volume', None),
                        timestamp=getattr(decision, 'timestamp', None),
                        metadata=getattr(decision, 'metadata', None)
                    )
                    # Pick the highest urgency (lower numeric priority)
                    if best_decision is None or ed.priority < best_decision.priority:
                        best_decision = ed
            except Exception:
                continue
        return best_decision
