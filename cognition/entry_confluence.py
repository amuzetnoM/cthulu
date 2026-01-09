"""
Entry Confluence Filter - Clean Implementation
Quality gate for trade entries based on price levels, momentum, and timing.
"""
import logging
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConfluenceResult:
    """Result of confluence analysis."""
    score: int  # 0-100
    quality: str  # premium, good, marginal, poor, reject
    should_reject: bool
    should_wait: bool
    confidence_multiplier: float
    suggested_entry: Optional[float]
    reasons: List[str]
    reason: str  # Summary reason


class EntryConfluenceFilter:
    """
    Entry quality gate that analyzes confluence of factors.
    
    Scoring Components:
    - Level Score (40%): S/R zones, round numbers, EMAs
    - Momentum Score (25%): Bar momentum, RSI alignment
    - Timing Score (20%): Range position, extension
    - Structure Score (15%): Higher highs/lows alignment
    
    Quality Grades:
    - PREMIUM (≥85): Full confidence, ideal entry
    - GOOD (≥70): Strong entry, slight confidence reduction
    - MARGINAL (50-69): Acceptable, reduced size
    - POOR (30-49): Wait for better entry
    - REJECT (<30): Do not enter
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Entry Confluence Filter.
        
        Config options:
        - min_score_to_enter: Minimum score to allow entry (default: 50)
        - min_score_for_full_size: Score for full position size (default: 75)
        - level_weight: Weight for level score (default: 0.40)
        - momentum_weight: Weight for momentum score (default: 0.25)
        - timing_weight: Weight for timing score (default: 0.20)
        - structure_weight: Weight for structure score (default: 0.15)
        """
        self.config = config or {}
        
        self.min_score_to_enter = self.config.get('min_score_to_enter', 50)
        self.min_score_for_full_size = self.config.get('min_score_for_full_size', 75)
        
        self.level_weight = self.config.get('level_weight', 0.40)
        self.momentum_weight = self.config.get('momentum_weight', 0.25)
        self.timing_weight = self.config.get('timing_weight', 0.20)
        self.structure_weight = self.config.get('structure_weight', 0.15)
        
        logger.info("EntryConfluenceFilter initialized")
    
    def analyze(
        self,
        signal: Dict[str, Any],
        data: Any,  # DataFrame
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze entry quality for a signal.
        
        Args:
            signal: Trading signal with direction, symbol
            data: Market data (OHLCV DataFrame)
            indicators: Calculated indicators
            
        Returns:
            ConfluenceResult as dict
        """
        if data is None or len(data) < 20:
            return self._create_result(50, "Data insufficient", [])
        
        direction = signal.get('direction', 'buy')
        is_buy = direction == 'buy'
        current_price = data['close'].iloc[-1]
        
        reasons = []
        
        # Calculate component scores
        level_score = self._calculate_level_score(data, current_price, is_buy, reasons)
        momentum_score = self._calculate_momentum_score(data, indicators, is_buy, reasons)
        timing_score = self._calculate_timing_score(data, current_price, reasons)
        structure_score = self._calculate_structure_score(data, is_buy, reasons)
        
        # Weighted total
        total_score = int(
            level_score * self.level_weight +
            momentum_score * self.momentum_weight +
            timing_score * self.timing_weight +
            structure_score * self.structure_weight
        )
        
        # Determine quality grade
        quality, should_reject, should_wait, conf_mult = self._grade_score(total_score)
        
        # Calculate suggested entry if waiting
        suggested_entry = None
        if should_wait:
            suggested_entry = self._calculate_suggested_entry(data, is_buy)
        
        result = ConfluenceResult(
            score=total_score,
            quality=quality,
            should_reject=should_reject,
            should_wait=should_wait,
            confidence_multiplier=conf_mult,
            suggested_entry=suggested_entry,
            reasons=reasons,
            reason=", ".join(reasons[:3]) if reasons else "No issues"
        )
        
        logger.info(f"Entry analysis: Entry: {quality} (score={total_score}), mult={conf_mult:.2f}, wait={should_wait}")
        
        return {
            'score': result.score,
            'quality': result.quality,
            'should_reject': result.should_reject,
            'should_wait': result.should_wait,
            'confidence_multiplier': result.confidence_multiplier,
            'suggested_entry': result.suggested_entry,
            'reasons': result.reasons,
            'reason': result.reason
        }
    
    def _calculate_level_score(
        self,
        data: Any,
        current_price: float,
        is_buy: bool,
        reasons: List[str]
    ) -> int:
        """Calculate score based on price levels."""
        score = 70  # Start neutral-good
        
        # Check if near support/resistance
        highs = data['high'].values
        lows = data['low'].values
        
        # Simple S/R detection (swing highs/lows)
        recent_high = highs[-20:].max()
        recent_low = lows[-20:].min()
        price_range = recent_high - recent_low
        
        if price_range == 0:
            return score
        
        # Distance from key levels
        dist_from_high = (recent_high - current_price) / price_range
        dist_from_low = (current_price - recent_low) / price_range
        
        if is_buy:
            # Good to buy near support
            if dist_from_low < 0.2:
                score += 15
                reasons.append("Near support - good for long")
            elif dist_from_high < 0.2:
                score -= 15
                reasons.append("Near resistance - risky for long")
        else:
            # Good to sell near resistance
            if dist_from_high < 0.2:
                score += 15
                reasons.append("Near resistance - good for short")
            elif dist_from_low < 0.2:
                score -= 15
                reasons.append("Near support - risky for short")
        
        # Check round numbers
        round_level = round(current_price, -1)  # Round to nearest 10
        dist_from_round = abs(current_price - round_level)
        
        if dist_from_round < price_range * 0.05:
            reasons.append(f"Near round number {round_level}")
        
        return max(0, min(100, score))
    
    def _calculate_momentum_score(
        self,
        data: Any,
        indicators: Dict[str, Any],
        is_buy: bool,
        reasons: List[str]
    ) -> int:
        """Calculate score based on momentum."""
        score = 70
        
        # RSI alignment
        rsi = indicators.get('RSI', 50)
        
        if is_buy:
            if rsi < 30:
                score += 15
                reasons.append("RSI oversold - good for long")
            elif rsi > 70:
                score -= 20
                reasons.append("RSI overbought - risky for long")
        else:
            if rsi > 70:
                score += 15
                reasons.append("RSI overbought - good for short")
            elif rsi < 30:
                score -= 20
                reasons.append("RSI oversold - risky for short")
        
        # Bar momentum (last few bars)
        closes = data['close'].values
        if len(closes) >= 3:
            bar_momentum = (closes[-1] - closes[-3]) / closes[-3] * 100
            
            if is_buy and bar_momentum > 0:
                score += 10
            elif not is_buy and bar_momentum < 0:
                score += 10
        
        return max(0, min(100, score))
    
    def _calculate_timing_score(
        self,
        data: Any,
        current_price: float,
        reasons: List[str]
    ) -> int:
        """Calculate score based on timing within range."""
        score = 70
        
        # Position within recent range
        recent_high = data['high'][-20:].max()
        recent_low = data['low'][-20:].min()
        range_size = recent_high - recent_low
        
        if range_size == 0:
            return score
        
        range_position = (current_price - recent_low) / range_size
        
        # Middle of range is generally safer
        if 0.3 <= range_position <= 0.7:
            score += 10
        elif range_position < 0.1 or range_position > 0.9:
            score -= 10
            reasons.append("Extended from mean")
        
        return max(0, min(100, score))
    
    def _calculate_structure_score(
        self,
        data: Any,
        is_buy: bool,
        reasons: List[str]
    ) -> int:
        """Calculate score based on market structure."""
        score = 70
        
        highs = data['high'].values
        lows = data['low'].values
        
        if len(highs) < 10:
            return score
        
        # Check for higher highs/higher lows (uptrend) or lower highs/lower lows (downtrend)
        recent_highs = highs[-10:]
        recent_lows = lows[-10:]
        
        higher_highs = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i-1])
        higher_lows = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] > recent_lows[i-1])
        
        uptrend_strength = (higher_highs + higher_lows) / (2 * (len(recent_highs) - 1))
        
        if is_buy:
            if uptrend_strength > 0.6:
                score += 15
                reasons.append("Strong uptrend structure")
            elif uptrend_strength < 0.3:
                score -= 10
                reasons.append("Weak uptrend structure")
        else:
            if uptrend_strength < 0.4:
                score += 15
                reasons.append("Strong downtrend structure")
            elif uptrend_strength > 0.7:
                score -= 10
                reasons.append("Against trend structure")
        
        return max(0, min(100, score))
    
    def _grade_score(self, score: int) -> tuple:
        """
        Grade the confluence score.
        
        Returns:
            (quality, should_reject, should_wait, confidence_multiplier)
        """
        if score >= 85:
            return ("premium", False, False, 1.0)
        elif score >= 70:
            return ("good", False, False, 0.90)
        elif score >= self.min_score_to_enter:
            return ("marginal", False, False, 0.75)
        elif score >= 30:
            return ("poor", False, True, 0.50)
        else:
            return ("reject", True, True, 0.0)
    
    def _calculate_suggested_entry(self, data: Any, is_buy: bool) -> float:
        """Calculate a suggested better entry price."""
        current = data['close'].iloc[-1]
        atr = (data['high'] - data['low']).mean()
        
        if is_buy:
            return current - atr * 0.5  # Look for pullback
        else:
            return current + atr * 0.5  # Look for rally
    
    def _create_result(self, score: int, reason: str, reasons: List[str]) -> Dict[str, Any]:
        """Create a result dict."""
        quality, should_reject, should_wait, conf_mult = self._grade_score(score)
        
        return {
            'score': score,
            'quality': quality,
            'should_reject': should_reject,
            'should_wait': should_wait,
            'confidence_multiplier': conf_mult,
            'suggested_entry': None,
            'reasons': reasons,
            'reason': reason
        }
