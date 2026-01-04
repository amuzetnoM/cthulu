"""
Entry Confluence Filter - The Quality Gate

This module provides entry-level confluence analysis to ensure we only execute
trades at optimal price levels. It acts as a filter between signal generation
and order execution.

Professional trading insight: A signal is worthless without proper execution.
The edge isn't in knowing the direction - it's in the timing and level of entry.

Key concepts:
1. Price Level Analysis - Are we at a meaningful level (S/R, round numbers, FVGs)?
2. Momentum Confirmation - Is price moving in our favor or against?
3. Liquidity Considerations - Are we entering into liquidity or from it?
4. Multi-Timeframe Alignment - Does higher TF support this entry?

Part of Cthulu v5.1.0 APEX - Entry Quality System
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger("Cthulu.entry_confluence")


class EntryQuality(Enum):
    """Entry quality classification."""
    PREMIUM = "premium"      # Optimal entry - full position
    GOOD = "good"            # Acceptable entry - standard position
    MARGINAL = "marginal"    # Suboptimal entry - reduced position
    POOR = "poor"            # Bad entry - wait or skip
    REJECT = "reject"        # Do not enter - signal invalidated


class PriceLevelType(Enum):
    """Types of significant price levels."""
    SUPPORT = "support"
    RESISTANCE = "resistance"
    ROUND_NUMBER = "round_number"
    PIVOT = "pivot"
    VWAP = "vwap"
    EMA = "ema"
    FVG = "fair_value_gap"         # Imbalance zone
    ORDER_BLOCK = "order_block"
    PREVIOUS_HIGH = "previous_high"
    PREVIOUS_LOW = "previous_low"


@dataclass
class PriceLevel:
    """A significant price level."""
    price: float
    level_type: PriceLevelType
    strength: float  # 0-1, how strong is this level
    touches: int     # Number of times price touched this level
    last_touch: Optional[datetime] = None
    broken: bool = False
    notes: str = ""


@dataclass
class EntryConfluenceResult:
    """Result of entry confluence analysis."""
    quality: EntryQuality
    score: float              # 0-100
    should_enter: bool
    position_mult: float      # Position size multiplier (0.5 = half size)
    wait_for_better: bool     # Should we wait for better entry?
    optimal_entry: Optional[float] = None  # Better entry price if waiting
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    levels_near: List[PriceLevel] = field(default_factory=list)
    momentum_aligned: bool = True
    timing_score: float = 0.0
    level_score: float = 0.0
    
    @property
    def summary(self) -> str:
        """Get summary of entry analysis."""
        return (f"Entry: {self.quality.value} (score={self.score:.0f}), "
                f"mult={self.position_mult:.2f}, wait={self.wait_for_better}")


class EntryConfluenceFilter:
    """
    Entry Confluence Filter - Quality gate for trade entries.
    
    Analyzes whether current price is a good entry point for a signal,
    considering:
    - Proximity to key levels (S/R, round numbers, EMAs)
    - Current momentum and micro-structure
    - Risk/reward from current level
    - Multi-timeframe alignment
    
    Philosophy:
    - A bad entry can turn a winning signal into a loser
    - Wait for price to come to your level, don't chase
    - Enter from liquidity (levels where stops cluster)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger("Cthulu.entry_confluence")
        
        # Configuration
        self.min_score_to_enter = self.config.get('min_score_to_enter', 50)
        self.min_score_for_full_size = self.config.get('min_score_for_full_size', 75)
        self.enable_wait_mode = self.config.get('enable_wait_mode', True)
        self.max_wait_bars = self.config.get('max_wait_bars', 10)
        
        # Level detection parameters
        self.sr_lookback = self.config.get('sr_lookback', 100)
        self.sr_min_touches = self.config.get('sr_min_touches', 2)
        self.level_tolerance_atr = self.config.get('level_tolerance_atr', 0.5)
        
        # Momentum parameters
        self.momentum_bars = self.config.get('momentum_bars', 5)
        self.momentum_weight = self.config.get('momentum_weight', 0.25)
        self.level_weight = self.config.get('level_weight', 0.40)
        self.timing_weight = self.config.get('timing_weight', 0.20)
        self.structure_weight = self.config.get('structure_weight', 0.15)
        
        # State: tracked levels and pending entries
        self._price_levels: Dict[str, List[PriceLevel]] = {}
        self._pending_entries: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("EntryConfluenceFilter initialized")
    
    def analyze_entry(
        self,
        signal_direction: str,  # 'long' or 'short'
        current_price: float,
        symbol: str,
        market_data: pd.DataFrame,
        atr: Optional[float] = None,
        signal_entry_price: Optional[float] = None
    ) -> EntryConfluenceResult:
        """
        Analyze whether current conditions support a quality entry.
        
        Args:
            signal_direction: 'long' or 'short'
            current_price: Current market price
            symbol: Trading symbol
            market_data: OHLCV DataFrame
            atr: Current ATR (will compute if not provided)
            signal_entry_price: Price where signal was generated (for drift check)
            
        Returns:
            EntryConfluenceResult with entry quality assessment
        """
        reasons = []
        warnings = []
        
        # Compute ATR if not provided
        if atr is None:
            atr = self._compute_atr(market_data)
        
        # Detect price levels
        levels = self._detect_price_levels(symbol, market_data, atr)
        
        # 1. LEVEL SCORE - Are we at a meaningful level?
        level_score, level_reasons, nearby_levels = self._score_price_levels(
            signal_direction, current_price, levels, atr
        )
        reasons.extend(level_reasons)
        
        # 2. MOMENTUM SCORE - Is momentum aligned with entry?
        momentum_score, momentum_aligned, momentum_reasons = self._score_momentum(
            signal_direction, market_data
        )
        reasons.extend(momentum_reasons)
        
        # 3. TIMING SCORE - Entry timing quality
        timing_score, timing_reasons, wait_for_better, optimal_entry = self._score_timing(
            signal_direction, current_price, market_data, atr, levels
        )
        reasons.extend(timing_reasons)
        
        # 4. STRUCTURE SCORE - Market structure alignment
        structure_score, structure_reasons = self._score_structure(
            signal_direction, market_data
        )
        reasons.extend(structure_reasons)
        
        # 5. Check for signal drift (price moved away from signal)
        drift_penalty = 0.0
        if signal_entry_price is not None:
            drift = abs(current_price - signal_entry_price) / atr if atr > 0 else 0
            if drift > 1.5:  # Price moved more than 1.5 ATR from signal
                drift_penalty = min(drift * 10, 30)  # Max 30 point penalty
                warnings.append(f"Price drifted {drift:.1f} ATR from signal")
        
        # Calculate weighted total score
        total_score = (
            level_score * self.level_weight +
            momentum_score * self.momentum_weight +
            timing_score * self.timing_weight +
            structure_score * self.structure_weight
        ) * 100 - drift_penalty
        
        total_score = max(0, min(100, total_score))
        
        # Determine entry quality
        if total_score >= 85:
            quality = EntryQuality.PREMIUM
        elif total_score >= 70:
            quality = EntryQuality.GOOD
        elif total_score >= self.min_score_to_enter:
            quality = EntryQuality.MARGINAL
        elif total_score >= 20:
            quality = EntryQuality.POOR
        else:
            quality = EntryQuality.REJECT
        
        # Determine position size multiplier
        if quality == EntryQuality.PREMIUM:
            position_mult = 1.0
        elif quality == EntryQuality.GOOD:
            position_mult = 0.85
        elif quality == EntryQuality.MARGINAL:
            position_mult = 0.6
        elif quality == EntryQuality.POOR:
            position_mult = 0.3
        else:
            position_mult = 0.0
        
        # Should we enter? Allow entry if score meets minimum threshold
        should_enter = total_score >= self.min_score_to_enter
        
        # Override: If momentum strongly against, don't enter
        if not momentum_aligned and momentum_score < 0.3:
            should_enter = False
            warnings.append("Momentum strongly against entry direction")
        
        result = EntryConfluenceResult(
            quality=quality,
            score=total_score,
            should_enter=should_enter,
            position_mult=position_mult,
            wait_for_better=wait_for_better and self.enable_wait_mode,
            optimal_entry=optimal_entry,
            reasons=reasons,
            warnings=warnings,
            levels_near=nearby_levels,
            momentum_aligned=momentum_aligned,
            timing_score=timing_score,
            level_score=level_score
        )
        
        self.logger.info(f"Entry analysis: {result.summary}")
        if reasons:
            self.logger.debug(f"  Reasons: {reasons}")
        if warnings:
            self.logger.warning(f"  Warnings: {warnings}")
        
        return result
    
    def register_pending_entry(
        self,
        signal_id: str,
        signal_direction: str,
        optimal_entry: float,
        symbol: str,
        max_wait_bars: int = None
    ):
        """
        Register a pending entry to wait for better price.
        
        Args:
            signal_id: Unique signal identifier
            signal_direction: 'long' or 'short'
            optimal_entry: Price to wait for
            symbol: Trading symbol
            max_wait_bars: Maximum bars to wait (default from config)
        """
        self._pending_entries[signal_id] = {
            'direction': signal_direction,
            'optimal_entry': optimal_entry,
            'symbol': symbol,
            'registered_at': datetime.now(),
            'bars_waited': 0,
            'max_wait': max_wait_bars or self.max_wait_bars,
            'active': True
        }
        self.logger.info(f"Registered pending entry {signal_id}: wait for {optimal_entry}")
    
    def check_pending_entries(
        self,
        symbol: str,
        current_price: float,
        current_bar: pd.Series
    ) -> List[Dict[str, Any]]:
        """
        Check if any pending entries should now execute.
        
        Args:
            symbol: Trading symbol
            current_price: Current price
            current_bar: Current bar data
            
        Returns:
            List of entries that are now ready to execute
        """
        ready_entries = []
        
        for signal_id, entry in list(self._pending_entries.items()):
            if not entry['active'] or entry['symbol'] != symbol:
                continue
            
            entry['bars_waited'] += 1
            
            # Check if price reached our target
            if entry['direction'] == 'long':
                if current_price <= entry['optimal_entry']:
                    ready_entries.append({
                        'signal_id': signal_id,
                        'direction': entry['direction'],
                        'entry_price': current_price,
                        'waited_bars': entry['bars_waited'],
                        'reason': f"Price reached optimal entry {entry['optimal_entry']}"
                    })
                    entry['active'] = False
                    
            elif entry['direction'] == 'short':
                if current_price >= entry['optimal_entry']:
                    ready_entries.append({
                        'signal_id': signal_id,
                        'direction': entry['direction'],
                        'entry_price': current_price,
                        'waited_bars': entry['bars_waited'],
                        'reason': f"Price reached optimal entry {entry['optimal_entry']}"
                    })
                    entry['active'] = False
            
            # Check timeout
            if entry['bars_waited'] >= entry['max_wait']:
                # Expired - execute at current price with reduced size
                ready_entries.append({
                    'signal_id': signal_id,
                    'direction': entry['direction'],
                    'entry_price': current_price,
                    'waited_bars': entry['bars_waited'],
                    'reason': f"Wait timeout ({entry['max_wait']} bars)",
                    'timeout': True,
                    'size_mult': 0.5  # Half size on timeout
                })
                entry['active'] = False
        
        # Clean up inactive entries
        self._pending_entries = {
            k: v for k, v in self._pending_entries.items() 
            if v['active'] or (datetime.now() - v['registered_at']).seconds < 3600
        }
        
        return ready_entries
    
    def _detect_price_levels(
        self,
        symbol: str,
        data: pd.DataFrame,
        atr: float
    ) -> List[PriceLevel]:
        """
        Detect significant price levels from market data.
        
        Identifies:
        - Support/Resistance from swing highs/lows
        - Round numbers
        - Previous session high/low
        - EMA levels
        """
        levels = []
        
        if len(data) < 20:
            return levels
        
        tolerance = atr * self.level_tolerance_atr
        close = data['close'].iloc[-1]
        
        # 1. SWING HIGHS/LOWS (Support/Resistance)
        highs = data['high'].values
        lows = data['low'].values
        
        # Find swing highs (local maxima)
        for i in range(2, min(len(highs) - 2, self.sr_lookback)):
            if highs[-i] > highs[-i-1] and highs[-i] > highs[-i+1]:
                # Count touches
                touches = sum(1 for j in range(len(highs)) if abs(highs[j] - highs[-i]) < tolerance)
                if touches >= self.sr_min_touches:
                    strength = min(touches / 5.0, 1.0)
                    levels.append(PriceLevel(
                        price=float(highs[-i]),
                        level_type=PriceLevelType.RESISTANCE,
                        strength=strength,
                        touches=touches,
                        notes=f"Swing high with {touches} touches"
                    ))
        
        # Find swing lows (local minima)
        for i in range(2, min(len(lows) - 2, self.sr_lookback)):
            if lows[-i] < lows[-i-1] and lows[-i] < lows[-i+1]:
                touches = sum(1 for j in range(len(lows)) if abs(lows[j] - lows[-i]) < tolerance)
                if touches >= self.sr_min_touches:
                    strength = min(touches / 5.0, 1.0)
                    levels.append(PriceLevel(
                        price=float(lows[-i]),
                        level_type=PriceLevelType.SUPPORT,
                        strength=strength,
                        touches=touches,
                        notes=f"Swing low with {touches} touches"
                    ))
        
        # 2. ROUND NUMBERS
        # Determine round number step based on price magnitude
        if close > 10000:
            round_step = 1000
        elif close > 1000:
            round_step = 100
        elif close > 100:
            round_step = 10
        else:
            round_step = 1
        
        # Find nearest round numbers
        lower_round = (close // round_step) * round_step
        upper_round = lower_round + round_step
        
        for rn in [lower_round, upper_round]:
            if abs(rn - close) < atr * 3:  # Within 3 ATR
                levels.append(PriceLevel(
                    price=float(rn),
                    level_type=PriceLevelType.ROUND_NUMBER,
                    strength=0.6,
                    touches=0,
                    notes=f"Round number {rn}"
                ))
        
        # 3. PREVIOUS SESSION HIGH/LOW
        if len(data) >= 24:  # Assuming hourly data
            prev_session = data.iloc[-48:-24] if len(data) >= 48 else data.iloc[:24]
            if len(prev_session) > 0:
                prev_high = prev_session['high'].max()
                prev_low = prev_session['low'].min()
                
                levels.append(PriceLevel(
                    price=float(prev_high),
                    level_type=PriceLevelType.PREVIOUS_HIGH,
                    strength=0.8,
                    touches=1,
                    notes="Previous session high"
                ))
                levels.append(PriceLevel(
                    price=float(prev_low),
                    level_type=PriceLevelType.PREVIOUS_LOW,
                    strength=0.8,
                    touches=1,
                    notes="Previous session low"
                ))
        
        # 4. EMA LEVELS
        for period in [20, 50, 200]:
            col = f'ema_{period}'
            if col in data.columns:
                ema_val = data[col].iloc[-1]
                levels.append(PriceLevel(
                    price=float(ema_val),
                    level_type=PriceLevelType.EMA,
                    strength=0.5 + (period / 400),  # Longer EMAs = stronger
                    touches=0,
                    notes=f"EMA {period}"
                ))
        
        # Cache levels
        self._price_levels[symbol] = levels
        
        return levels
    
    def _score_price_levels(
        self,
        direction: str,
        price: float,
        levels: List[PriceLevel],
        atr: float
    ) -> Tuple[float, List[str], List[PriceLevel]]:
        """
        Score entry based on proximity to key levels.
        
        For LONG: We want to enter near support (bouncing up)
        For SHORT: We want to enter near resistance (bouncing down)
        """
        score = 0.5  # Neutral starting point
        reasons = []
        nearby_levels = []
        
        tolerance = atr * 1.5
        
        for level in levels:
            distance = abs(price - level.price)
            
            if distance < tolerance:
                nearby_levels.append(level)
                
                # Calculate proximity score (closer = better)
                proximity = 1.0 - (distance / tolerance)
                level_contribution = proximity * level.strength
                
                if direction == 'long':
                    if level.level_type in [PriceLevelType.SUPPORT, 
                                            PriceLevelType.PREVIOUS_LOW,
                                            PriceLevelType.EMA]:
                        # Good for long: entering at support
                        score += level_contribution * 0.2
                        reasons.append(f"Near {level.level_type.value} @ {level.price:.2f}")
                    elif level.level_type in [PriceLevelType.RESISTANCE,
                                              PriceLevelType.PREVIOUS_HIGH]:
                        # Bad for long: entering at resistance
                        score -= level_contribution * 0.15
                        reasons.append(f"Warning: Near {level.level_type.value} @ {level.price:.2f}")
                
                elif direction == 'short':
                    if level.level_type in [PriceLevelType.RESISTANCE,
                                            PriceLevelType.PREVIOUS_HIGH]:
                        # Good for short: entering at resistance
                        score += level_contribution * 0.2
                        reasons.append(f"Near {level.level_type.value} @ {level.price:.2f}")
                    elif level.level_type in [PriceLevelType.SUPPORT,
                                              PriceLevelType.PREVIOUS_LOW]:
                        # Bad for short: entering at support
                        score -= level_contribution * 0.15
                        reasons.append(f"Warning: Near {level.level_type.value} @ {level.price:.2f}")
                
                # Round numbers are neutral-to-good for both directions
                if level.level_type == PriceLevelType.ROUND_NUMBER:
                    score += level_contribution * 0.05
        
        return max(0, min(1, score)), reasons, nearby_levels
    
    def _score_momentum(
        self,
        direction: str,
        data: pd.DataFrame
    ) -> Tuple[float, bool, List[str]]:
        """
        Score momentum alignment with entry direction.
        
        We want momentum in our favor, or at least not against us.
        """
        if len(data) < self.momentum_bars + 1:
            return 0.5, True, []
        
        reasons = []
        
        # Calculate short-term momentum
        recent_close = data['close'].iloc[-self.momentum_bars:].values
        momentum = (recent_close[-1] - recent_close[0]) / recent_close[0] if recent_close[0] > 0 else 0
        
        # Calculate momentum direction strength
        up_bars = sum(1 for i in range(1, len(recent_close)) if recent_close[i] > recent_close[i-1])
        down_bars = len(recent_close) - 1 - up_bars
        
        momentum_direction = 1 if up_bars > down_bars else -1 if down_bars > up_bars else 0
        momentum_strength = abs(up_bars - down_bars) / (len(recent_close) - 1)
        
        # Check RSI if available
        rsi = data['rsi'].iloc[-1] if 'rsi' in data.columns else 50
        
        aligned = True
        score = 0.5
        
        if direction == 'long':
            if momentum_direction > 0:
                score = 0.5 + momentum_strength * 0.3
                reasons.append(f"Bullish momentum ({up_bars}/{len(recent_close)-1} bars)")
            elif momentum_direction < 0:
                score = 0.5 - momentum_strength * 0.25
                aligned = momentum_strength < 0.6
                reasons.append(f"Bearish momentum warning ({down_bars}/{len(recent_close)-1} bars)")
            
            # RSI check
            if rsi < 30:
                score += 0.15
                reasons.append("RSI oversold - good for long")
            elif rsi > 70:
                score -= 0.1
                reasons.append("RSI overbought - risky for long")
        
        elif direction == 'short':
            if momentum_direction < 0:
                score = 0.5 + momentum_strength * 0.3
                reasons.append(f"Bearish momentum ({down_bars}/{len(recent_close)-1} bars)")
            elif momentum_direction > 0:
                score = 0.5 - momentum_strength * 0.25
                aligned = momentum_strength < 0.6
                reasons.append(f"Bullish momentum warning ({up_bars}/{len(recent_close)-1} bars)")
            
            if rsi > 70:
                score += 0.15
                reasons.append("RSI overbought - good for short")
            elif rsi < 30:
                score -= 0.1
                reasons.append("RSI oversold - risky for short")
        
        return max(0, min(1, score)), aligned, reasons
    
    def _score_timing(
        self,
        direction: str,
        price: float,
        data: pd.DataFrame,
        atr: float,
        levels: List[PriceLevel]
    ) -> Tuple[float, List[str], bool, Optional[float]]:
        """
        Score entry timing and suggest better entry if available.
        
        Checks:
        - Are we chasing price?
        - Is there a retest coming?
        - Is price extended from key levels?
        """
        reasons = []
        score = 0.5
        wait_for_better = False
        optimal_entry = None
        
        if len(data) < 10:
            return score, reasons, wait_for_better, optimal_entry
        
        # Calculate recent range
        recent_high = data['high'].iloc[-10:].max()
        recent_low = data['low'].iloc[-10:].min()
        recent_range = recent_high - recent_low
        
        # Position within recent range
        if recent_range > 0:
            range_position = (price - recent_low) / recent_range
            
            if direction == 'long':
                if range_position > 0.8:
                    # Near recent high - chasing
                    score -= 0.2
                    reasons.append("Buying near recent high (chasing)")
                    wait_for_better = True
                    optimal_entry = recent_low + recent_range * 0.3  # Buy lower
                elif range_position < 0.3:
                    # Near recent low - good entry
                    score += 0.2
                    reasons.append("Buying near recent low (optimal)")
                else:
                    reasons.append(f"Mid-range entry ({range_position:.0%} of range)")
                    
            elif direction == 'short':
                if range_position < 0.2:
                    # Near recent low - chasing
                    score -= 0.2
                    reasons.append("Selling near recent low (chasing)")
                    wait_for_better = True
                    optimal_entry = recent_high - recent_range * 0.3  # Sell higher
                elif range_position > 0.7:
                    # Near recent high - good entry
                    score += 0.2
                    reasons.append("Selling near recent high (optimal)")
                else:
                    reasons.append(f"Mid-range entry ({range_position:.0%} of range)")
        
        # Check for extension from EMA
        for col in ['ema_20', 'ema_50']:
            if col in data.columns:
                ema = data[col].iloc[-1]
                extension = abs(price - ema) / atr if atr > 0 else 0
                
                if extension > 2:
                    score -= 0.1
                    reasons.append(f"Extended {extension:.1f} ATR from {col}")
                    
                    if direction == 'long':
                        if price > ema:
                            wait_for_better = True
                            optimal_entry = ema + atr * 0.5
                    elif direction == 'short':
                        if price < ema:
                            wait_for_better = True
                            optimal_entry = ema - atr * 0.5
                break
        
        return max(0, min(1, score)), reasons, wait_for_better, optimal_entry
    
    def _score_structure(
        self,
        direction: str,
        data: pd.DataFrame
    ) -> Tuple[float, List[str]]:
        """
        Score market structure alignment.
        
        Checks higher-timeframe trend and structure.
        """
        if len(data) < 50:
            return 0.5, []
        
        reasons = []
        score = 0.5
        
        # Check if making higher highs/lows (uptrend) or lower highs/lows (downtrend)
        recent = data.iloc[-20:]
        older = data.iloc[-50:-20]
        
        recent_high = recent['high'].max()
        recent_low = recent['low'].min()
        older_high = older['high'].max()
        older_low = older['low'].min()
        
        higher_highs = recent_high > older_high
        higher_lows = recent_low > older_low
        lower_highs = recent_high < older_high
        lower_lows = recent_low < older_low
        
        if direction == 'long':
            if higher_highs and higher_lows:
                score += 0.25
                reasons.append("Structure: Higher highs & lows (bullish)")
            elif lower_highs and lower_lows:
                score -= 0.2
                reasons.append("Structure: Lower highs & lows (bearish - against long)")
            elif higher_lows:
                score += 0.1
                reasons.append("Structure: Higher lows (bullish bias)")
                
        elif direction == 'short':
            if lower_highs and lower_lows:
                score += 0.25
                reasons.append("Structure: Lower highs & lows (bearish)")
            elif higher_highs and higher_lows:
                score -= 0.2
                reasons.append("Structure: Higher highs & lows (bullish - against short)")
            elif lower_highs:
                score += 0.1
                reasons.append("Structure: Lower highs (bearish bias)")
        
        return max(0, min(1, score)), reasons
    
    def _compute_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Compute ATR from market data."""
        if len(data) < period:
            return 0.0
        
        if 'atr' in data.columns:
            return float(data['atr'].iloc[-1])
        
        # Manual calculation
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values
        
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )
        
        atr = np.mean(tr[-period:]) if len(tr) >= period else np.mean(tr)
        return float(atr)


# Module-level singleton
_confluence_filter: Optional[EntryConfluenceFilter] = None


def get_entry_confluence_filter(**kwargs) -> EntryConfluenceFilter:
    """Get or create the entry confluence filter singleton."""
    global _confluence_filter
    if _confluence_filter is None:
        _confluence_filter = EntryConfluenceFilter(**kwargs)
    return _confluence_filter


def analyze_entry(
    signal_direction: str,
    current_price: float,
    symbol: str,
    market_data: pd.DataFrame,
    atr: Optional[float] = None
) -> EntryConfluenceResult:
    """Convenience function to analyze entry quality."""
    return get_entry_confluence_filter().analyze_entry(
        signal_direction, current_price, symbol, market_data, atr
    )
