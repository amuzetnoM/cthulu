"""
Observability Integration

Provides integration hooks for starting/stopping the observability service
as part of the Cthulu bootstrap process.
"""

import logging
import multiprocessing
from pathlib import Path
from typing import Optional


def start_observability_service(
    csv_path: Optional[str] = None,
    prom_path: Optional[str] = None,
    http_port: Optional[int] = None,
    update_interval: float = 1.0
) -> Optional[multiprocessing.Process]:
    """
    Start observability service as separate process during bootstrap.
    
    This starts comprehensive metrics collection in a separate process
    that won't block the main trading loop.
    
    Args:
        csv_path: Path to CSV metrics file (default: observability/comprehensive_metrics.csv)
        prom_path: Path to Prometheus metrics file (default: auto-detected)
        http_port: Optional HTTP port for metrics endpoint (e.g., 8181)
        update_interval: Seconds between metric updates
        
    Returns:
        Process object if started successfully, None otherwise
    """
    logger = logging.getLogger("cthulu.observability_integration")
    
    try:
        from observability.service import start_observability_process
        
        # Set defaults
        if csv_path is None:
            base_dir = Path(__file__).parent.parent / "observability"
            csv_path = str(base_dir / "comprehensive_metrics.csv")
        
        if prom_path is None:
            # Auto-detect based on OS
            import os
            if os.name == 'nt':
                prom_path = r"C:\workspace\cthulu\metrics\cthulu_metrics.prom"
            else:
                prom_path = "/tmp/cthulu_metrics.prom"
        
        logger.info("Starting observability service...")
        logger.info(f"  CSV: {csv_path}")
        logger.info(f"  Prometheus: {prom_path}")
        if http_port:
            logger.info(f"  HTTP: port {http_port}")
        
        # Start as subprocess
        process = start_observability_process(
            csv_path=csv_path,
            prom_path=prom_path,
            update_interval=update_interval,
            http_port=http_port
        )
        
        logger.info(f"Observability service started (PID: {process.pid})")
        return process
        
    except Exception as e:
        logger.error(f"Failed to start observability service: {e}")
        logger.error("Continuing without observability service")
        return None


def stop_observability_service(process: Optional[multiprocessing.Process]):
    """
    Stop observability service process.
    
    Args:
        process: Process object from start_observability_service
    """
    if process is None:
        return
    
    logger = logging.getLogger("cthulu.observability_integration")
    
    try:
        if process.is_alive():
            logger.info("Stopping observability service...")
            process.terminate()
            process.join(timeout=5.0)
            
            if process.is_alive():
                logger.warning("Observability service did not stop gracefully, killing...")
                process.kill()
                process.join(timeout=2.0)
            
            logger.info("Observability service stopped")
    except Exception as e:
        logger.error(f"Error stopping observability service: {e}")


def get_comprehensive_collector():
    """
    Get the comprehensive metrics collector for manual updates.
    
    Returns:
        ComprehensiveMetricsCollector instance
    """
    from observability.comprehensive_collector import ComprehensiveMetricsCollector
    return ComprehensiveMetricsCollector()
