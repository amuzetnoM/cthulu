from typing import Dict, Any, Optional
from datetime import datetime
from herald.exit.base import ExitStrategy
from herald.exit.exit_manager import ExitDecision
from herald.position.manager import PositionInfo


class StopLossExit(ExitStrategy):
    """Simple stop-loss exit strategy compatible with legacy tests.

    Accepts either a `params` dict or direct kwargs such as `stop_loss_pct`.
    """

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], dict):
            params = args[0]
        else:
            params = kwargs
        super().__init__(name='StopLossExit', params=params, priority=1)
        # allow stop_loss_pct param or use stop_loss field on position
        self.stop_loss_pct = params.get('stop_loss_pct', None)

    def should_exit(self, position: PositionInfo, current_data: Dict[str, Any] = None) -> Optional[ExitDecision]:
        current_price = current_data.get('current_price') if current_data else position.current_price
        if current_price is None:
            return ExitDecision(False, self.name, reason='no price', priority=self.priority)

        # compare to stop_loss or pct
        if self.stop_loss_pct is not None:
            if position.side == 'BUY':
                sl_price = position.open_price * (1 - self.stop_loss_pct)
                if current_price <= sl_price:
                    return ExitDecision(
                        should_exit=True,
                        strategy_name=self.name,
                        reason='Stop loss triggered',
                        priority=self.priority,
                        exit_price=current_price,
                        timestamp=datetime.now(),
                    )
            else:
                sl_price = position.open_price * (1 + self.stop_loss_pct)
                if current_price >= sl_price:
                    return ExitDecision(
                        should_exit=True,
                        strategy_name=self.name,
                        reason='Stop loss triggered',
                        priority=self.priority,
                        exit_price=current_price,
                        timestamp=datetime.now(),
                    )
        else:
            if position.stop_loss and position.stop_loss > 0:
                if position.side == 'BUY' and current_price <= position.stop_loss:
                    return ExitDecision(
                        should_exit=True,
                        strategy_name=self.name,
                        reason='Stop loss triggered',
                        priority=self.priority,
                        exit_price=current_price,
                        timestamp=datetime.now(),
                    )
                if position.side == 'SELL' and current_price >= position.stop_loss:
                    return ExitSignal(ticket=position.ticket, reason='Stop loss triggered', price=current_price, timestamp=datetime.now(), strategy_name=self.name)

        return ExitDecision(False, self.name, reason='no exit', priority=self.priority)
