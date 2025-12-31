"""
Profit Scaling Exit Strategy

Intelligent partial profit taking with position scaling:
- Close 25-35% at first profit tier
- Close another 25-35% at second tier
- Let remaining position run with trailing protection

This approach:
1. Locks in guaranteed profits early
2. Reduces risk exposure as profit grows
3. Allows remaining position to capture extended moves
4. Adapts scaling based on account size and volatility

Philosophy:
- "You can't go broke taking profits"
- Scale out of winners, not all at once
- Let house money ride
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .base import ExitStrategy, ExitSignal
from cthulu.position.manager import PositionInfo

logger = logging.getLogger(__name__)


class ScaleTier(Enum):
    """Profit tier levels for scaling out."""
    INITIAL = "initial"      # No scaling yet
    TIER_1 = "tier_1"        # First profit target hit
    TIER_2 = "tier_2"        # Second profit target hit
    TIER_3 = "tier_3"        # Third profit target hit (runner)
    COMPLETE = "complete"    # Fully scaled out


@dataclass
class ScaleConfig:
    """Configuration for profit scaling."""
    # Profit targets as percentage of entry price
    tier_1_profit_pct: float = 0.3   # First scale at 0.3% profit
    tier_2_profit_pct: float = 0.6   # Second scale at 0.6% profit
    tier_3_profit_pct: float = 1.0   # Third scale at 1.0% profit
    
    # Volume to close at each tier (as percentage of remaining)
    tier_1_close_pct: float = 30.0   # Close 30% at tier 1
    tier_2_close_pct: float = 35.0   # Close 35% of remaining at tier 2
    tier_3_close_pct: float = 50.0   # Close 50% of remaining at tier 3
    
    # Micro account adjustments (tighter targets)
    micro_account_threshold: float = 100.0
    micro_tier_1_pct: float = 0.15   # Tighter first tier for micro
    micro_tier_2_pct: float = 0.30
    micro_tier_3_pct: float = 0.50
    
    # Small account adjustments
    small_account_threshold: float = 500.0
    small_tier_1_pct: float = 0.20
    small_tier_2_pct: float = 0.40
    small_tier_3_pct: float = 0.70
    
    # Dynamic adjustments
    volatility_adjust: bool = True   # Adjust targets based on ATR
    momentum_adjust: bool = True     # Adjust based on momentum strength


@dataclass
class PositionScaleState:
    """Track scaling state for a position."""
    ticket: int
    original_volume: float
    current_tier: ScaleTier = ScaleTier.INITIAL
    scales_executed: List[Dict[str, Any]] = field(default_factory=list)
    peak_profit: float = 0.0
    peak_profit_pct: float = 0.0
    entry_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_scaled_volume(self) -> float:
        """Total volume already scaled out."""
        return sum(s.get('volume', 0) for s in self.scales_executed)
    
    @property
    def remaining_volume_pct(self) -> float:
        """Percentage of original volume remaining."""
        if self.original_volume <= 0:
            return 0
        return ((self.original_volume - self.total_scaled_volume) / self.original_volume) * 100


class ProfitScalingExit(ExitStrategy):
    """
    Intelligent profit scaling strategy.
    
    Takes partial profits at predetermined levels while letting
    remaining position run for larger gains.
    
    Features:
    - Multi-tier profit targets
    - Account-size adaptive targets
    - Volatility-adjusted scaling
    - Momentum-aware adjustments
    - Never gives back significant profits
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        params = params or {}
        super().__init__(
            name="ProfitScaling",
            params=params,
            priority=55  # Medium-high priority
        )
        
        # Load configuration
        self.config = ScaleConfig(
            tier_1_profit_pct=params.get('tier_1_profit_pct', 0.3),
            tier_2_profit_pct=params.get('tier_2_profit_pct', 0.6),
            tier_3_profit_pct=params.get('tier_3_profit_pct', 1.0),
            tier_1_close_pct=params.get('tier_1_close_pct', 30.0),
            tier_2_close_pct=params.get('tier_2_close_pct', 35.0),
            tier_3_close_pct=params.get('tier_3_close_pct', 50.0),
            micro_account_threshold=params.get('micro_account_threshold', 100.0),
            small_account_threshold=params.get('small_account_threshold', 500.0),
            volatility_adjust=params.get('volatility_adjust', True),
            momentum_adjust=params.get('momentum_adjust', True),
        )
        
        # State tracking
        self._position_states: Dict[int, PositionScaleState] = {}
        
    def should_exit(
        self,
        position: PositionInfo,
        current_data: Dict[str, Any]
    ) -> Optional[ExitSignal]:
        """
        Check if position should be partially scaled out.
        
        Args:
            position: Position information
            current_data: Market data including account_balance, indicators, current_price
            
        Returns:
            ExitSignal with partial_volume if scaling triggered, None otherwise
        """
        if not self._enabled:
            return None
            
        ticket = position.ticket
        current_price = current_data.get('current_price', position.current_price)
        account_balance = current_data.get('account_balance', 1000)
        indicators = current_data.get('indicators', {})
        
        if current_price is None or current_price <= 0:
            return None
            
        # Initialize state for new position
        if ticket not in self._position_states:
            self._position_states[ticket] = PositionScaleState(
                ticket=ticket,
                original_volume=position.volume,
                entry_price=position.open_price
            )
            logger.info(f"[ProfitScaling] Initialized tracking for {ticket}, vol={position.volume}")
            
        state = self._position_states[ticket]
        
        # Skip if fully scaled out
        if state.current_tier == ScaleTier.COMPLETE:
            return None
            
        # Calculate profit percentage
        profit_pct = self._calculate_profit_pct(position, current_price)
        
        # Update peak profit
        if profit_pct > state.peak_profit_pct:
            state.peak_profit_pct = profit_pct
            state.peak_profit = position.unrealized_pnl
            
        # Get adjusted targets based on account size and volatility
        targets = self._get_adjusted_targets(account_balance, indicators)
        
        # Check each tier
        scale_signal = self._check_scale_tiers(position, state, profit_pct, targets, current_price)
        
        if scale_signal:
            return scale_signal
            
        # Check profit giveback protection for scaled positions
        if state.current_tier != ScaleTier.INITIAL:
            giveback_signal = self._check_scaled_giveback(position, state, profit_pct, current_price)
            if giveback_signal:
                return giveback_signal
                
        return None
        
    def _calculate_profit_pct(self, position: PositionInfo, current_price: float) -> float:
        """Calculate profit as percentage of entry price."""
        if position.open_price <= 0:
            return 0
            
        if position.side == 'BUY':
            return ((current_price - position.open_price) / position.open_price) * 100
        else:
            return ((position.open_price - current_price) / position.open_price) * 100
            
    def _get_adjusted_targets(
        self,
        account_balance: float,
        indicators: Dict[str, Any]
    ) -> Dict[str, float]:
        """Get profit targets adjusted for account size and volatility."""
        
        # Base targets
        if account_balance < self.config.micro_account_threshold:
            targets = {
                'tier_1': self.config.micro_tier_1_pct,
                'tier_2': self.config.micro_tier_2_pct,
                'tier_3': self.config.micro_tier_3_pct,
            }
            logger.debug(f"Using MICRO targets: {targets}")
        elif account_balance < self.config.small_account_threshold:
            targets = {
                'tier_1': self.config.small_tier_1_pct,
                'tier_2': self.config.small_tier_2_pct,
                'tier_3': self.config.small_tier_3_pct,
            }
            logger.debug(f"Using SMALL targets: {targets}")
        else:
            targets = {
                'tier_1': self.config.tier_1_profit_pct,
                'tier_2': self.config.tier_2_profit_pct,
                'tier_3': self.config.tier_3_profit_pct,
            }
            
        # Volatility adjustment
        if self.config.volatility_adjust:
            atr = indicators.get('atr')
            if atr and atr > 0:
                # Higher ATR = wider targets (more volatile = need bigger moves)
                # Normalize ATR as percentage of price
                atr_pct = indicators.get('atr_pct', atr * 100)
                
                # If ATR is high, widen targets; if low, tighten
                volatility_mult = max(0.7, min(1.5, atr_pct / 0.5))  # Normalized around 0.5%
                
                for key in targets:
                    targets[key] *= volatility_mult
                    
        # Momentum adjustment
        if self.config.momentum_adjust:
            rsi = indicators.get('rsi') or indicators.get('RSI')
            adx = indicators.get('adx') or indicators.get('ADX')
            
            # Strong momentum = let it run (widen targets)
            if adx and adx > 30:
                momentum_mult = 1.2  # Strong trend, widen targets
            elif adx and adx < 20:
                momentum_mult = 0.85  # Weak trend, tighter targets
            else:
                momentum_mult = 1.0
                
            for key in targets:
                targets[key] *= momentum_mult
                
        return targets
        
    def _check_scale_tiers(
        self,
        position: PositionInfo,
        state: PositionScaleState,
        profit_pct: float,
        targets: Dict[str, float],
        current_price: float
    ) -> Optional[ExitSignal]:
        """Check if any profit tier is hit and return scale signal."""
        
        remaining_volume = position.volume
        
        # Check Tier 1
        if state.current_tier == ScaleTier.INITIAL and profit_pct >= targets['tier_1']:
            close_volume = self._calculate_scale_volume(
                remaining_volume,
                self.config.tier_1_close_pct
            )
            
            if close_volume > 0:
                state.current_tier = ScaleTier.TIER_1
                state.scales_executed.append({
                    'tier': 'TIER_1',
                    'volume': close_volume,
                    'profit_pct': profit_pct,
                    'price': current_price,
                    'timestamp': datetime.now()
                })
                
                logger.info(
                    f"[ProfitScaling] TIER 1 HIT for {position.ticket}: "
                    f"profit={profit_pct:.2f}%, closing {close_volume:.4f} ({self.config.tier_1_close_pct}%)"
                )
                
                return self._create_scale_signal(
                    position, close_volume, current_price,
                    tier="TIER_1", profit_pct=profit_pct, targets=targets
                )
                
        # Check Tier 2
        elif state.current_tier == ScaleTier.TIER_1 and profit_pct >= targets['tier_2']:
            close_volume = self._calculate_scale_volume(
                remaining_volume,
                self.config.tier_2_close_pct
            )
            
            if close_volume > 0:
                state.current_tier = ScaleTier.TIER_2
                state.scales_executed.append({
                    'tier': 'TIER_2',
                    'volume': close_volume,
                    'profit_pct': profit_pct,
                    'price': current_price,
                    'timestamp': datetime.now()
                })
                
                logger.info(
                    f"[ProfitScaling] TIER 2 HIT for {position.ticket}: "
                    f"profit={profit_pct:.2f}%, closing {close_volume:.4f} ({self.config.tier_2_close_pct}%)"
                )
                
                return self._create_scale_signal(
                    position, close_volume, current_price,
                    tier="TIER_2", profit_pct=profit_pct, targets=targets
                )
                
        # Check Tier 3
        elif state.current_tier == ScaleTier.TIER_2 and profit_pct >= targets['tier_3']:
            close_volume = self._calculate_scale_volume(
                remaining_volume,
                self.config.tier_3_close_pct
            )
            
            if close_volume > 0:
                state.current_tier = ScaleTier.TIER_3
                state.scales_executed.append({
                    'tier': 'TIER_3',
                    'volume': close_volume,
                    'profit_pct': profit_pct,
                    'price': current_price,
                    'timestamp': datetime.now()
                })
                
                logger.info(
                    f"[ProfitScaling] TIER 3 HIT for {position.ticket}: "
                    f"profit={profit_pct:.2f}%, closing {close_volume:.4f} - RUNNER active"
                )
                
                return self._create_scale_signal(
                    position, close_volume, current_price,
                    tier="TIER_3", profit_pct=profit_pct, targets=targets
                )
                
        return None
        
    def _check_scaled_giveback(
        self,
        position: PositionInfo,
        state: PositionScaleState,
        profit_pct: float,
        current_price: float
    ) -> Optional[ExitSignal]:
        """
        Protect scaled positions from giving back too much profit.
        
        Once we've scaled out, remaining position should not give back
        more than 50% of peak profit.
        """
        if state.peak_profit_pct <= 0:
            return None
            
        # Calculate giveback percentage
        giveback = state.peak_profit_pct - profit_pct
        giveback_pct = (giveback / state.peak_profit_pct) * 100 if state.peak_profit_pct > 0 else 0
        
        # Tighter protection after more scales
        if state.current_tier == ScaleTier.TIER_1:
            max_giveback = 60  # Allow 60% giveback at tier 1
        elif state.current_tier == ScaleTier.TIER_2:
            max_giveback = 50  # Allow 50% giveback at tier 2
        elif state.current_tier == ScaleTier.TIER_3:
            max_giveback = 40  # Allow only 40% giveback for runner
        else:
            max_giveback = 70
            
        if giveback_pct >= max_giveback and profit_pct > 0:
            remaining_vol = position.volume
            
            logger.warning(
                f"[ProfitScaling] Giveback protection for {position.ticket}: "
                f"Peak {state.peak_profit_pct:.2f}% -> Current {profit_pct:.2f}% "
                f"({giveback_pct:.1f}% giveback) - closing remaining"
            )
            
            state.current_tier = ScaleTier.COMPLETE
            
            return self._create_scale_signal(
                position, remaining_vol, current_price,
                tier="GIVEBACK_PROTECTION",
                profit_pct=profit_pct,
                targets={},
                reason=f"Profit giveback protection ({giveback_pct:.1f}% giveback)"
            )
            
        return None
        
    def _calculate_scale_volume(
        self,
        current_volume: float,
        close_pct: float
    ) -> float:
        """
        Calculate volume to close for scaling.
        
        Respects minimum lot sizes and rounds appropriately.
        """
        raw_volume = current_volume * (close_pct / 100)
        
        # Round to 2 decimal places (standard lot precision)
        volume = round(raw_volume, 2)
        
        # Ensure minimum volume (0.01 for most brokers)
        if volume < 0.01:
            # If remaining is tiny, close it all
            if current_volume <= 0.02:
                return current_volume
            return 0.01
            
        # Don't close more than we have
        return min(volume, current_volume)
        
    def _create_scale_signal(
        self,
        position: PositionInfo,
        volume: float,
        price: float,
        tier: str,
        profit_pct: float,
        targets: Dict[str, float],
        reason: str = None
    ) -> ExitSignal:
        """Create exit signal for partial close."""
        
        if reason is None:
            reason = f"Profit scaling {tier}: +{profit_pct:.2f}%"
            
        return ExitSignal(
            ticket=position.ticket,
            reason=reason,
            price=price,
            timestamp=datetime.now(),
            strategy_name=self.name,
            confidence=0.92,
            partial_volume=volume,
            metadata={
                'tier': tier,
                'profit_pct': profit_pct,
                'close_volume': volume,
                'original_volume': position.volume,
                'targets': targets,
                'remaining_after_close': position.volume - volume
            }
        )
        
    def get_position_state(self, ticket: int) -> Optional[PositionScaleState]:
        """Get scaling state for a position."""
        return self._position_states.get(ticket)
        
    def reset(self):
        """Reset all position states."""
        super().reset()
        self._position_states.clear()
        logger.info("[ProfitScaling] Reset all position states")
        
    def remove_position(self, ticket: int):
        """Remove position from tracking when fully closed."""
        if ticket in self._position_states:
            state = self._position_states[ticket]
            logger.info(
                f"[ProfitScaling] Position {ticket} closed. "
                f"Final tier: {state.current_tier.value}, "
                f"Scales: {len(state.scales_executed)}"
            )
            del self._position_states[ticket]


