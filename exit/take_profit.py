from typing import Dict, Any, Optional
from datetime import datetime
from herald.exit.base import ExitStrategy
from herald.exit.exit_manager import ExitDecision
from herald.position.manager import PositionInfo


class TakeProfitExit(ExitStrategy):
    """Simple take profit strategy, legacy-compatible.

    Accepts `take_profit_pct` kwarg or uses `position.take_profit` if set.
    """

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            params = args[0]
        else:
            params = kwargs
        super().__init__(name='TakeProfitExit', params=params, priority=2)
        self.take_profit_pct = params.get('take_profit_pct', None)

    def should_exit(self, position: PositionInfo, current_data: Dict[str, Any] = None) -> Optional[ExitDecision]:
        current_price = current_data.get('current_price') if current_data else position.current_price
        if current_price is None:
            return ExitDecision(False, self.name, reason='no price', priority=self.priority)

        if self.take_profit_pct is not None:
            if position.side == 'BUY' and current_price >= position.open_price * (1 + self.take_profit_pct):
                return ExitDecision(should_exit=True, strategy_name=self.name, reason='Take profit hit', priority=self.priority, exit_price=current_price, timestamp=datetime.now())
            if position.side == 'SELL' and current_price <= position.open_price * (1 - self.take_profit_pct):
                return ExitSignal(ticket=position.ticket, reason='Take profit hit', price=current_price, timestamp=datetime.now(), strategy_name=self.name)

        # Or use explicit position.take_profit if provided
        if position.take_profit and position.take_profit > 0:
            if position.side == 'BUY' and current_price >= position.take_profit:
                return ExitDecision(should_exit=True, strategy_name=self.name, reason='Take profit reached', priority=self.priority, exit_price=current_price, timestamp=datetime.now())
            if position.side == 'SELL' and current_price <= position.take_profit:
                return ExitSignal(ticket=position.ticket, reason='Take profit reached', price=current_price, timestamp=datetime.now(), strategy_name=self.name)

        return ExitDecision(False, self.name, reason='no exit', priority=self.priority)
