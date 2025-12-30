"""
Monitoring Service Processes

Runs indicator and system health collectors as separate processes.
"""

import sys
import time
import logging
import argparse
import multiprocessing
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.indicator_collector import IndicatorMetricsCollector
from monitoring.system_health_collector import SystemHealthCollector
from observability.logger import setup_logger


def run_indicator_service(config_path: str = None, update_interval: float = 1.0):
    """Run indicator monitoring service"""
    logger = setup_logger("cthulu.indicator_service", level=logging.INFO)
    logger.info("Starting Indicator Monitoring Service...")
    
    collector = IndicatorMetricsCollector(
        config_path=config_path,
        update_interval=update_interval
    )
    
    try:
        collector.start()
        logger.info("Indicator service running. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        collector.stop()


def run_system_health_service(update_interval: float = 5.0):
    """Run system health monitoring service"""
    logger = setup_logger("cthulu.system_health_service", level=logging.INFO)
    logger.info("Starting System Health Monitoring Service...")
    
    collector = SystemHealthCollector(update_interval=update_interval)
    
    try:
        collector.start()
        logger.info("System health service running. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        collector.stop()


def _run_indicator_service(config_path: str, update_interval: float):
    """Target function for subprocess - must be module-level for Windows spawn"""
    logger = setup_logger("cthulu.indicator_service", level=logging.INFO)
    logger.info("Starting Indicator Monitoring Service...")
    
    collector = IndicatorMetricsCollector(
        config_path=config_path,
        update_interval=update_interval
    )
    
    try:
        collector.start()
        logger.info("Indicator service running. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        collector.stop()


def _run_system_health_service(update_interval: float):
    """Target function for subprocess - must be module-level for Windows spawn"""
    logger = setup_logger("cthulu.system_health_service", level=logging.INFO)
    logger.info("Starting System Health Monitoring Service...")
    
    collector = SystemHealthCollector(update_interval=update_interval)
    
    try:
        collector.start()
        logger.info("System health service running. Press Ctrl+C to stop.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        collector.stop()


def start_indicator_process(config_path: str = None, update_interval: float = 1.0):
    """Start indicator service as subprocess"""
    process = multiprocessing.Process(
        target=_run_indicator_service,
        args=(config_path, update_interval),
        daemon=False
    )
    process.start()
    return process


def start_system_health_process(update_interval: float = 5.0):
    """Start system health service as subprocess"""
    process = multiprocessing.Process(
        target=_run_system_health_service,
        args=(update_interval,),
        daemon=False
    )
    process.start()
    return process


def start_monitoring_services(indicator_interval: float = 1.0, 
                               system_interval: float = 5.0,
                               config_path: str = None):
    """
    Start both monitoring services as separate processes.
    
    Called by bootstrap to automatically start monitoring when Cthulu starts.
    
    Args:
        indicator_interval: Update interval for indicator metrics (default: 1.0s)
        system_interval: Update interval for system health (default: 5.0s)
        config_path: Optional path to indicator config JSON
        
    Returns:
        List of started processes, or empty list on failure
    """
    processes = []
    logger = logging.getLogger("cthulu.monitoring")
    
    try:
        indicator_proc = start_indicator_process(
            config_path=config_path,
            update_interval=indicator_interval
        )
        if indicator_proc:
            processes.append(indicator_proc)
            logger.info(f"Indicator service started (PID: {indicator_proc.pid})")
    except Exception as e:
        logger.warning(f"Failed to start indicator service: {e}")
    
    try:
        system_proc = start_system_health_process(update_interval=system_interval)
        if system_proc:
            processes.append(system_proc)
            logger.info(f"System health service started (PID: {system_proc.pid})")
    except Exception as e:
        logger.warning(f"Failed to start system health service: {e}")
    
    return processes


def stop_monitoring_services(processes):
    """
    Stop monitoring service processes.
    
    Args:
        processes: List of process objects from start_monitoring_services
    """
    logger = logging.getLogger("cthulu.monitoring")
    
    for proc in processes:
        try:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=5.0)
                if proc.is_alive():
                    proc.kill()
                    proc.join(timeout=2.0)
        except Exception as e:
            logger.warning(f"Error stopping process {proc.pid}: {e}")
    
    logger.info("Monitoring services stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Cthulu Monitoring Services',
        epilog="""
Services:
  indicator    - Indicator & signal monitoring with scoring
  system       - System health & resource monitoring
  both         - Run both services

Examples:
  python -m monitoring.service indicator
  python -m monitoring.service system
  python -m monitoring.service both
        """
    )
    parser.add_argument('service', choices=['indicator', 'system', 'both'],
                       help='Which service to run')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Update interval for indicator service (default: 1.0s)')
    parser.add_argument('--system-interval', type=float, default=5.0,
                       help='Update interval for system health service (default: 5.0s)')
    parser.add_argument('--config', help='Path to indicator config JSON')
    
    args = parser.parse_args()
    
    if args.service == 'indicator':
        run_indicator_service(config_path=args.config, update_interval=args.interval)
    elif args.service == 'system':
        run_system_health_service(update_interval=args.system_interval)
    elif args.service == 'both':
        # Start both as subprocesses
        logger = setup_logger("cthulu.monitoring", level=logging.INFO)
        logger.info("Starting both monitoring services...")
        
        indicator_proc = start_indicator_process(config_path=args.config, 
                                                 update_interval=args.interval)
        system_proc = start_system_health_process(update_interval=args.system_interval)
        
        logger.info(f"Indicator service PID: {indicator_proc.pid}")
        logger.info(f"System health service PID: {system_proc.pid}")
        logger.info("Press Ctrl+C to stop all services.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down all services...")
            indicator_proc.terminate()
            system_proc.terminate()
            indicator_proc.join(timeout=5)
            system_proc.join(timeout=5)


if __name__ == '__main__':
    main()
