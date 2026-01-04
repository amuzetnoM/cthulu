"""
Android Background Service Manager

Provides robust background execution for Cthulu on Android/Termux.
Handles:
- Process persistence when app goes to background
- Signal handling for graceful shutdown
- Watchdog for automatic restart
- Wake locks to prevent process killing
- Logging and monitoring for headless operation

Usage:
    python -m cthulu.core.android_service --config config.json

Or programmatically:
    from cthulu.core.android_service import AndroidServiceManager
    service = AndroidServiceManager(config)
    service.start()
"""

import os
import sys
import signal
import time
import logging
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger('Cthulu.android_service')


@dataclass
class ServiceConfig:
    """Android service configuration."""
    # Process management
    enable_watchdog: bool = True
    watchdog_interval_seconds: int = 60
    max_restart_attempts: int = 5
    restart_cooldown_seconds: int = 300
    
    # Wake lock (prevents Android from killing process)
    acquire_wake_lock: bool = True
    wake_lock_tag: str = "cthulu:trading"
    
    # Termux-specific
    enable_termux_notification: bool = True
    notification_title: str = "Cthulu Trading"
    notification_content: str = "Trading bot running"
    
    # Logging for headless operation
    log_to_file: bool = True
    log_file: str = "logs/cthulu_service.log"
    max_log_size_mb: int = 10
    log_backup_count: int = 3
    
    # Health checks
    health_check_interval_seconds: int = 30
    max_consecutive_failures: int = 3


