"""
Bootstrap Module

Handles system initialization including:
- Configuration loading and validation
- Component initialization (connectors, managers, databases)
- Dependency injection setup
- Logging and monitoring setup

Extracted from __main__.py for better modularity and testability.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from herald.connector.mt5_connector import MT5Connector, ConnectionConfig
from herald.data.layer import DataLayer
from herald.risk.evaluator import RiskEvaluator, RiskLimits
from herald.execution.engine import ExecutionEngine
from herald.position.tracker import PositionTracker
from herald.position.lifecycle import PositionLifecycle
from herald.position.adoption import TradeAdoptionManager, TradeAdoptionPolicy
from herald.persistence.database import Database
from herald.observability.metrics import MetricsCollector
from config_schema import Config
from config.mindsets import apply_mindset


@dataclass
class SystemComponents:
    """Container for all initialized system components."""
    
    # Core components
    config: Dict[str, Any]
    connector: MT5Connector
    data_layer: DataLayer
    risk_manager: RiskEvaluator
    execution_engine: ExecutionEngine
    position_tracker: PositionTracker
    position_manager: Optional[Any]
    position_lifecycle: PositionLifecycle
    trade_adoption_manager: TradeAdoptionManager
    exit_coordinator: PositionLifecycle
    database: Database
    metrics: MetricsCollector
    
    # Strategy and indicators (loaded separately)
    strategy: Any = None
    indicators: list = None
    exit_strategies: list = None
    trade_adoption_policy: Optional[Any] = None
    
    # Optional components
    ml_collector: Any = None
    advisory_manager: Any = None
    monitor: Any = None
    exporter: Any = None


class HeraldBootstrap:
    """Handles Herald system initialization."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize bootstrap handler.
        
        Args:
            logger: Logger instance (will be created if not provided)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.components = None
    
    def load_configuration(self, config_path: str, mindset: Optional[str] = None,
                          symbol_override: Optional[str] = None) -> Dict[str, Any]:
        """Load and validate configuration.
        
        Args:
            config_path: Path to configuration file
            mindset: Optional mindset to apply (aggressive, balanced, conservative, ultra_aggressive)
            symbol_override: Optional symbol to override configuration
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            Exception: If configuration loading or validation fails
        """
        try:
            cfg = Config.load(config_path)
            self.logger.info(f"Configuration loaded from {config_path}")
            
            # Convert to dict (Pydantic v2 compatibility)
            config = cfg.model_dump() if hasattr(cfg, 'model_dump') else cfg.dict()
            
            # Apply mindset if specified
            if mindset:
                config = apply_mindset(config, mindset)
                self.logger.info(f"Applied '{mindset}' trading mindset")
                self.logger.info(
                    f"  Risk: position_size_pct={config['risk'].get('position_size_pct', 2.0)}%, "
                    f"max_daily_loss=${config['risk'].get('max_daily_loss', 50)}"
                )
            
            # Symbol override from CLI
            if symbol_override:
                config['trading']['symbol'] = symbol_override
                self.logger.info(f"Overriding trading symbol: {symbol_override}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def initialize_connector(self, config: Dict[str, Any]) -> MT5Connector:
        """Initialize MT5 connector.
        
        Args:
            config: System configuration
            
        Returns:
            Initialized MT5Connector instance
        """
        self.logger.info("Initializing MT5 connector...")
        connection_config = ConnectionConfig(**config['mt5'])
        connector = MT5Connector(connection_config)
        return connector
    
    def initialize_data_layer(self, config: Dict[str, Any]) -> DataLayer:
        """Initialize data layer.
        
        Args:
            config: System configuration
            
        Returns:
            Initialized DataLayer instance
        """
        self.logger.info("Initializing data layer...")
        cache_enabled = config.get('cache_enabled', True)
        data_layer = DataLayer(cache_enabled=cache_enabled)
        return data_layer
    
    def initialize_risk_manager(self, config: Dict[str, Any]) -> RiskEvaluator:
        """Initialize risk evaluator.
        
        Args:
            config: System configuration
            
        Returns:
            Initialized RiskEvaluator instance
        """
        self.logger.info("Initializing risk evaluator...")
        risk_config = config.get('risk', {})
        
        # Build RiskLimits with defaults
        risk_limits = RiskLimits(
            max_position_size_percent=risk_config.get('max_position_size_percent', 2.0),
            max_total_exposure_percent=risk_config.get('max_total_exposure_percent', 10.0),
            max_daily_loss=risk_config.get('max_daily_loss', 500.0),
            max_positions_per_symbol=risk_config.get('max_positions_per_symbol', 3),
            min_risk_reward_ratio=risk_config.get('min_risk_reward_ratio', 1.5),
            max_spread_points=risk_config.get('max_spread_points', 10.0),
            min_confidence=risk_config.get('min_confidence', 0.0),
            emergency_shutdown_enabled=risk_config.get('emergency_shutdown_enabled', True)
        )
        
        return risk_limits
    
    def initialize_execution_engine(self, connector: MT5Connector, config: Dict[str, Any],
                                   ml_collector: Any = None) -> ExecutionEngine:
        """Initialize execution engine.
        
        Args:
            connector: MT5 connector instance
            config: System configuration
            ml_collector: Optional ML data collector
            
        Returns:
            Initialized ExecutionEngine instance
        """
        self.logger.info("Initializing execution engine...")
        risk_config = config.get('risk', {})
        execution_engine = ExecutionEngine(
            connector,
            risk_config=risk_config,
            ml_collector=ml_collector
        )
        return execution_engine
    
    def initialize_position_tracker(self, connector: MT5Connector) -> PositionTracker:
        """Initialize position tracker.
        
        Args:
            connector: MT5 connector instance
            
        Returns:
            Initialized PositionTracker instance
        """
        self.logger.info("Initializing position tracker...")
        position_tracker = PositionTracker()
        return position_tracker

    def initialize_position_manager(self, connector: MT5Connector, execution_engine: ExecutionEngine) -> 'PositionManager':
        """Initialize a lightweight PositionManager for higher-level monitoring.
        
        This manager is separate from the low-level PositionTracker and provides
        additional monitoring and convenience APIs used by the trading loop.
        """
        try:
            from herald.position.manager import PositionManager
            self.logger.info("Initializing position manager...")
            pm = PositionManager(connector=connector, execution_engine=execution_engine)
            self.logger.info('PositionManager initialized')
            return pm
        except Exception as e:
            self.logger.exception('PositionManager initialization failed; continuing without it')
            return None

    def initialize_strategy(self, config: Dict[str, Any]) -> Optional[Any]:
        """Initialize trading strategy from configuration."""
        self.logger.info("Initializing strategy...")
        try:
            from core.strategy_factory import load_strategy
            strat_cfg = config.get('strategy', {}) if isinstance(config, dict) else {}
            strategy = load_strategy(strat_cfg)
            self.logger.info(f"Strategy initialized: {strategy.__class__.__name__}")
            return strategy
        except Exception as e:
            self.logger.exception(f"Failed to initialize strategy: {e}")
            return None
    
    def initialize_position_lifecycle(self, connector: MT5Connector,
                                      execution_engine: ExecutionEngine,
                                      position_tracker: PositionTracker,
                                      database: Database) -> PositionLifecycle:
        """Initialize position lifecycle manager.
        
        Args:
            connector: MT5 connector instance
            execution_engine: Execution engine instance
            position_tracker: PositionTracker instance
            database: Database instance
            
        Returns:
            Initialized PositionLifecycle instance
        """
        self.logger.info("Initializing position lifecycle...")
        position_lifecycle = PositionLifecycle(connector, execution_engine, position_tracker, database)
        return position_lifecycle
    
    def initialize_trade_adoption_manager(self, connector: MT5Connector, position_tracker: PositionTracker,
                                          position_lifecycle: PositionLifecycle,
                                          config: Dict[str, Any]) -> TradeAdoptionManager:
        """Initialize trade adoption manager for external trade adoption.
        
        Args:
            position_tracker: Position tracker instance
            position_lifecycle: Position lifecycle instance
            config: System configuration
            
        Returns:
            Initialized TradeAdoptionManager instance
        """
        trade_adoption_config = config.get('orphan_trades', {})
        trade_adoption_policy = TradeAdoptionPolicy(
            enabled=trade_adoption_config.get('enabled', False),
            allowed_symbols=trade_adoption_config.get('adopt_symbols') or None,
            blocked_symbols=trade_adoption_config.get('ignore_symbols', []),
            max_age_hours=trade_adoption_config.get('max_adoption_age_hours'),
            min_age_seconds=trade_adoption_config.get('min_age_seconds', 60),
            min_volume=trade_adoption_config.get('min_volume'),
            max_volume=trade_adoption_config.get('max_volume'),
            excluded_magic_numbers=set(trade_adoption_config.get('excluded_magic_numbers', [])),
            apply_emergency_sl=trade_adoption_config.get('apply_emergency_sl', True),
            emergency_sl_points=trade_adoption_config.get('emergency_sl_points', 100),
            apply_emergency_tp=trade_adoption_config.get('apply_emergency_tp', False),
            emergency_tp_points=trade_adoption_config.get('emergency_tp_points', 100)
        )
        
        trade_adoption_manager = TradeAdoptionManager(
            connector,
            position_tracker,
            position_lifecycle,
            trade_adoption_policy
        )
        
        if trade_adoption_policy.enabled:
            self.logger.info(
                f"External trade adoption ENABLED (log_only: {trade_adoption_policy.log_only})"
            )
        else:
            self.logger.info("External trade adoption disabled")
        
        return trade_adoption_manager
    
    def initialize_database(self, config: Dict[str, Any]) -> Database:
        """Initialize database.
        
        Args:
            config: System configuration
            
        Returns:
            Initialized Database instance
        """
        self.logger.info("Initializing database...")
        db_path = config.get('database', {}).get('path', 'herald.db')
        database = Database(db_path)
        return database
    
    def initialize_metrics(self, database: Database) -> MetricsCollector:
        """Initialize metrics collector.
        
        Args:
            database: Database instance
            
        Returns:
            Initialized MetricsCollector instance
        """
        self.logger.info("Initializing metrics collector...")
        metrics = MetricsCollector(database=database)
        return metrics
    
    def initialize_ml_collector(self, config: Dict[str, Any], args: Any) -> Optional[Any]:
        """Initialize ML data collector (optional).
        
        Args:
            config: System configuration
            args: Command-line arguments
            
        Returns:
            MLDataCollector instance or None if disabled
        """
        ml_collector = None
        try:
            ml_config = config.get('ml', {}) if isinstance(config, dict) else {}
            ml_enabled = ml_config.get('enabled', True)
            
            # CLI overrides config when provided
            if hasattr(args, 'enable_ml') and args.enable_ml is not None:
                ml_enabled = args.enable_ml
            
            if ml_enabled:
                from herald.ML_RL.instrumentation import MLDataCollector
                ml_prefix = ml_config.get('prefix', 'events')
                ml_collector = MLDataCollector(prefix=ml_prefix)
                self.logger.info('MLDataCollector initialized')
            else:
                self.logger.info('ML instrumentation disabled via config/CLI')
        except Exception:
            self.logger.exception('Failed to initialize MLDataCollector; continuing without it')
        
        return ml_collector
    
    def initialize_advisory_manager(self, config: Dict[str, Any],
                                    execution_engine: ExecutionEngine,
                                    ml_collector: Any) -> Optional[Any]:
        """Initialize advisory manager (optional).
        
        Args:
            config: System configuration
            execution_engine: Execution engine instance
            ml_collector: ML data collector instance
            
        Returns:
            AdvisoryManager instance or None if disabled
        """
        advisory_manager = None
        try:
            from herald.advisory.manager import AdvisoryManager
            advisory_cfg = config.get('advisory', {}) if isinstance(config, dict) else {}
            advisory_manager = AdvisoryManager(advisory_cfg, execution_engine, ml_collector)
            if advisory_manager.enabled:
                self.logger.info(f"AdvisoryManager enabled (mode={advisory_manager.mode})")
        except Exception:
            self.logger.exception('Failed to initialize AdvisoryManager; continuing without it')
        
        return advisory_manager
    
    def initialize_prometheus_exporter(self, config: Dict[str, Any]) -> Optional[Any]:
        """Initialize Prometheus exporter (optional).
        
        Args:
            config: System configuration
            
        Returns:
            PrometheusExporter instance or None if disabled
        """
        exporter = None
        try:
            prom_cfg = config.get('observability', {}).get('prometheus', {})
            if prom_cfg.get('enabled', False):
                from herald.observability.prometheus import PrometheusExporter
                exporter = PrometheusExporter(prefix=prom_cfg.get('prefix', 'herald'))
                self.logger.info('Prometheus exporter initialized')
        except Exception:
            self.logger.exception('Failed to initialize Prometheus exporter; continuing without it')
        
        return exporter
    
    def initialize_trade_monitor(self, position_tracker: PositionTracker,
                                 position_lifecycle: PositionLifecycle,
                                 trade_adoption_manager: TradeAdoptionManager,
                                 config: Dict[str, Any],
                                 ml_collector: Any) -> Optional[Any]:
        """Initialize trade monitor (optional).
        
        Args:
            position_tracker: Position tracker instance
            position_lifecycle: Position lifecycle instance
            trade_adoption_manager: Trade adoption manager instance
            config: System configuration
            ml_collector: ML data collector instance
            
        Returns:
            TradeMonitor instance or None if initialization fails
        """
        monitor = None
        try:
            from herald.monitoring.trade_monitor import TradeMonitor
            poll_interval = config.get('monitor_poll_interval', 5.0)
            monitor = TradeMonitor(
                position_tracker,
                position_lifecycle,
                poll_interval=poll_interval,
                ml_collector=ml_collector
            )
            monitor.start()
            self.logger.info(f"TradeMonitor started (poll_interval={poll_interval}s)")
        except Exception:
            self.logger.exception('Failed to start TradeMonitor; continuing without it')
        
        return monitor
    
    def bootstrap(self, config_path: str, args: Any) -> SystemComponents:
        """Bootstrap the entire Herald system.
        
        Args:
            config_path: Path to configuration file
            args: Command-line arguments
            
        Returns:
            SystemComponents with all initialized components
            
        Raises:
            Exception: If critical initialization fails
        """
        # Load configuration
        config = self.load_configuration(
            config_path,
            mindset=getattr(args, 'mindset', None),
            symbol_override=getattr(args, 'symbol', None)
        )
        
        # Initialize core components
        connector = self.initialize_connector(config)
        data_layer = self.initialize_data_layer(config)
        # Compute risk limits configuration (create RiskEvaluator later when position tracker is available)
        risk_limits = self.initialize_risk_manager(config)
        
        # Initialize ML collector before execution engine
        ml_collector = self.initialize_ml_collector(config, args)
        
        # Initialize execution components
        execution_engine = self.initialize_execution_engine(connector, config, ml_collector)
        
        # Initialize persistence first (needed by lifecycle)
        database = self.initialize_database(config)
        # Wire telemetry helper to execution engine so provenance is persisted
        try:
            from herald.observability.telemetry import Telemetry
            telemetry = Telemetry(database)
            execution_engine.telemetry = telemetry
        except Exception:
            telemetry = None
            self.logger.debug('Telemetry helper unavailable; provenance will still be logged to file')
        
        # Initialize position management components
        position_tracker = self.initialize_position_tracker(connector)
        # Initialize higher-level position manager used by trading loop monitoring
        position_manager = self.initialize_position_manager(connector, execution_engine)
        # Now we can construct the risk evaluator with the connector and position tracker
        risk_manager = RiskEvaluator(connector, position_tracker, limits=risk_limits)
        self.logger.info('RiskEvaluator initialized with runtime dependencies')
        
        position_lifecycle = self.initialize_position_lifecycle(connector, execution_engine, position_tracker, database)
        trade_adoption_manager = self.initialize_trade_adoption_manager(connector, position_tracker, position_lifecycle, config)
        
        # Initialize strategy
        strategy = self.initialize_strategy(config)
        
        # Initialize metrics
        metrics = self.initialize_metrics(database)
        
        # Attach metrics to execution engine
        try:
            execution_engine.metrics = metrics
        except Exception:
            self.logger.debug('Failed to attach metrics to execution engine')        
        # Initialize optional components
        advisory_manager = self.initialize_advisory_manager(config, execution_engine, ml_collector)
        exporter = self.initialize_prometheus_exporter(config)
        monitor = self.initialize_trade_monitor(position_tracker, position_lifecycle, trade_adoption_manager, config, ml_collector)
        
        # Create components container
        components = SystemComponents(
            config=config,
            connector=connector,
            data_layer=data_layer,
            risk_manager=risk_manager,
            execution_engine=execution_engine,
            position_tracker=position_tracker,
            position_manager=position_manager,
            position_lifecycle=position_lifecycle,
            trade_adoption_manager=trade_adoption_manager,
            exit_coordinator=position_lifecycle,
            database=database,
            metrics=metrics,
            ml_collector=ml_collector,
            advisory_manager=advisory_manager,
            monitor=monitor,
            exporter=exporter,
            strategy=strategy
        )
        # Expose trade_adoption_policy for convenience
        try:
            components.trade_adoption_policy = trade_adoption_manager.policy
        except Exception:
            components.trade_adoption_policy = None
        
        self.components = components
        self.logger.info("System bootstrap complete")
        
        return components


def bootstrap_system(config_path: str, args: Any, logger: logging.Logger) -> SystemComponents:
    """Convenience function for bootstrapping the system.
    
    Args:
        config_path: Path to configuration file
        args: Command-line arguments
        logger: Logger instance
        
    Returns:
        SystemComponents with all initialized components
    """
    bootstrapper = HeraldBootstrap(logger=logger)
    return bootstrapper.bootstrap(config_path, args)
