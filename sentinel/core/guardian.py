"""
SENTINEL GUARDIAN - Core Watchdog System
=========================================
Independent process that monitors Cthulu and MT5 for:
- Crashes and automatic recovery
- Disconnections and reconnection attempts
- Algo trading state monitoring and auto-re-enable
- System health metrics collection
- Emergency shutdown protocols

This runs OUTSIDE of Cthulu to ensure it survives any Cthulu crash.
"""

import os
import sys
import time
import json
import signal
import logging
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any, List, Callable
import psutil

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SENTINEL] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"sentinel_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SENTINEL")


class SystemState(Enum):
    """Overall system state"""
    HEALTHY = auto()
    DEGRADED = auto()
    CRITICAL = auto()
    RECOVERING = auto()
    OFFLINE = auto()


class CthhuluState(Enum):
    """Cthulu process state"""
    RUNNING = auto()
    STARTING = auto()
    STOPPED = auto()
    CRASHED = auto()
    UNRESPONSIVE = auto()


class MT5State(Enum):
    """MetaTrader 5 state"""
    CONNECTED = auto()
    DISCONNECTED = auto()
    ALGO_ENABLED = auto()
    ALGO_DISABLED = auto()
    NOT_RUNNING = auto()


@dataclass
class HealthMetrics:
    """System health snapshot"""
    timestamp: datetime = field(default_factory=datetime.now)
    cthulu_state: CthhuluState = CthhuluState.STOPPED
    mt5_state: MT5State = MT5State.NOT_RUNNING
    system_state: SystemState = SystemState.OFFLINE
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    cthulu_pid: Optional[int] = None
    mt5_pid: Optional[int] = None
    uptime_seconds: float = 0.0
    crash_count: int = 0
    last_crash: Optional[datetime] = None
    recovery_attempts: int = 0
    last_heartbeat: Optional[datetime] = None
    error_log: List[str] = field(default_factory=list)


@dataclass
class RecoveryConfig:
    """Recovery behavior configuration"""
    max_crash_recovery_attempts: int = 5
    recovery_cooldown_seconds: int = 30
    heartbeat_timeout_seconds: int = 120
    auto_restart_cthulu: bool = True
    auto_enable_algo: bool = True
    emergency_stop_on_repeated_crashes: bool = True
    crash_threshold_for_emergency: int = 5
    crash_window_minutes: int = 10
    mt5_path: str = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    cthulu_path: str = r"C:\workspace\cthulu"
    cthulu_config: str = "config.json"