class TermuxIntegration:
    """
    Termux-specific integrations for Android background operation.
    
    Uses Termux:API when available for:
    - Wake locks
    - Notifications
    - Battery optimization bypass
    """
    
    def __init__(self):
        self.termux_api_available = self._check_termux_api()
        self.wake_lock_held = False
        
    def _check_termux_api(self) -> bool:
        """Check if Termux:API is available."""
        try:
            result = subprocess.run(
                ['termux-notification', '--help'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def acquire_wake_lock(self, tag: str = "cthulu") -> bool:
        """
        Acquire a wake lock to prevent Android from killing the process.
        
        Uses termux-wake-lock if available.
        """
        if not self.termux_api_available:
            logger.warning("Termux:API not available, cannot acquire wake lock")
            return False
        
        try:
            subprocess.run(['termux-wake-lock'], check=True, timeout=10)
            self.wake_lock_held = True
            logger.info("Wake lock acquired - process will persist in background")
            return True
        except Exception as e:
            logger.error(f"Failed to acquire wake lock: {e}")
            return False
    
    def release_wake_lock(self) -> bool:
        """Release the wake lock."""
        if not self.wake_lock_held:
            return True
        
        try:
            subprocess.run(['termux-wake-unlock'], check=True, timeout=10)
            self.wake_lock_held = False
            logger.info("Wake lock released")
            return True
        except Exception as e:
            logger.error(f"Failed to release wake lock: {e}")
            return False
    
    def show_notification(self, title: str, content: str, 
                         notification_id: str = "cthulu_status") -> bool:
        """
        Show a persistent notification in Android status bar.
        
        This helps keep the process alive and informs user of status.
        """
        if not self.termux_api_available:
            return False
        
        try:
            subprocess.run([
                'termux-notification',
                '--id', notification_id,
                '--title', title,
                '--content', content,
                '--ongoing',  # Persistent notification
                '--priority', 'low'
            ], check=True, timeout=10)
            return True
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            return False
    
    def update_notification(self, content: str, 
                           notification_id: str = "cthulu_status") -> bool:
        """Update the notification content."""
        return self.show_notification("Cthulu Trading", content, notification_id)
    
    def remove_notification(self, notification_id: str = "cthulu_status") -> bool:
        """Remove the notification."""
        if not self.termux_api_available:
            return True
        
        try:
            subprocess.run([
                'termux-notification-remove', notification_id
            ], check=True, timeout=10)
            return True
        except Exception:
            return False
    
    def get_battery_status(self) -> Optional[Dict[str, Any]]:
        """Get battery status to adjust behavior."""
        if not self.termux_api_available:
            return None
        
        try:
            result = subprocess.run(
                ['termux-battery-status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
        except Exception:
            pass
        return None


class SignalHandler:
    """
    Handles Unix signals for graceful shutdown.
    
    Ensures proper cleanup when:
    - User presses Ctrl+C (SIGINT)
    - Process is terminated (SIGTERM)
    - Terminal is closed (SIGHUP)
    """
    
    def __init__(self, shutdown_callback: Callable[[], None]):
        self.shutdown_callback = shutdown_callback
        self.shutdown_requested = False
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up signal handlers."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        # SIGHUP for terminal disconnect (important for Termux)
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, self._handle_sighup)
    
    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}, initiating graceful shutdown...")
        self.shutdown_requested = True
        self.shutdown_callback()
    
    def _handle_sighup(self, signum, frame):
        """
        Handle SIGHUP (terminal disconnect).
        
        On Android/Termux, this happens when:
        - App goes to background
        - Screen turns off
        - Terminal session ends
        
        We DON'T shutdown - we continue running in background.
        """
        logger.info("Received SIGHUP (terminal disconnect) - continuing in background")
        # Don't call shutdown - keep running


class Watchdog:
    """
    Watchdog timer to detect and recover from hangs.
    
    Monitors the trading loop and restarts if it becomes unresponsive.
    """
    
    def __init__(self, timeout_seconds: int = 120, 
                 restart_callback: Optional[Callable] = None):
        self.timeout = timeout_seconds
        self.restart_callback = restart_callback
        self.last_heartbeat = time.time()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the watchdog thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        logger.info(f"Watchdog started with {self.timeout}s timeout")
    
    def stop(self):
        """Stop the watchdog."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
    
    def heartbeat(self):
        """Call this regularly from the trading loop."""
        self.last_heartbeat = time.time()
    
    def _monitor(self):
        """Monitor thread that checks for heartbeats."""
        while not self._stop_event.is_set():
            elapsed = time.time() - self.last_heartbeat
            
            if elapsed > self.timeout:
                logger.error(f"Watchdog timeout! No heartbeat for {elapsed:.0f}s")
                if self.restart_callback:
                    self.restart_callback()
                # Reset heartbeat after restart attempt
                self.last_heartbeat = time.time()
            
            self._stop_event.wait(10)  # Check every 10 seconds


class AndroidServiceManager:
    """
    Main service manager for running Cthulu on Android.
    
    Provides:
    - Background execution with wake locks
    - Graceful signal handling
    - Watchdog for automatic recovery
    - Status notifications
    - Logging for headless operation
    """
    
    def __init__(self, config: ServiceConfig = None):
        self.config = config or ServiceConfig()
        self.termux = TermuxIntegration()
        self.watchdog: Optional[Watchdog] = None
        self.signal_handler: Optional[SignalHandler] = None
        self.trading_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_time: Optional[datetime] = None
        self._restart_count = 0
        self._last_restart_time: Optional[datetime] = None
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging for headless operation."""
        if not self.config.log_to_file:
            return
        
        log_path = Path(self.config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        from logging.handlers import RotatingFileHandler
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=self.config.max_log_size_mb * 1024 * 1024,
            backupCount=self.config.log_backup_count
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Add to root logger
        logging.getLogger().addHandler(handler)
        logger.info("File logging initialized")
    
    def start(self, trading_loop_func: Callable[[], None]):
        """
        Start the service with the given trading loop function.
        
        Args:
            trading_loop_func: Function that runs the trading loop
        """
        logger.info("=" * 60)
        logger.info("Starting Cthulu Android Service")
        logger.info("=" * 60)
        
        self._running = True
        self._start_time = datetime.now()
        
        # Set up signal handlers
        self.signal_handler = SignalHandler(self.shutdown)
        
        # Acquire wake lock
        if self.config.acquire_wake_lock:
            self.termux.acquire_wake_lock(self.config.wake_lock_tag)
        
        # Show notification
        if self.config.enable_termux_notification:
            self.termux.show_notification(
                self.config.notification_title,
                self.config.notification_content
            )
        
        # Start watchdog
        if self.config.enable_watchdog:
            self.watchdog = Watchdog(
                timeout_seconds=self.config.watchdog_interval_seconds * 2,
                restart_callback=self._handle_watchdog_timeout
            )
            self.watchdog.start()
        
        # Run trading loop
        try:
            self._run_with_recovery(trading_loop_func)
        finally:
            self._cleanup()
    
    def _run_with_recovery(self, trading_loop_func: Callable[[], None]):
        """Run the trading loop with automatic recovery."""
        while self._running:
            try:
                logger.info("Starting trading loop...")
                self._update_notification("Trading active")
                trading_loop_func()
                
                # If we get here normally, loop ended
                if self._running:
                    logger.warning("Trading loop ended unexpectedly, restarting...")
                    self._handle_restart()
                    
            except Exception as e:
                logger.exception(f"Trading loop crashed: {e}")
                self._update_notification(f"Error: {str(e)[:30]}")
                
                if self._running:
                    self._handle_restart()
    
    def _handle_restart(self):
        """Handle restart logic with cooldown."""
        now = datetime.now()
        
        # Check cooldown
        if self._last_restart_time:
            elapsed = (now - self._last_restart_time).total_seconds()
            if elapsed < self.config.restart_cooldown_seconds:
                self._restart_count += 1
            else:
                self._restart_count = 1
        else:
            self._restart_count = 1
        
        self._last_restart_time = now
        
        # Check max restarts
        if self._restart_count > self.config.max_restart_attempts:
            logger.error(f"Max restart attempts ({self.config.max_restart_attempts}) exceeded")
            self._update_notification("Stopped: Too many restarts")
            self._running = False
            return
        
        # Wait before restart
        wait_time = min(30 * self._restart_count, 300)
        logger.info(f"Restart attempt {self._restart_count}/{self.config.max_restart_attempts} in {wait_time}s")
        self._update_notification(f"Restarting in {wait_time}s...")
        time.sleep(wait_time)
    
    def _handle_watchdog_timeout(self):
        """Handle watchdog timeout - force restart."""
        logger.error("Watchdog detected unresponsive trading loop")
        self._update_notification("Watchdog restart...")
        # The main loop will handle restart
    
    def _update_notification(self, content: str):
        """Update the status notification."""
        if self.config.enable_termux_notification:
            uptime = ""
            if self._start_time:
                delta = datetime.now() - self._start_time
                hours = delta.total_seconds() / 3600
                uptime = f" | Up: {hours:.1f}h"
            self.termux.update_notification(f"{content}{uptime}")
    
    def heartbeat(self):
        """Call from trading loop to signal healthy operation."""
        if self.watchdog:
            self.watchdog.heartbeat()
    
    def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutdown requested...")
        self._running = False
        self._update_notification("Shutting down...")
    
    def _cleanup(self):
        """Clean up resources on exit."""
        logger.info("Cleaning up...")
        
        if self.watchdog:
            self.watchdog.stop()
        
        if self.config.acquire_wake_lock:
            self.termux.release_wake_lock()
        
        if self.config.enable_termux_notification:
            self.termux.remove_notification()
        
        logger.info("Cthulu Android Service stopped")


def create_background_runner(config_path: str = "config.json"):
    """
    Create a background runner for Cthulu.
    
    This is the main entry point for running Cthulu as a background service
    on Android/Termux.
    
    Usage:
        python -c "from cthulu.core.android_service import create_background_runner; create_background_runner()"
    """
    import json
    from cthulu.core.bootstrap import bootstrap
    from cthulu.core.trading_loop import TradingLoop
    
    # Load config
    with open(config_path) as f:
        app_config = json.load(f)
    
    # Create service manager
    service = AndroidServiceManager(ServiceConfig(
        enable_watchdog=True,
        enable_termux_notification=True,
        acquire_wake_lock=True,
        log_to_file=True
    ))
    
    # Bootstrap trading system
    ctx = bootstrap(app_config)
    loop = TradingLoop(ctx)
    
    def trading_loop_with_heartbeat():
        """Wrapper that sends heartbeats."""
        while True:
            loop.tick()
            service.heartbeat()
            time.sleep(1)
    
    # Start service
    service.start(trading_loop_with_heartbeat)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cthulu Android Background Service")
    parser.add_argument("--config", default="config.json", help="Config file path")
    args = parser.parse_args()
    
    create_background_runner(args.config)
