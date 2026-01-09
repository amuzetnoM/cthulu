"""
Core Bootstrap Module - System Initialization
Cleanly initializes all system components with proper dependency injection.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SystemComponents:
    """Container for all system components with clear ownership."""
    # Core
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Connector
    mt5_connector: Any = None
    
    # Data
    data_layer: Any = None
    
    # Strategy
    strategy: Any = None
    strategy_selector: Any = None
    
    # Risk
    risk_evaluator: Any = None
    dynamic_sltp_manager: Any = None
    adaptive_drawdown_manager: Any = None
    
    # Position
    trade_manager: Any = None
    position_manager: Any = None
    lifecycle_manager: Any = None
    
    # Exit
    exit_coordinator: Any = None
    trailing_stop: Any = None
    
    # Execution
    execution_engine: Any = None
    
    # Cognition
    entry_confluence: Any = None
    regime_classifier: Any = None
    
    # Filters
    liquidity_filter: Any = None
    
    # Persistence
    database: Any = None
    
    # Monitoring
    metrics_collector: Any = None
    trade_monitor: Any = None


class CthuluBootstrap:
    """
    Clean system bootstrap with explicit initialization order.
    
    Initialization Order:
    1. Configuration
    2. MT5 Connector
    3. Data Layer
    4. Database/Persistence
    5. Risk Management
    6. Position Management
    7. Strategy Layer
    8. Cognition Layer
    9. Exit Strategies
    10. Execution Engine
    11. Monitoring
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.components = SystemComponents()
        self._initialized = False
        
    def bootstrap(self) -> SystemComponents:
        """Initialize all system components in proper order."""
        logger.info("="*80)
        logger.info("Cthulu Rule-Based Trading System v5.2.0")
        logger.info("="*80)
        
        # Phase 1: Configuration
        self._init_config()
        
        # Phase 2: Connector
        self._init_connector()
        
        # Phase 3: Data Layer
        self._init_data_layer()
        
        # Phase 4: Database
        self._init_database()
        
        # Phase 5: Risk Management
        self._init_risk()
        
        # Phase 6: Position Management
        self._init_position()
        
        # Phase 7: Strategy Layer
        self._init_strategy()
        
        # Phase 8: Cognition Layer
        self._init_cognition()
        
        # Phase 9: Exit Strategies
        self._init_exit()
        
        # Phase 10: Execution Engine
        self._init_execution()
        
        # Phase 11: Monitoring
        self._init_monitoring()
        
        # Wire up dependencies
        self._wire_dependencies()
        
        self._initialized = True
        logger.info("System bootstrap complete")
        
        return self.components
    
    def _init_config(self):
        """Load configuration from file."""
        import json
        logger.info("Loading configuration...")
        
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file) as f:
                self.components.config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
        else:
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            self.components.config = self._default_config()
    
    def _init_connector(self):
        """Initialize MT5 connector."""
        logger.info("Initializing MT5 connector...")
        from connector.mt5_connector import MT5Connector
        self.components.mt5_connector = MT5Connector(self.components.config)
        
    def _init_data_layer(self):
        """Initialize data layer."""
        logger.info("Initializing data layer...")
        from data.layer import DataLayer
        self.components.data_layer = DataLayer(
            connector=self.components.mt5_connector,
            config=self.components.config
        )
        
    def _init_database(self):
        """Initialize database persistence."""
        logger.info("Initializing database...")
        from persistence.database import Database
        db_name = self.components.config.get('database', {}).get('name', 'cthulu.db')
        self.components.database = Database(db_name)
        logger.info(f"Database initialized: {db_name}")
        
    def _init_risk(self):
        """Initialize risk management components."""
        logger.info("Initializing risk management...")
        
        from risk.evaluator import RiskEvaluator
        from risk.dynamic_sltp import DynamicSLTPManager
        from risk.adaptive_drawdown import AdaptiveDrawdownManager
        
        risk_config = self.components.config.get('risk', {})
        
        self.components.risk_evaluator = RiskEvaluator(
            config=risk_config,
            connector=self.components.mt5_connector
        )
        
        sltp_config = self.components.config.get('dynamic_sltp', {})
        self.components.dynamic_sltp_manager = DynamicSLTPManager(
            config=sltp_config,
            connector=self.components.mt5_connector
        )
        
        self.components.adaptive_drawdown_manager = AdaptiveDrawdownManager(
            config=self.components.config.get('adaptive_drawdown', {})
        )
        
    def _init_position(self):
        """Initialize position management."""
        logger.info("Initializing position management...")
        
        from position.trade_manager import TradeManager
        from position.manager import PositionManager
        from position.lifecycle import PositionLifecycle
        
        self.components.trade_manager = TradeManager(
            connector=self.components.mt5_connector,
            config=self.components.config
        )
        
        self.components.position_manager = PositionManager(
            connector=self.components.mt5_connector,
            config=self.components.config
        )
        
        adoption_config = self.components.config.get('adoption_policy', {})
        self.components.lifecycle_manager = PositionLifecycle(
            trade_manager=self.components.trade_manager,
            connector=self.components.mt5_connector,
            adoption_policy=adoption_config
        )
        
    def _init_strategy(self):
        """Initialize strategy layer."""
        logger.info("Initializing strategies...")
        
        from strategy.strategy_selector import StrategySelector
        
        strategy_config = self.components.config.get('strategy_selector', {})
        self.components.strategy_selector = StrategySelector(
            config=strategy_config,
            data_layer=self.components.data_layer
        )
        self.components.strategy = self.components.strategy_selector
        
    def _init_cognition(self):
        """Initialize cognition layer (rule-based analysis)."""
        logger.info("Initializing cognition layer...")
        
        from cognition.entry_confluence import EntryConfluenceFilter
        from cognition.regime_classifier import RegimeClassifier
        
        confluence_config = self.components.config.get('entry_confluence', {})
        self.components.entry_confluence = EntryConfluenceFilter(
            config=confluence_config
        )
        
        self.components.regime_classifier = RegimeClassifier()
        
    def _init_exit(self):
        """Initialize exit strategies."""
        logger.info("Initializing exit strategies...")
        
        from exit.coordinator import ExitCoordinator
        from exit.trailing_stop import TrailingStop
        
        exit_config = self.components.config.get('exit_strategies', {})
        
        self.components.trailing_stop = TrailingStop(
            config=exit_config.get('trailing_stop', {})
        )
        
        self.components.exit_coordinator = ExitCoordinator(
            config=exit_config,
            connector=self.components.mt5_connector
        )
        
    def _init_execution(self):
        """Initialize execution engine."""
        logger.info("Initializing execution engine...")
        
        from execution.engine import ExecutionEngine
        
        self.components.execution_engine = ExecutionEngine(
            connector=self.components.mt5_connector,
            risk_evaluator=self.components.risk_evaluator,
            config=self.components.config
        )
        
    def _init_monitoring(self):
        """Initialize monitoring components."""
        logger.info("Initializing monitoring...")
        
        from monitoring.metrics_collector import MetricsCollector
        from monitoring.trade_monitor import TradeMonitor
        
        self.components.metrics_collector = MetricsCollector(
            database=self.components.database,
            config=self.components.config
        )
        
        self.components.trade_monitor = TradeMonitor(
            connector=self.components.mt5_connector,
            trade_manager=self.components.trade_manager
        )
        
    def _wire_dependencies(self):
        """Wire up runtime dependencies between components."""
        logger.info("Wiring component dependencies...")
        
        # Risk evaluator needs position manager for exposure checks
        if hasattr(self.components.risk_evaluator, 'set_position_manager'):
            self.components.risk_evaluator.set_position_manager(
                self.components.position_manager
            )
        
        # Dynamic SLTP needs trade manager for position tracking
        if hasattr(self.components.dynamic_sltp_manager, 'set_trade_manager'):
            self.components.dynamic_sltp_manager.set_trade_manager(
                self.components.trade_manager
            )
            
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "symbol": "GOLDm#",
            "timeframe": "M5",
            "mode": "live",
            "risk": {
                "max_positions": 3,
                "max_positions_per_symbol": 3,
                "max_risk_per_trade": 0.02,
                "min_balance_threshold": 10.0
            },
            "dynamic_sltp": {
                "base_sl_atr": 2.0,
                "base_tp_atr": 4.0,
                "breakeven_pips": 10,
                "trailing_trigger_pips": 20,
                "trailing_lock_pct": 0.5
            },
            "entry_confluence": {
                "enabled": True,
                "min_score_to_enter": 50,
                "min_score_for_full_size": 75
            },
            "adoption_policy": {
                "enabled": True,
                "min_trade_age_seconds": 0,
                "apply_sltp_on_adopt": True
            },
            "strategy_selector": {
                "enabled_strategies": [
                    "sma_crossover", "ema_crossover", "momentum_breakout",
                    "scalping", "mean_reversion", "trend_following", "rsi_reversal"
                ]
            }
        }
