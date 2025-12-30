"""
Reinforcement Learning Module

Implements RL agents for auto-tuning Cthulu parameters.
Uses Q-learning with argmax action selection and policy gradients with softmax.
Fully decoupled from main trading loop.
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import numpy as np
from collections import defaultdict, deque


@dataclass
class RLState:
    """State representation for RL agent."""
    # Market context
    volatility_regime: str  # 'low', 'medium', 'high'
    trend_regime: str  # 'uptrend', 'downtrend', 'ranging'
    
    # Performance context
    recent_win_rate: float  # Last N trades
    current_drawdown: float  # Current drawdown percentage
    
    # Time context
    hour_of_day: int
    day_of_week: int
    
    def to_tuple(self) -> Tuple:
        """Convert to tuple for use as dictionary key."""
        return (
            self.volatility_regime,
            self.trend_regime,
            int(self.recent_win_rate * 10),  # Discretize
            int(self.current_drawdown * 10),
            self.hour_of_day,
            self.day_of_week
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'volatility_regime': self.volatility_regime,
            'trend_regime': self.trend_regime,
            'recent_win_rate': self.recent_win_rate,
            'current_drawdown': self.current_drawdown,
            'hour_of_day': self.hour_of_day,
            'day_of_week': self.day_of_week
        }


@dataclass
class RLAction:
    """Action representation for RL agent."""
    # Parameter adjustments
    position_size_multiplier: float  # 0.5, 1.0, 1.5
    risk_per_trade: float  # 0.01, 0.02, 0.03
    stop_loss_multiplier: float  # 0.8, 1.0, 1.2
    take_profit_multiplier: float  # 0.8, 1.0, 1.2
    
    def to_tuple(self) -> Tuple:
        """Convert to tuple for use as dictionary key."""
        return (
            self.position_size_multiplier,
            self.risk_per_trade,
            self.stop_loss_multiplier,
            self.take_profit_multiplier
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'position_size_multiplier': self.position_size_multiplier,
            'risk_per_trade': self.risk_per_trade,
            'stop_loss_multiplier': self.stop_loss_multiplier,
            'take_profit_multiplier': self.take_profit_multiplier
        }


class QLearningAgent:
    """
    Q-Learning agent for parameter tuning.
    
    Uses argmax for action selection (exploitation) with epsilon-greedy exploration.
    Learns optimal parameter adjustments based on trading outcomes.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Q-Learning agent.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("Cthulu.rl_qlearning")
        self.config = config or {}
        
        # Q-table: state -> action -> Q-value
        self.q_table = defaultdict(lambda: defaultdict(float))
        
        # Hyperparameters
        self.learning_rate = self.config.get('learning_rate', 0.1)
        self.discount_factor = self.config.get('discount_factor', 0.95)
        self.epsilon = self.config.get('epsilon', 0.1)  # Exploration rate
        self.epsilon_decay = self.config.get('epsilon_decay', 0.995)
        self.epsilon_min = self.config.get('epsilon_min', 0.01)
        
        # Action space (discrete actions)
        self.action_space = self._build_action_space()
        
        # Experience tracking
        self.total_steps = 0
        self.total_reward = 0.0
        
        self.logger.info(
            f"QLearningAgent initialized with {len(self.action_space)} actions"
        )
    
    def _build_action_space(self) -> List[RLAction]:
        """Build discrete action space."""
        actions = []
        
        for pos_mult in [0.5, 1.0, 1.5]:
            for risk in [0.01, 0.02, 0.03]:
                for sl_mult in [0.8, 1.0, 1.2]:
                    for tp_mult in [0.8, 1.0, 1.2]:
                        action = RLAction(
                            position_size_multiplier=pos_mult,
                            risk_per_trade=risk,
                            stop_loss_multiplier=sl_mult,
                            take_profit_multiplier=tp_mult
                        )
                        actions.append(action)
        
        return actions
    
    def select_action(
        self,
        state: RLState,
        mode: str = 'epsilon_greedy'
    ) -> RLAction:
        """
        Select action using argmax Q-values with exploration.
        
        Args:
            state: Current state
            mode: Selection mode ('epsilon_greedy', 'greedy', 'random')
            
        Returns:
            Selected action
        """
        state_key = state.to_tuple()
        
        if mode == 'random':
            # Random exploration
            action = np.random.choice(self.action_space)
            self.logger.debug("Selected random action")
            return action
        
        elif mode == 'greedy':
            # Pure exploitation (argmax)
            return self._argmax_action(state_key)
        
        else:  # epsilon_greedy
            # Epsilon-greedy: explore with probability epsilon
            if np.random.random() < self.epsilon:
                # Explore
                action = np.random.choice(self.action_space)
                self.logger.debug(f"Exploring (ε={self.epsilon:.3f})")
                return action
            else:
                # Exploit (argmax)
                return self._argmax_action(state_key)
    
    def _argmax_action(self, state_key: Tuple) -> RLAction:
        """
        Select action with highest Q-value (argmax).
        
        Args:
            state_key: State tuple key
            
        Returns:
            Action with highest Q-value
        """
        # Get Q-values for all actions in this state
        q_values = []
        for action in self.action_space:
            action_key = action.to_tuple()
            q_value = self.q_table[state_key][action_key]
            q_values.append((action, q_value))
        
        # Argmax: select action with highest Q-value
        best_action = max(q_values, key=lambda x: x[1])[0]
        
        self.logger.debug(
            f"Argmax selected action with Q={max(q_values, key=lambda x: x[1])[1]:.3f}"
        )
        
        return best_action
    
    def update(
        self,
        state: RLState,
        action: RLAction,
        reward: float,
        next_state: RLState,
        done: bool = False
    ):
        """
        Update Q-value using Q-learning update rule.
        
        Q(s,a) ← Q(s,a) + α[r + γ max_a' Q(s',a') - Q(s,a)]
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
        """
        state_key = state.to_tuple()
        action_key = action.to_tuple()
        next_state_key = next_state.to_tuple()
        
        # Current Q-value
        current_q = self.q_table[state_key][action_key]
        
        if done:
            # Terminal state
            target = reward
        else:
            # Get max Q-value for next state (argmax)
            next_q_values = [
                self.q_table[next_state_key][a.to_tuple()]
                for a in self.action_space
            ]
            max_next_q = max(next_q_values) if next_q_values else 0.0
            
            # Q-learning target
            target = reward + self.discount_factor * max_next_q
        
        # Update Q-value
        self.q_table[state_key][action_key] += self.learning_rate * (target - current_q)
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Track
        self.total_steps += 1
        self.total_reward += reward
        
        self.logger.debug(
            f"Q-update: Q={current_q:.3f} → {self.q_table[state_key][action_key]:.3f}, "
            f"reward={reward:.3f}"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            'total_steps': self.total_steps,
            'total_reward': self.total_reward,
            'avg_reward': self.total_reward / max(1, self.total_steps),
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table),
            'action_space_size': len(self.action_space)
        }
    
    def save_q_table(self, filepath: str):
        """Save Q-table to disk."""
        # Convert Q-table to serializable format
        q_table_serializable = {}
        for state_key, actions in self.q_table.items():
            state_str = json.dumps(state_key)
            q_table_serializable[state_str] = {}
            for action_key, q_value in actions.items():
                action_str = json.dumps(action_key)
                q_table_serializable[state_str][action_str] = q_value
        
        data = {
            'q_table': q_table_serializable,
            'statistics': self.get_statistics(),
            'hyperparameters': {
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor,
                'epsilon': self.epsilon
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved Q-table to {filepath}")
    
    def load_q_table(self, filepath: str):
        """Load Q-table from disk."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Restore Q-table
        q_table_loaded = data['q_table']
        self.q_table = defaultdict(lambda: defaultdict(float))
        
        for state_str, actions in q_table_loaded.items():
            state_key = tuple(json.loads(state_str))
            for action_str, q_value in actions.items():
                action_key = tuple(json.loads(action_str))
                self.q_table[state_key][action_key] = q_value
        
        # Restore statistics
        if 'statistics' in data:
            stats = data['statistics']
            self.total_steps = stats.get('total_steps', 0)
            self.total_reward = stats.get('total_reward', 0.0)
        
        # Restore hyperparameters
        if 'hyperparameters' in data:
            hyper = data['hyperparameters']
            self.epsilon = hyper.get('epsilon', self.epsilon)
        
        self.logger.info(f"Loaded Q-table from {filepath}")


class PolicyGradientAgent:
    """
    Policy Gradient agent using softmax policy.
    
    Uses softmax over action preferences for smooth exploration.
    Learns directly from rewards without Q-values.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Policy Gradient agent.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("Cthulu.rl_policy_gradient")
        self.config = config or {}
        
        # Policy network: state -> action preferences
        self.policy_table = defaultdict(lambda: defaultdict(float))
        
        # Hyperparameters
        self.learning_rate = self.config.get('learning_rate', 0.01)
        self.temperature = self.config.get('temperature', 1.0)
        
        # Action space
        self.action_space = self._build_action_space()
        
        # Episode buffer
        self.episode_buffer = []
        
        self.total_episodes = 0
        self.total_reward = 0.0
        
        self.logger.info("PolicyGradientAgent initialized")
    
    def _build_action_space(self) -> List[RLAction]:
        """Build discrete action space."""
        actions = []
        
        for pos_mult in [0.5, 1.0, 1.5]:
            for risk in [0.01, 0.02, 0.03]:
                for sl_mult in [0.8, 1.0, 1.2]:
                    for tp_mult in [0.8, 1.0, 1.2]:
                        action = RLAction(
                            position_size_multiplier=pos_mult,
                            risk_per_trade=risk,
                            stop_loss_multiplier=sl_mult,
                            take_profit_multiplier=tp_mult
                        )
                        actions.append(action)
        
        return actions
    
    def softmax_policy(self, state: RLState) -> np.ndarray:
        """
        Compute softmax policy over actions.
        
        π(a|s) = exp(θ(s,a) / τ) / Σ exp(θ(s,a') / τ)
        
        Args:
            state: Current state
            
        Returns:
            Probability distribution over actions
        """
        state_key = state.to_tuple()
        
        # Get action preferences
        preferences = []
        for action in self.action_space:
            action_key = action.to_tuple()
            pref = self.policy_table[state_key][action_key]
            preferences.append(pref)
        
        preferences = np.array(preferences)
        
        # Softmax with temperature
        exp_prefs = np.exp(preferences / self.temperature)
        probabilities = exp_prefs / np.sum(exp_prefs)
        
        return probabilities
    
    def select_action(self, state: RLState) -> RLAction:
        """
        Sample action from softmax policy.
        
        Args:
            state: Current state
            
        Returns:
            Sampled action
        """
        probabilities = self.softmax_policy(state)
        
        # Sample action
        action_idx = np.random.choice(len(self.action_space), p=probabilities)
        action = self.action_space[action_idx]
        
        self.logger.debug(
            f"Softmax selected action {action_idx} with p={probabilities[action_idx]:.3f}"
        )
        
        return action
    
    def store_transition(self, state: RLState, action: RLAction, reward: float):
        """Store transition in episode buffer."""
        self.episode_buffer.append((state, action, reward))
    
    def update_policy(self):
        """
        Update policy using REINFORCE algorithm.
        
        Gradient: ∇J = E[Σ G_t ∇ log π(a_t|s_t)]
        """
        if not self.episode_buffer:
            return
        
        # Compute returns (cumulative discounted rewards)
        returns = []
        G = 0.0
        for _, _, reward in reversed(self.episode_buffer):
            G = reward + 0.99 * G
            returns.insert(0, G)
        
        # Normalize returns
        returns = np.array(returns)
        if len(returns) > 1:
            returns = (returns - np.mean(returns)) / (np.std(returns) + 1e-8)
        
        # Update policy
        for (state, action, _), G_t in zip(self.episode_buffer, returns):
            state_key = state.to_tuple()
            action_key = action.to_tuple()
            
            # Get softmax probabilities
            probs = self.softmax_policy(state)
            action_idx = self.action_space.index(action)
            
            # Policy gradient update
            # ∇ log π(a|s) = (1 - π(a|s)) for selected action
            grad_log_pi = 1.0 - probs[action_idx]
            
            # Update preference
            self.policy_table[state_key][action_key] += \
                self.learning_rate * G_t * grad_log_pi
        
        # Track
        total_reward = sum(r for _, _, r in self.episode_buffer)
        self.total_episodes += 1
        self.total_reward += total_reward
        
        # Clear buffer
        self.episode_buffer = []
        
        self.logger.info(f"Policy updated: episode_reward={total_reward:.2f}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            'total_episodes': self.total_episodes,
            'total_reward': self.total_reward,
            'avg_reward': self.total_reward / max(1, self.total_episodes),
            'temperature': self.temperature,
            'policy_table_size': len(self.policy_table)
        }


class AutoTuner:
    """
    Auto-tuning system for Cthulu parameters.
    
    Combines supervised learning (ML models) and reinforcement learning
    to continuously optimize trading parameters based on performance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize auto-tuner.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("Cthulu.autotuner")
        self.config = config or {}
        
        # Initialize agents
        self.q_agent = QLearningAgent(config.get('q_learning', {}))
        self.policy_agent = PolicyGradientAgent(config.get('policy_gradient', {}))
        
        # Current mode
        self.mode = self.config.get('mode', 'supervised')  # 'supervised', 'rl_q', 'rl_pg'
        
        # Performance tracking
        self.tuning_history = deque(maxlen=1000)
        
        self.logger.info(f"AutoTuner initialized in {self.mode} mode")
    
    def suggest_parameters(
        self,
        current_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Suggest parameter adjustments based on current state.
        
        Args:
            current_state: Current trading state
            
        Returns:
            Dictionary of parameter adjustments
        """
        # Convert to RL state
        rl_state = RLState(
            volatility_regime=current_state.get('volatility_regime', 'medium'),
            trend_regime=current_state.get('trend_regime', 'ranging'),
            recent_win_rate=current_state.get('recent_win_rate', 0.5),
            current_drawdown=current_state.get('current_drawdown', 0.0),
            hour_of_day=datetime.now().hour,
            day_of_week=datetime.now().weekday()
        )
        
        if self.mode == 'rl_q':
            # Use Q-learning agent
            action = self.q_agent.select_action(rl_state, mode='epsilon_greedy')
        elif self.mode == 'rl_pg':
            # Use policy gradient agent
            action = self.policy_agent.select_action(rl_state)
        else:
            # Default: no adjustment
            action = RLAction(
                position_size_multiplier=1.0,
                risk_per_trade=0.02,
                stop_loss_multiplier=1.0,
                take_profit_multiplier=1.0
            )
        
        return action.to_dict()
    
    def update_from_outcome(
        self,
        state: Dict[str, Any],
        action: Dict[str, float],
        reward: float,
        next_state: Dict[str, Any]
    ):
        """
        Update agents based on trading outcome.
        
        Args:
            state: State before action
            action: Action taken
            reward: Reward received (e.g., P&L)
            next_state: State after action
        """
        # Convert to RL format
        rl_state = RLState(
            volatility_regime=state.get('volatility_regime', 'medium'),
            trend_regime=state.get('trend_regime', 'ranging'),
            recent_win_rate=state.get('recent_win_rate', 0.5),
            current_drawdown=state.get('current_drawdown', 0.0),
            hour_of_day=datetime.now().hour,
            day_of_week=datetime.now().weekday()
        )
        
        rl_next_state = RLState(
            volatility_regime=next_state.get('volatility_regime', 'medium'),
            trend_regime=next_state.get('trend_regime', 'ranging'),
            recent_win_rate=next_state.get('recent_win_rate', 0.5),
            current_drawdown=next_state.get('current_drawdown', 0.0),
            hour_of_day=datetime.now().hour,
            day_of_week=datetime.now().weekday()
        )
        
        rl_action = RLAction(
            position_size_multiplier=action.get('position_size_multiplier', 1.0),
            risk_per_trade=action.get('risk_per_trade', 0.02),
            stop_loss_multiplier=action.get('stop_loss_multiplier', 1.0),
            take_profit_multiplier=action.get('take_profit_multiplier', 1.0)
        )
        
        # Update agents
        if self.mode == 'rl_q':
            self.q_agent.update(rl_state, rl_action, reward, rl_next_state)
        elif self.mode == 'rl_pg':
            self.policy_agent.store_transition(rl_state, rl_action, reward)
        
        # Track
        self.tuning_history.append({
            'timestamp': datetime.now().isoformat(),
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state
        })
    
    def finalize_episode(self):
        """Finalize episode for policy gradient agent."""
        if self.mode == 'rl_pg':
            self.policy_agent.update_policy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tuning statistics."""
        return {
            'mode': self.mode,
            'q_learning': self.q_agent.get_statistics(),
            'policy_gradient': self.policy_agent.get_statistics(),
            'tuning_history_size': len(self.tuning_history)
        }