class AggressiveScalingExit(ProfitScalingExit):
    """
    More aggressive profit scaling for volatile markets or small accounts.
    
    Takes profits faster with tighter targets:
    - Tier 1: 0.15% (vs 0.3%)
    - Tier 2: 0.30% (vs 0.6%)
    - Tier 3: 0.50% (vs 1.0%)
    
    Closes larger portions at each tier:
    - Tier 1: 35% (vs 30%)
    - Tier 2: 40% (vs 35%)
    - Tier 3: 60% (vs 50%)
    """
    
    def __init__(self, params: Dict[str, Any] = None):
        params = params or {}
        
        # Override with aggressive defaults
        aggressive_params = {
            'tier_1_profit_pct': params.get('tier_1_profit_pct', 0.15),
            'tier_2_profit_pct': params.get('tier_2_profit_pct', 0.30),
            'tier_3_profit_pct': params.get('tier_3_profit_pct', 0.50),
            'tier_1_close_pct': params.get('tier_1_close_pct', 35.0),
            'tier_2_close_pct': params.get('tier_2_close_pct', 40.0),
            'tier_3_close_pct': params.get('tier_3_close_pct', 60.0),
            'micro_tier_1_pct': params.get('micro_tier_1_pct', 0.10),
            'micro_tier_2_pct': params.get('micro_tier_2_pct', 0.20),
            'micro_tier_3_pct': params.get('micro_tier_3_pct', 0.35),
            **params
        }
        
        super().__init__(aggressive_params)
        self.name = "AggressiveScaling"
        self.priority = 60  # Slightly higher priority
        
        logger.info("[AggressiveScaling] Initialized with tight profit targets")


# Convenience exports
ProfitScaling = ProfitScalingExit
AggressiveScaling = AggressiveScalingExit
