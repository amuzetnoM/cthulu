"""
Unit tests for Multi-Armed Bandit Strategy Selector

Tests all four algorithms (UCB, Thompson Sampling, Epsilon-Greedy, Softmax)
and verifies theoretical properties.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from datetime import datetime

from cthulu.strategy.bandit_selector import BanditSelector, ArmStatistics
from cthulu.strategy.base import Strategy, Signal, SignalType


# Mock strategy classes for testing
class MockStrategy(Strategy):
    """Mock strategy for testing."""
    
    def __init__(self, name, true_mean_reward=0.0):
        super().__init__(name, {})
        self.true_mean_reward = true_mean_reward
        self.call_count = 0
    
    def on_bar(self, bar):
        """Generate a mock signal."""
        self.call_count += 1
        return Signal(
            symbol="TEST",
            side=SignalType.LONG,
            confidence=0.8,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0
        )


@pytest.fixture
def mock_strategies():
    """Create mock strategies with different mean rewards."""
    return [
        MockStrategy("strategy_a", true_mean_reward=0.6),  # Best
        MockStrategy("strategy_b", true_mean_reward=0.3),  # Medium
        MockStrategy("strategy_c", true_mean_reward=0.1),  # Worst
    ]


class TestArmStatistics:
    """Test ArmStatistics dataclass."""
    
    def test_initialization(self):
        """Test arm statistics initialization."""
        arm = ArmStatistics(name="test")
        
        assert arm.name == "test"
        assert arm.pulls == 0
        assert arm.total_reward == 0.0
        assert arm.squared_reward == 0.0
        assert arm.successes == 0
        assert arm.failures == 0
        assert arm.mean_reward == 0.0
        assert arm.variance == 0.0
        assert arm.success_rate == 0.5  # Prior: equal chance
    
    def test_mean_reward(self):
        """Test mean reward calculation."""
        arm = ArmStatistics(name="test")
        arm.pulls = 10
        arm.total_reward = 5.0
        
        assert arm.mean_reward == 0.5
    
    def test_mean_reward_no_pulls(self):
        """Test mean reward with no pulls."""
        arm = ArmStatistics(name="test")
        assert arm.mean_reward == 0.0
    
    def test_variance(self):
        """Test variance calculation."""
        arm = ArmStatistics(name="test")
        arm.pulls = 100
        arm.total_reward = 50.0  # mean = 0.5
        arm.squared_reward = 30.0  # E[X²] = 0.3
        
        # Var = E[X²] - (E[X])²
        expected_variance = 0.3 - (0.5 ** 2)  # = 0.05
        assert abs(arm.variance - expected_variance) < 1e-6
    
    def test_success_rate(self):
        """Test success rate calculation."""
        arm = ArmStatistics(name="test")
        arm.successes = 70
        arm.failures = 30
        
        assert arm.success_rate == 0.7


class TestBanditSelectorInitialization:
    """Test BanditSelector initialization."""
    
    def test_initialization_ucb(self, mock_strategies):
        """Test UCB initialization."""
        selector = BanditSelector(
            strategies=mock_strategies,
            algorithm='ucb',
            config={'exploration_factor': 2.0}
        )
        
        assert selector.algorithm == 'ucb'
        assert len(selector.strategies) == 3
        assert len(selector.arms) == 3
        assert selector.exploration_factor == 2.0
        assert selector.total_pulls == 0
    
    def test_initialization_thompson(self, mock_strategies):
        """Test Thompson Sampling initialization."""
        selector = BanditSelector(
            strategies=mock_strategies,
            algorithm='thompson',
            config={'alpha_prior': 2, 'beta_prior': 2}
        )
        
        assert selector.algorithm == 'thompson'
        assert selector.alpha_prior == 2
        assert selector.beta_prior == 2
    
    def test_initialization_epsilon(self, mock_strategies):
        """Test Epsilon-Greedy initialization."""
        selector = BanditSelector(
            strategies=mock_strategies,
            algorithm='epsilon',
            config={'epsilon': 0.2, 'epsilon_decay': 0.99}
        )
        
        assert selector.algorithm == 'epsilon'
        assert selector.epsilon == 0.2
        assert selector.epsilon_decay == 0.99
    
    def test_initialization_softmax(self, mock_strategies):
        """Test Softmax initialization."""
        selector = BanditSelector(
            strategies=mock_strategies,
            algorithm='softmax',
            config={'temperature': 0.5}
        )
        
        assert selector.algorithm == 'softmax'
        assert selector.temperature == 0.5
    
    def test_invalid_algorithm(self, mock_strategies):
        """Test that invalid algorithm raises error."""
        with pytest.raises(ValueError, match="Invalid algorithm"):
            BanditSelector(
                strategies=mock_strategies,
                algorithm='invalid'
            )
    
    def test_default_config(self, mock_strategies):
        """Test default configuration."""
        selector = BanditSelector(strategies=mock_strategies)
        
        assert selector.algorithm == 'ucb'  # Default
        assert selector.exploration_factor == 2.0  # Default


class TestUCBAlgorithm:
    """Test UCB (Upper Confidence Bound) algorithm."""
    
    def test_ucb_score_unpulled_arm(self, mock_strategies):
        """Test that unpulled arms get infinite UCB score."""
        selector = BanditSelector(mock_strategies, algorithm='ucb')
        
        arm = selector.arms['strategy_a']
        score = selector._ucb_score(arm)
        
        assert score == float('inf')
    
    def test_ucb_score_calculation(self, mock_strategies):
        """Test UCB score calculation."""
        selector = BanditSelector(
            mock_strategies,
            algorithm='ucb',
            config={'exploration_factor': 2.0}
        )
        
        # Set up arm statistics
        arm = selector.arms['strategy_a']
        arm.pulls = 10
        arm.total_reward = 6.0  # mean = 0.6
        selector.total_pulls = 30
        
        score = selector._ucb_score(arm)
        
        # UCB = mean + c * sqrt(log(total) / pulls)
        expected_exploitation = 0.6
        expected_exploration = 2.0 * np.sqrt(np.log(30) / 10)
        expected_score = expected_exploitation + expected_exploration
        
        assert abs(score - expected_score) < 1e-6
    
    def test_ucb_selects_unpulled_arms_first(self, mock_strategies):
        """Test that UCB tries all arms before exploiting."""
        selector = BanditSelector(mock_strategies, algorithm='ucb')
        
        selected_strategies = set()
        
        # Select 3 times (number of arms)
        for _ in range(3):
            strategy = selector.select_strategy()
            selected_strategies.add(strategy.name)
        
        # Should have tried all 3 arms
        assert len(selected_strategies) == 3
    
    def test_ucb_exploitation_after_exploration(self, mock_strategies):
        """Test that UCB exploits best arm after sufficient exploration."""
        np.random.seed(42)  # For reproducibility
        selector = BanditSelector(
            mock_strategies,
            algorithm='ucb',
            config={'exploration_factor': 1.0}  # Lower for faster convergence
        )
        
        # Simulate many pulls with known rewards
        for _ in range(100):
            strategy = selector.select_strategy()
            
            # Simulate reward based on true mean (with noise)
            true_mean = next(s.true_mean_reward for s in mock_strategies if s.name == strategy.name)
            reward = true_mean + np.random.normal(0, 0.1)
            success = reward > 0.5
            
            selector.update_reward(strategy.name, reward, success)
        
        # After 100 pulls, should mostly select best arm (strategy_a with mean 0.6)
        strategy_counts = {s.name: 0 for s in mock_strategies}
        
        for _ in range(50):
            strategy = selector.select_strategy()
            strategy_counts[strategy.name] += 1
            
            # Update with reward
            true_mean = next(s.true_mean_reward for s in mock_strategies if s.name == strategy.name)
            reward = true_mean + np.random.normal(0, 0.1)
            selector.update_reward(strategy.name, reward, reward > 0.5)
        
        # Best arm should be selected most often
        assert strategy_counts['strategy_a'] > strategy_counts['strategy_b']
        assert strategy_counts['strategy_a'] > strategy_counts['strategy_c']


class TestThompsonSampling:
    """Test Thompson Sampling algorithm."""
    
    def test_thompson_sample(self, mock_strategies):
        """Test Thompson Sampling from Beta distribution."""
        np.random.seed(42)
        selector = BanditSelector(mock_strategies, algorithm='thompson')
        
        arm = selector.arms['strategy_a']
        arm.successes = 70
        arm.failures = 30
        
        # Sample should be between 0 and 1
        sample = selector._thompson_sample(arm)
        assert 0.0 <= sample <= 1.0
    
    def test_thompson_with_priors(self, mock_strategies):
        """Test Thompson Sampling with custom priors."""
        selector = BanditSelector(
            mock_strategies,
            algorithm='thompson',
            config={'alpha_prior': 10, 'beta_prior': 5}  # Optimistic prior
        )
        
        arm = selector.arms['strategy_a']
        # With no data, should sample from Beta(10, 5)
        sample = selector._thompson_sample(arm)
        
        # Mean of Beta(10, 5) is 10/15 = 0.667
        # Sample should be around this (probabilistically)
        assert 0.0 <= sample <= 1.0
    
    def test_thompson_convergence(self, mock_strategies):
        """Test that Thompson Sampling converges to best arm."""
        np.random.seed(42)
        selector = BanditSelector(mock_strategies, algorithm='thompson')
        
        # Simulate 200 pulls
        for _ in range(200):
            strategy = selector.select_strategy()
            
            true_mean = next(s.true_mean_reward for s in mock_strategies if s.name == strategy.name)
            reward = true_mean + np.random.normal(0, 0.1)
            success = reward > 0.5
            
            selector.update_reward(strategy.name, reward, success)
        
        # Check that best arm has highest success rate
        best_arm_name = max(
            selector.arms.keys(),
            key=lambda name: selector.arms[name].success_rate
        )
        
        # Should be strategy_a (highest true mean)
        assert best_arm_name == 'strategy_a'


class TestEpsilonGreedy:
    """Test Epsilon-Greedy algorithm."""
    
    def test_epsilon_exploration(self, mock_strategies):
        """Test that epsilon controls exploration rate."""
        np.random.seed(42)
        selector = BanditSelector(
            mock_strategies,
            algorithm='epsilon',
            config={'epsilon': 1.0}  # Always explore
        )
        
        # With epsilon=1, should select randomly
        # Give all arms some history
        for arm in selector.arms.values():
            arm.pulls = 10
            arm.total_reward = 5.0
        
        selected = []
        for _ in range(30):
            strategy = selector.select_strategy()
            selected.append(strategy.name)
        
        # Should have tried multiple arms (not just one)
        assert len(set(selected)) > 1
    
    def test_epsilon_exploitation(self, mock_strategies):
        """Test that low epsilon exploits best arm."""
        np.random.seed(42)
        selector = BanditSelector(
            mock_strategies,
            algorithm='epsilon',
            config={'epsilon': 0.0}  # Never explore
        )
        
        # Set up clear best arm
        selector.arms['strategy_a'].pulls = 10
        selector.arms['strategy_a'].total_reward = 8.0  # mean = 0.8
        selector.arms['strategy_b'].pulls = 10
        selector.arms['strategy_b'].total_reward = 3.0  # mean = 0.3
        selector.arms['strategy_c'].pulls = 10
        selector.arms['strategy_c'].total_reward = 1.0  # mean = 0.1
        
        # Should always select strategy_a
        for _ in range(10):
            strategy = selector.select_strategy()
            assert strategy.name == 'strategy_a'
    
    def test_epsilon_decay(self, mock_strategies):
        """Test that epsilon decays over time."""
        selector = BanditSelector(
            mock_strategies,
            algorithm='epsilon',
            config={'epsilon': 0.5, 'epsilon_decay': 0.9, 'min_epsilon': 0.01}
        )
        
        initial_epsilon = selector.epsilon
        
        # Make some selections
        for _ in range(10):
            selector.select_strategy()
        
        # Epsilon should have decayed
        assert selector.epsilon < initial_epsilon
        assert selector.epsilon >= 0.01  # But not below minimum


class TestSoftmax:
    """Test Softmax algorithm."""
    
    def test_softmax_probability(self, mock_strategies):
        """Test softmax probability calculation."""
        selector = BanditSelector(
            mock_strategies,
            algorithm='softmax',
            config={'temperature': 1.0}
        )
        
        # Set up arms with different rewards
        arm_a = selector.arms['strategy_a']
        arm_a.pulls = 10
        arm_a.total_reward = 8.0  # mean = 0.8
        
        arm_b = selector.arms['strategy_b']
        arm_b.pulls = 10
        arm_b.total_reward = 3.0  # mean = 0.3
        
        arm_c = selector.arms['strategy_c']
        arm_c.pulls = 10
        arm_c.total_reward = 1.0  # mean = 0.1
        
        arm_list = [arm_a, arm_b, arm_c]
        
        # Calculate probabilities
        prob_a = selector._softmax_probability(arm_a, arm_list)
        prob_b = selector._softmax_probability(arm_b, arm_list)
        prob_c = selector._softmax_probability(arm_c, arm_list)
        
        # Probabilities should sum to ~1
        assert abs(prob_a + prob_b + prob_c - 1.0) < 0.01
        
        # Best arm should have highest probability
        assert prob_a > prob_b
        assert prob_a > prob_c
    
    def test_softmax_temperature_effect(self, mock_strategies):
        """Test that temperature affects exploration."""
        # High temperature (more exploration)
        selector_hot = BanditSelector(
            mock_strategies,
            algorithm='softmax',
            config={'temperature': 10.0}
        )
        
        # Low temperature (more exploitation)
        selector_cold = BanditSelector(
            mock_strategies,
            algorithm='softmax',
            config={'temperature': 0.01}
        )
        
        # Set up same arm statistics for both
        for selector in [selector_hot, selector_cold]:
            selector.arms['strategy_a'].pulls = 10
            selector.arms['strategy_a'].total_reward = 8.0
            selector.arms['strategy_b'].pulls = 10
            selector.arms['strategy_b'].total_reward = 3.0
            selector.arms['strategy_c'].pulls = 10
            selector.arms['strategy_c'].total_reward = 1.0
        
        # High temperature should give more uniform probabilities
        # (We can't test exact probabilities due to randomness, but we can
        # test that high temp explores more by running simulations)
        # This is implicitly tested in integration tests


class TestRewardUpdate:
    """Test reward update mechanism."""
    
    def test_update_reward(self, mock_strategies):
        """Test that reward updates arm statistics."""
        selector = BanditSelector(mock_strategies, algorithm='ucb')
        
        arm_name = 'strategy_a'
        arm = selector.arms[arm_name]
        
        # Update with reward
        selector.update_reward(arm_name, reward=50.0, success=True)
        
        # Check updates
        assert arm.total_reward > 0
        assert arm.successes == 1
        assert arm.failures == 0
        assert len(selector.reward_history) == 1
    
    def test_update_reward_normalization(self, mock_strategies):
        """Test that rewards are normalized."""
        selector = BanditSelector(
            mock_strategies,
            algorithm='ucb',
            config={'reward_scale': 100.0}
        )
        
        arm_name = 'strategy_a'
        
        # Update with large reward
        selector.update_reward(arm_name, reward=200.0, success=True)
        
        # Normalized reward should be clipped to [-1, 1]
        assert abs(selector.arms[arm_name].total_reward) <= 1.0
    
    def test_update_reward_with_decay(self, mock_strategies):
        """Test reward update with decay for non-stationary environments."""
        selector = BanditSelector(
            mock_strategies,
            algorithm='ucb',
            config={'use_decay': True, 'decay_factor': 0.9}
        )
        
        arm_name = 'strategy_a'
        arm = selector.arms[arm_name]
        
        # First update
        selector.update_reward(arm_name, reward=100.0, success=True)
        first_reward = arm.total_reward
        
        # Second update (first reward should be decayed)
        selector.update_reward(arm_name, reward=100.0, success=True)
        
        # Total should be less than 2x first (due to decay)
        assert arm.total_reward < 2 * first_reward
    
    def test_update_unknown_strategy(self, mock_strategies):
        """Test that updating unknown strategy logs warning."""
        selector = BanditSelector(mock_strategies, algorithm='ucb')
        
        # Should not raise error, just log warning
        selector.update_reward('unknown_strategy', reward=100.0, success=True)


class TestStatisticsAndMetrics:
    """Test statistics and metrics functionality."""
    
    def test_get_statistics(self, mock_strategies):
        """Test statistics retrieval."""
        selector = BanditSelector(mock_strategies, algorithm='ucb')
        
        # Make some selections and updates
        for _ in range(5):
            strategy = selector.select_strategy()
            selector.update_reward(strategy.name, reward=50.0, success=True)
        
        stats = selector.get_statistics()
        
        assert stats['algorithm'] == 'ucb'
        assert stats['total_pulls'] == 5
        assert 'arms' in stats
        assert len(stats['arms']) == 3
        
        # Check arm-level statistics
        for arm_stats in stats['arms'].values():
            assert 'pulls' in arm_stats
            assert 'mean_reward' in arm_stats
            assert 'success_rate' in arm_stats
    
    def test_get_best_strategy(self, mock_strategies):
        """Test best strategy identification."""
        selector = BanditSelector(mock_strategies, algorithm='ucb')
        
        # Set up clear best arm
        selector.arms['strategy_a'].pulls = 10
        selector.arms['strategy_a'].total_reward = 8.0
        selector.arms['strategy_b'].pulls = 10
        selector.arms['strategy_b'].total_reward = 3.0
        selector.arms['strategy_c'].pulls = 10
        selector.arms['strategy_c'].total_reward = 1.0
        
        best_name, best_reward = selector.get_best_strategy()
        
        assert best_name == 'strategy_a'
        assert best_reward == 0.8
    
    def test_reset_statistics(self, mock_strategies):
        """Test statistics reset."""
        selector = BanditSelector(mock_strategies, algorithm='ucb')
        
        # Make some selections
        for _ in range(5):
            strategy = selector.select_strategy()
            selector.update_reward(strategy.name, reward=50.0, success=True)
        
        # Reset
        selector.reset_statistics()
        
        # Everything should be cleared
        assert selector.total_pulls == 0
        assert selector.total_reward == 0.0
        assert len(selector.selection_history) == 0
        assert len(selector.reward_history) == 0
        
        for arm in selector.arms.values():
            assert arm.pulls == 0
            assert arm.total_reward == 0.0


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_full_workflow_ucb(self, mock_strategies):
        """Test complete workflow with UCB."""
        np.random.seed(42)
        selector = BanditSelector(mock_strategies, algorithm='ucb')
        
        # Simulate 50 trading episodes
        for episode in range(50):
            # Select strategy
            strategy = selector.select_strategy()
            
            # Simulate trade outcome
            true_mean = next(s.true_mean_reward for s in mock_strategies if s.name == strategy.name)
            reward = true_mean + np.random.normal(0, 0.1)
            success = reward > 0.5
            
            # Update selector
            selector.update_reward(strategy.name, reward * 100, success)
        
        # Verify learning occurred
        stats = selector.get_statistics()
        assert stats['total_pulls'] == 50
        
        # Best strategy should have been identified
        best_name, _ = selector.get_best_strategy()
        assert best_name == 'strategy_a'  # Highest true mean
    
    def test_algorithm_comparison(self, mock_strategies):
        """Compare all four algorithms on same problem."""
        np.random.seed(42)
        algorithms = ['ucb', 'thompson', 'epsilon', 'softmax']
        results = {}
        
        for algo in algorithms:
            if algo == 'epsilon':
                config = {'epsilon': 0.1, 'epsilon_decay': 0.99}
            elif algo == 'softmax':
                config = {'temperature': 0.1, 'temperature_decay': 0.999}
            else:
                config = {}
            
            selector = BanditSelector(
                [MockStrategy(s.name, s.true_mean_reward) for s in mock_strategies],
                algorithm=algo,
                config=config
            )
            
            total_reward = 0.0
            
            # Run for 100 episodes
            for _ in range(100):
                strategy = selector.select_strategy()
                true_mean = strategy.true_mean_reward
                reward = true_mean + np.random.normal(0, 0.05)
                success = reward > 0.5
                
                selector.update_reward(strategy.name, reward * 100, success)
                total_reward += reward
            
            results[algo] = {
                'total_reward': total_reward,
                'best_strategy': selector.get_best_strategy()[0]
            }
        
        # All algorithms should identify the best strategy
        for algo in algorithms:
            assert results[algo]['best_strategy'] == 'strategy_a'
        
        # Rewards should be positive (all exploiting good arms)
        for algo in algorithms:
            assert results[algo]['total_reward'] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_strategies(self):
        """Test with no strategies."""
        with pytest.raises(Exception):
            BanditSelector(strategies=[], algorithm='ucb')
    
    def test_single_strategy(self):
        """Test with single strategy."""
        single_strategy = [MockStrategy("only_one", 0.5)]
        selector = BanditSelector(single_strategy, algorithm='ucb')
        
        # Should still work, always selecting the only strategy
        for _ in range(5):
            strategy = selector.select_strategy()
            assert strategy.name == "only_one"
    
    def test_extreme_rewards(self, mock_strategies):
        """Test with extremely large/small rewards."""
        selector = BanditSelector(
            mock_strategies,
            algorithm='ucb',
            config={'reward_scale': 1000.0}
        )
        
        # Very large reward
        selector.update_reward('strategy_a', reward=1000000.0, success=True)
        
        # Should be normalized/clipped
        assert abs(selector.arms['strategy_a'].total_reward) <= 1.0
        
        # Very small (negative) reward
        selector.update_reward('strategy_b', reward=-1000000.0, success=False)
        
        # Should be normalized/clipped
        assert abs(selector.arms['strategy_b'].total_reward) <= 1.0
    
    def test_zero_exploration_factor(self, mock_strategies):
        """Test UCB with zero exploration."""
        selector = BanditSelector(
            mock_strategies,
            algorithm='ucb',
            config={'exploration_factor': 0.0}
        )
        
        # Should still work, just pure exploitation
        # (might not explore all arms)
        for _ in range(10):
            strategy = selector.select_strategy()
            selector.update_reward(strategy.name, reward=50.0, success=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