class SentinelGuardian:
    """
    The Sentinel Guardian - Watches over Cthulu and MT5
    
    Runs as an independent process, completely separate from Cthulu.
    Survives Cthulu crashes and orchestrates recovery.
    """
    
    def __init__(self, config: Optional[RecoveryConfig] = None):
        self.config = config or RecoveryConfig()
        self.metrics = HealthMetrics()
        self.running = False
        self.start_time: Optional[datetime] = None
        self._crash_timestamps: List[datetime] = []
        self._callbacks: Dict[str, List[Callable]] = {
            "on_crash": [],
            "on_recovery": [],
            "on_state_change": [],
            "on_emergency": []
        }
        self._lock = threading.Lock()
        
        # MT5 Python integration
        self._mt5_module = None
        self._load_mt5_module()
        
        logger.info("🛡️ SENTINEL Guardian initialized")
    
    def _load_mt5_module(self):
        """Attempt to load MT5 Python module"""
        try:
            import MetaTrader5 as mt5
            self._mt5_module = mt5
            logger.info("✅ MT5 Python module loaded")
        except ImportError:
            logger.warning("⚠️ MT5 Python module not available - limited MT5 control")
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for events: on_crash, on_recovery, on_state_change, on_emergency"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _emit_event(self, event: str, *args, **kwargs):
        """Emit event to all registered callbacks"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")
    
    # ==================== Process Detection ====================
    
    def find_cthulu_process(self) -> Optional[psutil.Process]:
        """Find running Cthulu process"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', []) or []
                cmdline_str = ' '.join(cmdline).lower()
                if 'python' in proc.info['name'].lower():
                    if 'cthulu' in cmdline_str or '__main__.py' in cmdline_str:
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def find_mt5_process(self) -> Optional[psutil.Process]:
        """Find running MetaTrader 5 process"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'terminal64' in proc.info['name'].lower() or 'metatrader' in proc.info['name'].lower():
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    # ==================== Health Checks ====================
    
    def check_cthulu_health(self) -> CthhuluState:
        """Check Cthulu process health"""
        proc = self.find_cthulu_process()
        
        if proc is None:
            if self.metrics.cthulu_state == CthhuluState.RUNNING:
                # Was running, now not - potential crash
                return CthhuluState.CRASHED
            return CthhuluState.STOPPED
        
        try:
            # Check if process is responding
            cpu = proc.cpu_percent(interval=0.1)
            status = proc.status()
            
            if status == psutil.STATUS_ZOMBIE:
                return CthhuluState.CRASHED
            elif status == psutil.STATUS_STOPPED:
                return CthhuluState.UNRESPONSIVE
            
            self.metrics.cthulu_pid = proc.pid
            return CthhuluState.RUNNING
            
        except psutil.NoSuchProcess:
            return CthhuluState.CRASHED
        except Exception as e:
            logger.error(f"Error checking Cthulu health: {e}")
            return CthhuluState.UNRESPONSIVE
    
    def check_mt5_health(self) -> MT5State:
        """Check MT5 process and connection health"""
        proc = self.find_mt5_process()
        
        if proc is None:
            return MT5State.NOT_RUNNING
        
        self.metrics.mt5_pid = proc.pid
        
        # Try to check connection via MT5 Python API
        if self._mt5_module:
            try:
                if not self._mt5_module.initialize():
                    return MT5State.DISCONNECTED
                
                info = self._mt5_module.terminal_info()
                if info is None:
                    return MT5State.DISCONNECTED
                
                # Check algo trading state
                if hasattr(info, 'trade_allowed') and info.trade_allowed:
                    return MT5State.ALGO_ENABLED
                else:
                    return MT5State.ALGO_DISABLED
                    
            except Exception as e:
                logger.warning(f"MT5 API check failed: {e}")
                return MT5State.DISCONNECTED
        
        # Without API, assume connected if process exists
        return MT5State.CONNECTED
    
    def check_system_health(self) -> SystemState:
        """Determine overall system state"""
        cthulu = self.metrics.cthulu_state
        mt5 = self.metrics.mt5_state
        
        # Both healthy
        if cthulu == CthhuluState.RUNNING and mt5 == MT5State.ALGO_ENABLED:
            return SystemState.HEALTHY
        
        # Recovery in progress
        if self.metrics.recovery_attempts > 0:
            return SystemState.RECOVERING
        
        # Critical states
        if cthulu == CthhuluState.CRASHED:
            return SystemState.CRITICAL
        
        # Degraded states
        if cthulu == CthhuluState.UNRESPONSIVE or mt5 == MT5State.ALGO_DISABLED:
            return SystemState.DEGRADED
        
        # Everything offline
        if cthulu == CthhuluState.STOPPED and mt5 == MT5State.NOT_RUNNING:
            return SystemState.OFFLINE
        
        return SystemState.DEGRADED
    
    # ==================== Recovery Actions ====================
    
    def start_mt5(self) -> bool:
        """Start MetaTrader 5"""
        logger.info("🚀 Starting MetaTrader 5...")
        try:
            if self._mt5_module:
                if self._mt5_module.initialize():
                    logger.info("✅ MT5 initialized via Python API")
                    return True
            
            # Fallback: Start via subprocess
            if os.path.exists(self.config.mt5_path):
                subprocess.Popen([self.config.mt5_path], 
                               creationflags=subprocess.DETACHED_PROCESS)
                time.sleep(5)  # Wait for MT5 to start
                logger.info("✅ MT5 started via subprocess")
                return True
            else:
                logger.error(f"MT5 not found at: {self.config.mt5_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start MT5: {e}")
            return False
    
    def enable_algo_trading(self) -> bool:
        """Enable algo trading in MT5"""
        logger.info("🔧 Enabling algo trading...")
        
        if not self._mt5_module:
            logger.warning("Cannot enable algo - MT5 module not loaded")
            return False
        
        try:
            # Re-initialize to refresh state
            if not self._mt5_module.initialize():
                logger.error("Failed to initialize MT5 for algo enable")
                return False
            
            # The Python API cannot directly toggle algo trading
            # We can only check the state
            info = self._mt5_module.terminal_info()
            if info and hasattr(info, 'trade_allowed') and info.trade_allowed:
                logger.info("✅ Algo trading is enabled")
                return True
            else:
                logger.warning("⚠️ Algo trading is disabled - requires manual enable or AutoHotkey")
                # Could integrate AutoHotkey here for GUI automation
                return False
                
        except Exception as e:
            logger.error(f"Error enabling algo: {e}")
            return False
    
    def start_cthulu(self, config_file: Optional[str] = None) -> bool:
        """Start Cthulu trading system"""
        logger.info("🐙 Starting Cthulu...")
        
        config = config_file or self.config.cthulu_config
        cthulu_dir = Path(self.config.cthulu_path)
        
        if not cthulu_dir.exists():
            logger.error(f"Cthulu directory not found: {cthulu_dir}")
            return False
        
        try:
            # Start Cthulu as detached process
            cmd = [sys.executable, "-m", "cthulu", "--config", config, "--live"]
            
            proc = subprocess.Popen(
                cmd,
                cwd=str(cthulu_dir),
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(3)  # Wait for startup
            
            # Verify it started
            if self.find_cthulu_process():
                logger.info(f"✅ Cthulu started (PID: {proc.pid})")
                self.metrics.cthulu_pid = proc.pid
                return True
            else:
                logger.error("Cthulu failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Cthulu: {e}")
            return False
    
    def stop_cthulu(self) -> bool:
        """Gracefully stop Cthulu"""
        logger.info("🛑 Stopping Cthulu...")
        proc = self.find_cthulu_process()
        
        if proc is None:
            logger.info("Cthulu not running")
            return True
        
        try:
            # Send SIGTERM for graceful shutdown
            proc.terminate()
            proc.wait(timeout=10)
            logger.info("✅ Cthulu stopped gracefully")
            return True
        except psutil.TimeoutExpired:
            logger.warning("Cthulu not responding, forcing kill...")
            proc.kill()
            return True
        except Exception as e:
            logger.error(f"Error stopping Cthulu: {e}")
            return False
    
    def recover_from_crash(self) -> bool:
        """Execute crash recovery procedure"""
        logger.warning("🔥 CRASH RECOVERY INITIATED")
        
        with self._lock:
            self._crash_timestamps.append(datetime.now())
            self.metrics.crash_count += 1
            self.metrics.last_crash = datetime.now()
            self.metrics.recovery_attempts += 1
        
        # Check for repeated crashes (emergency condition)
        recent_crashes = [
            t for t in self._crash_timestamps 
            if datetime.now() - t < timedelta(minutes=self.config.crash_window_minutes)
        ]
        
        if len(recent_crashes) >= self.config.crash_threshold_for_emergency:
            logger.critical("🚨 EMERGENCY: Too many crashes in short window!")
            self._emit_event("on_emergency", "repeated_crashes", recent_crashes)
            
            if self.config.emergency_stop_on_repeated_crashes:
                logger.critical("⛔ Emergency stop - manual intervention required")
                self.metrics.error_log.append(
                    f"{datetime.now()}: EMERGENCY STOP - {len(recent_crashes)} crashes in "
                    f"{self.config.crash_window_minutes} minutes"
                )
                return False
        
        # Cooldown before recovery
        logger.info(f"⏳ Cooldown: {self.config.recovery_cooldown_seconds}s")
        time.sleep(self.config.recovery_cooldown_seconds)
        
        self._emit_event("on_crash", self.metrics)
        
        # Recovery sequence
        success = True
        
        # Step 1: Ensure MT5 is running
        if self.check_mt5_health() == MT5State.NOT_RUNNING:
            success = self.start_mt5() and success
            time.sleep(5)
        
        # Step 2: Enable algo if needed
        if self.config.auto_enable_algo:
            mt5_state = self.check_mt5_health()
            if mt5_state == MT5State.ALGO_DISABLED:
                self.enable_algo_trading()
        
        # Step 3: Restart Cthulu
        if self.config.auto_restart_cthulu:
            success = self.start_cthulu() and success
        
        if success:
            logger.info("✅ Recovery completed successfully")
            self.metrics.recovery_attempts = 0
            self._emit_event("on_recovery", self.metrics)
        else:
            logger.error("❌ Recovery failed")
        
        return success
    
    # ==================== Main Loop ====================
    
    def update_metrics(self):
        """Update all health metrics"""
        old_state = self.metrics.system_state
        
        self.metrics.timestamp = datetime.now()
        self.metrics.cthulu_state = self.check_cthulu_health()
        self.metrics.mt5_state = self.check_mt5_health()
        self.metrics.system_state = self.check_system_health()
        self.metrics.cpu_percent = psutil.cpu_percent()
        self.metrics.memory_percent = psutil.virtual_memory().percent
        
        if self.start_time:
            self.metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Emit state change event
        if old_state != self.metrics.system_state:
            logger.info(f"📊 State change: {old_state.name} → {self.metrics.system_state.name}")
            self._emit_event("on_state_change", old_state, self.metrics.system_state, self.metrics)
    
    def run(self, poll_interval: float = 5.0):
        """Main guardian loop"""
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🛡️  SENTINEL GUARDIAN ACTIVE")
        logger.info("=" * 60)
        logger.info(f"Poll interval: {poll_interval}s")
        logger.info(f"Auto restart: {self.config.auto_restart_cthulu}")
        logger.info(f"Auto algo enable: {self.config.auto_enable_algo}")
        logger.info("=" * 60)
        
        # Setup signal handlers for graceful shutdown
        def shutdown_handler(signum, frame):
            logger.info("🛑 Shutdown signal received")
            self.running = False
        
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        
        while self.running:
            try:
                self.update_metrics()
                
                # Log status periodically
                logger.debug(
                    f"Status: Cthulu={self.metrics.cthulu_state.name}, "
                    f"MT5={self.metrics.mt5_state.name}, "
                    f"System={self.metrics.system_state.name}"
                )
                
                # Handle crash detection
                if self.metrics.cthulu_state == CthhuluState.CRASHED:
                    if self.metrics.recovery_attempts < self.config.max_crash_recovery_attempts:
                        self.recover_from_crash()
                    else:
                        logger.critical("⛔ Max recovery attempts exceeded - stopping guardian")
                        self.running = False
                        break
                
                # Handle MT5 algo disabled
                if (self.config.auto_enable_algo and 
                    self.metrics.mt5_state == MT5State.ALGO_DISABLED):
                    logger.warning("⚠️ Algo trading disabled - attempting re-enable")
                    self.enable_algo_trading()
                
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Guardian loop error: {e}")
                time.sleep(poll_interval)
        
        logger.info("🛡️ SENTINEL Guardian shutting down")
    
    def get_status_dict(self) -> Dict[str, Any]:
        """Get current status as dictionary (for WebUI)"""
        return {
            "timestamp": self.metrics.timestamp.isoformat(),
            "system_state": self.metrics.system_state.name,
            "cthulu_state": self.metrics.cthulu_state.name,
            "cthulu_pid": self.metrics.cthulu_pid,
            "mt5_state": self.metrics.mt5_state.name,
            "mt5_pid": self.metrics.mt5_pid,
            "cpu_percent": self.metrics.cpu_percent,
            "memory_percent": self.metrics.memory_percent,
            "uptime_seconds": self.metrics.uptime_seconds,
            "crash_count": self.metrics.crash_count,
            "last_crash": self.metrics.last_crash.isoformat() if self.metrics.last_crash else None,
            "recovery_attempts": self.metrics.recovery_attempts,
            "error_log": self.metrics.error_log[-10:]  # Last 10 errors
        }


# ==================== CLI Entry Point ====================

def main():
    """CLI entry point for Sentinel"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SENTINEL - Cthulu Guardian System")
    parser.add_argument("--interval", type=float, default=5.0, help="Poll interval in seconds")
    parser.add_argument("--no-auto-restart", action="store_true", help="Disable auto-restart of Cthulu")
    parser.add_argument("--no-auto-algo", action="store_true", help="Disable auto-enable of algo trading")
    parser.add_argument("--config", type=str, help="Cthulu config file to use")
    parser.add_argument("--webui", action="store_true", help="Start WebUI server")
    parser.add_argument("--webui-port", type=int, default=8282, help="WebUI port")
    
    args = parser.parse_args()
    
    config = RecoveryConfig(
        auto_restart_cthulu=not args.no_auto_restart,
        auto_enable_algo=not args.no_auto_algo,
        cthulu_config=args.config or "config.json"
    )
    
    guardian = SentinelGuardian(config)
    
    if args.webui:
        # Start WebUI in separate thread
        from sentinel.webui.server import start_webui_server
        webui_thread = threading.Thread(
            target=start_webui_server,
            args=(guardian, args.webui_port),
            daemon=True
        )
        webui_thread.start()
        logger.info(f"🌐 WebUI started on http://localhost:{args.webui_port}")
    
    guardian.run(poll_interval=args.interval)


if __name__ == "__main__":
    main()
