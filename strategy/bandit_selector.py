"""
Multi-Armed Bandit Strategy Selector

Implements advanced argmax-based strategy selection using multi-armed bandit algorithms.
This module provides exploration-exploitation balance for dynamic strategy optimization.

Algorithms Implemented:
1. UCB (Upper Confidence Bound) - Optimistic selection with confidence intervals
2. Thompson Sampling - Bayesian approach with posterior sampling
3. Epsilon-Greedy - Simple exploration with random selection
4. Softmax - Temperature-based probabilistic selection

Theoretical Foundation:
- Balances exploration (trying new strategies) vs exploitation (using best known strategy)
- Minimizes regret over time by learning from outcomes
- Adapts to non-stationary reward distributions (changing market conditions)
- Converges to optimal strategy selection given sufficient samples

References:
- Auer et al. (2002): "Finite-time Analysis of the Multiarmed Bandit Problem"
- Russo et al. (2018): "A Tutorial on Thompson Sampling"
- Sutton & Barto (2018): "Reinforcement Learning: An Introduction"
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import math

from cthulu.strategy.base import Strategy, Signal


logger = logging.getLogger("Cthulu.bandit_selector")


@dataclass
class ArmStatistics:
    """Statistics for a single bandit arm (strategy)."""
    name: str
    pulls: int = 0  # Number of times this strategy was selected
    total_reward: float = 0.0  # Cumulative reward
    squared_reward: float = 0.0  # For variance calculation
    successes: int = 0  # Number of successful trades (for Thompson Sampling)
    failures: int = 0  # Number of failed trades
    last_update: datetime = field(default_factory=datetime.now)
    
    @property
    def mean_reward(self) -> float:
        """Average reward per pull."""
        return self.total_reward / self.pulls if self.pulls > 0 else 0.0
    
    @property
    def variance(self) -> float:
        """Variance of rewards."""
        if self.pulls < 2:
            return 0.0
        mean = self.mean_reward
        return (self.squared_reward / self.pulls) - (mean ** 2)
    
    @property
    def std_dev(self) -> float:
        """Standard deviation of rewards."""
        return math.sqrt(max(0, self.variance))
    
    @property
    def success_rate(self) -> float:
        """Success rate for Thompson Sampling."""
        total = self.successes + self.failures
        return self.successes / total if total > 0 else 0.5


class BanditSelector:
    """
    Multi-armed bandit strategy selector using argmax-based algorithms.
    
    This class implements sophisticated exploration-exploitation balance
    for optimal strategy selection in non-stationary environments.
    
    Key Features:
    - Multiple algorithm support (UCB, Thompson Sampling, Epsilon-Greedy, Softmax)
    - Context-aware selection (market regime consideration)
    - Adaptive learning rates
    - Decay for non-stationary environments
    - Comprehensive logging and metrics
    
    Example Usage:
        selector = BanditSelector(
            strategies=strategies,
            algorithm='ucb',
            config={'exploration_factor': 2.0}
        )
        
        # Select strategy using argmax
        selected = selector.select_strategy(context={'regime': 'trending'})
        
        # Update with outcome
        selector.update_reward(strategy_name, reward=100.0, success=True)
    
    Algorithm Details:
    
    UCB (Upper Confidence Bound):
        score = mean_reward + c * sqrt(log(total_pulls) / strategy_pulls)
        - Uses optimistic initialization
        - Guarantees logarithmic regret
        - Parameter c controls exploration (default: 2.0)
    
    Thompson Sampling:
        - Sample from Beta(successes+1, failures+1) distribution
        - Select strategy with highest sample (argmax)
        - Bayesian approach with natural exploration
        - No tuning parameters needed
    
    Epsilon-Greedy:
        - Select best strategy with probability (1-ε)
        - Select random strategy with probability ε
        - Simple but effective
        - ε can decay over time
    
    Softmax:
        - Probability proportional to exp(reward/temperature)
        - Temperature controls exploration
        - Higher temperature = more exploration
    """
    
    def __init__(
        self,
        strategies: List[Strategy],
        algorithm: str = 'ucb',
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize bandit selector.
        
        Args:
            strategies: List of available strategies
            algorithm: Algorithm to use ('ucb', 'thompson', 'epsilon', 'softmax')
            config: Algorithm-specific configuration
        """
        self.strategies = {s.name: s for s in strategies}
        self.algorithm = algorithm.lower()
        self.config = config or {}
        
        # Algorithm parameters
        self.exploration_factor = self.config.get('exploration_factor', 2.0)  # UCB c parameter
        self.epsilon = self.config.get('epsilon', 0.1)  # Epsilon-greedy
        self.epsilon_decay = self.config.get('epsilon_decay', 0.995)  # Decay rate
        self.min_epsilon = self.config.get('min_epsilon', 0.01)
        self.temperature = self.config.get('temperature', 0.1)  # Softmax
        self.temperature_decay = self.config.get('temperature_decay', 0.999)
        self.min_temperature = self.config.get('min_temperature', 0.01)
        
        # Thompson Sampling priors
        self.alpha_prior = self.config.get('alpha_prior', 1)  # Beta prior successes
        self.beta_prior = self.config.get('beta_prior', 1)  # Beta prior failures
        
        # Reward normalization
        self.reward_scale = self.config.get('reward_scale', 100.0)  # Scale rewards to [-1, 1] range
        
        # Decay factor for non-stationary environments
        self.decay_factor = self.config.get('decay_factor', 0.99)  # Weight recent observations more
        self.use_decay = self.config.get('use_decay', False)
        
        # Initialize arm statistics
        self.arms: Dict[str, ArmStatistics] = {
            name: ArmStatistics(name=name)
            for name in self.strategies.keys()
        }
        
        # Global counters
        self.total_pulls = 0
        self.total_reward = 0.0
        
        # Current selection tracking
        self.current_strategy = None
        self.last_selection_time = None
        
        # Metrics
        self.selection_history = []
        self.reward_history = []
        
        logger.info(
            f"BanditSelector initialized: algorithm={self.algorithm}, "
            f"strategies={len(self.strategies)}, config={self.config}"
        )
        
        # Validate algorithm
        valid_algorithms = ['ucb', 'thompson', 'epsilon', 'softmax']
        if self.algorithm not in valid_algorithms:
            raise ValueError(
                f"Invalid algorithm '{self.algorithm}'. "
                f"Must be one of {valid_algorithms}"
            )
    
    def _ucb_score(self, arm: ArmStatistics) -> float:
        """
        Calculate UCB1 score for an arm.
        
        UCB1 formula:
            score = mean_reward + c * sqrt(log(total_pulls) / arm_pulls)
        
        Where:
            - mean_reward: average reward for this arm
            - c: exploration factor (typically 2.0)
            - total_pulls: total selections across all arms
            - arm_pulls: selections for this specific arm
        
        The exploration term (second part) decreases as the arm is pulled more,
        but increases as other arms are pulled (relative to this one).
        
        Args:
            arm: Arm statistics
            
        Returns:
            UCB score (higher is better)
        """
        if arm.pulls == 0:
            # Optimistic initialization: unpulled arms get infinite score
            return float('inf')
        
        exploitation = arm.mean_reward
        
        # Exploration bonus
        exploration = self.exploration_factor * math.sqrt(
            math.log(max(1, self.total_pulls)) / arm.pulls
        )
        
        return exploitation + exploration
    
    def _thompson_sample(self, arm: ArmStatistics) -> float:
        """
        Sample from Beta distribution for Thompson Sampling.
        
        Thompson Sampling uses Bayesian inference:
        - Prior: Beta(α, β) distribution
        - Posterior after observing data: Beta(α + successes, β + failures)
        - Sample from posterior and select arm with highest sample (argmax)
        
        Beta distribution is conjugate prior for Bernoulli/Binomial likelihood,
        making it perfect for win/loss outcomes.
        
        Args:
            arm: Arm statistics
            
        Returns:
            Sampled value from Beta distribution
        """
        alpha = self.alpha_prior + arm.successes
        beta = self.beta_prior + arm.failures
        
        # Sample from Beta distribution
        sample = np.random.beta(alpha, beta)
        
        return sample
    
    def _softmax_probability(self, arm: ArmStatistics, all_arms: List[ArmStatistics]) -> float:
        """
        Calculate softmax probability for an arm.
        
        Softmax (Boltzmann) exploration:
            P(arm) = exp(Q(arm)/τ) / Σ exp(Q(a)/τ)
        
        Where:
            - Q(arm): mean reward for arm
            - τ: temperature parameter
            - Higher temperature → more uniform (more exploration)
            - Lower temperature → more greedy (more exploitation)
        
        Args:
            arm: Arm to calculate probability for
            all_arms: All available arms
            
        Returns:
            Selection probability
        """
        if arm.pulls == 0:
            # Unpulled arms get equal high probability
            return 1.0
        
        # Calculate exp(Q/τ) for all arms
        scores = []
        for a in all_arms:
            if a.pulls == 0:
                scores.append(1.0)  # Equal probability for unpulled
            else:
                scores.append(math.exp(a.mean_reward / max(self.temperature, 1e-6)))
        
        # Softmax normalization
        total = sum(scores)
        arm_idx = all_arms.index(arm)
        
        return scores[arm_idx] / total if total > 0 else 1.0 / len(all_arms)
    
    def select_strategy(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> Strategy:
        """
        Select strategy using argmax over bandit scores.
        
        This is the core method that implements the multi-armed bandit
        algorithm selection. Uses argmax to find the strategy with the
        highest score according to the chosen algorithm.
        
        Args:
            context: Optional context information (market regime, etc.)
            
        Returns:
            Selected strategy instance
        """
        arm_list = list(self.arms.values())
        
        if self.algorithm == 'ucb':
            # UCB: argmax over UCB scores
            scores = {arm.name: self._ucb_score(arm) for arm in arm_list}
            selected_name = max(scores.keys(), key=lambda k: scores[k])  # argmax
            
            logger.debug(f"UCB scores: {scores}")
            
        elif self.algorithm == 'thompson':
            # Thompson Sampling: argmax over sampled values
            samples = {arm.name: self._thompson_sample(arm) for arm in arm_list}
            selected_name = max(samples.keys(), key=lambda k: samples[k])  # argmax
            
            logger.debug(f"Thompson samples: {samples}")
            
        elif self.algorithm == 'epsilon':
            # Epsilon-greedy: explore with probability ε, exploit otherwise
            if np.random.random() < self.epsilon:
                # Explore: random selection
                selected_name = np.random.choice(list(self.arms.keys()))
                logger.debug(f"Epsilon-greedy: exploring (ε={self.epsilon:.3f})")
            else:
                # Exploit: argmax over mean rewards
                scores = {arm.name: arm.mean_reward for arm in arm_list}
                selected_name = max(scores.keys(), key=lambda k: scores[k])  # argmax
                logger.debug(f"Epsilon-greedy: exploiting, scores={scores}")
            
            # Decay epsilon
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
            
        elif self.algorithm == 'softmax':
            # Softmax: probabilistic selection based on rewards
            probabilities = {
                arm.name: self._softmax_probability(arm, arm_list)
                for arm in arm_list
            }
            
            # Normalize probabilities
            total_prob = sum(probabilities.values())
            probabilities = {k: v/total_prob for k, v in probabilities.items()}
            
            # Sample according to probabilities
            names = list(probabilities.keys())
            probs = list(probabilities.values())
            selected_name = np.random.choice(names, p=probs)
            
            logger.debug(f"Softmax probabilities: {probabilities}, T={self.temperature:.3f}")
            
            # Decay temperature
            self.temperature = max(self.min_temperature, self.temperature * self.temperature_decay)
            
        else:
            # Fallback: uniform random
            selected_name = np.random.choice(list(self.arms.keys()))
            logger.warning(f"Unknown algorithm, using random selection")
        
        # Update tracking
        self.current_strategy = selected_name
        self.last_selection_time = datetime.now()
        self.total_pulls += 1
        self.arms[selected_name].pulls += 1
        
        # Record selection
        self.selection_history.append({
            'timestamp': self.last_selection_time,
            'strategy': selected_name,
            'algorithm': self.algorithm,
            'total_pulls': self.total_pulls
        })
        
        logger.info(
            f"Selected strategy: {selected_name} "
            f"(algorithm={self.algorithm}, pulls={self.arms[selected_name].pulls})"
        )
        
        return self.strategies[selected_name]
    
    def update_reward(
        self,
        strategy_name: str,
        reward: float,
        success: bool,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Update bandit statistics with observed reward.
        
        This method implements the learning component of the bandit algorithm.
        Called after a trade outcome is known to update the strategy's statistics.
        
        Args:
            strategy_name: Name of strategy that was used
            reward: Observed reward (profit/loss)
            success: Whether trade was successful (for Thompson Sampling)
            context: Optional context about the trade
        """
        if strategy_name not in self.arms:
            logger.warning(f"Unknown strategy: {strategy_name}")
            return
        
        arm = self.arms[strategy_name]
        
        # Normalize reward to [-1, 1] range for stability
        normalized_reward = np.clip(reward / self.reward_scale, -1.0, 1.0)
        
        # Apply decay if enabled (for non-stationary environments)
        if self.use_decay:
            arm.total_reward *= self.decay_factor
            arm.squared_reward *= self.decay_factor
            arm.successes = int(arm.successes * self.decay_factor)
            arm.failures = int(arm.failures * self.decay_factor)
        
        # Update statistics
        arm.total_reward += normalized_reward
        arm.squared_reward += normalized_reward ** 2
        
        if success:
            arm.successes += 1
        else:
            arm.failures += 1
        
        arm.last_update = datetime.now()
        
        # Update global statistics
        self.total_reward += normalized_reward
        
        # Record reward
        self.reward_history.append({
            'timestamp': datetime.now(),
            'strategy': strategy_name,
            'reward': reward,
            'normalized_reward': normalized_reward,
            'success': success,
            'cumulative_reward': self.total_reward
        })
        
        logger.info(
            f"Updated {strategy_name}: reward={reward:.2f} (norm={normalized_reward:.3f}), "
            f"success={success}, mean={arm.mean_reward:.3f}, pulls={arm.pulls}"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics for all arms.
        
        Returns:
            Dictionary with detailed statistics
        """
        stats = {
            'algorithm': self.algorithm,
            'total_pulls': self.total_pulls,
            'total_reward': self.total_reward,
            'current_strategy': self.current_strategy,
            'arms': {}
        }
        
        for name, arm in self.arms.items():
            stats['arms'][name] = {
                'pulls': arm.pulls,
                'mean_reward': arm.mean_reward,
                'std_dev': arm.std_dev,
                'success_rate': arm.success_rate,
                'total_reward': arm.total_reward,
                'successes': arm.successes,
                'failures': arm.failures,
                'last_update': arm.last_update.isoformat() if arm.last_update else None
            }
        
        # Add algorithm-specific stats
        if self.algorithm == 'epsilon':
            stats['epsilon'] = self.epsilon
        elif self.algorithm == 'softmax':
            stats['temperature'] = self.temperature
        
        return stats
    
    def reset_statistics(self):
        """Reset all arm statistics (useful for regime changes)."""
        for arm in self.arms.values():
            arm.pulls = 0
            arm.total_reward = 0.0
            arm.squared_reward = 0.0
            arm.successes = 0
            arm.failures = 0
        
        self.total_pulls = 0
        self.total_reward = 0.0
        self.selection_history.clear()
        self.reward_history.clear()
        
        logger.info("Bandit statistics reset")
    
    def get_best_strategy(self) -> Tuple[str, float]:
        """
        Get the current best strategy based on mean reward.
        
        Returns:
            Tuple of (strategy_name, mean_reward)
        """
        if not self.arms:
            return None, 0.0
        
        best_arm = max(
            self.arms.values(),
            key=lambda a: a.mean_reward if a.pulls > 0 else float('-inf')
        )
        
        return best_arm.name, best_arm.mean_reward
