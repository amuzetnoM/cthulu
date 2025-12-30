"""
Observability Service Process

Runs as a separate process to collect and export metrics without blocking
the main trading loop. Provides:
- Real-time CSV metrics export
- Prometheus metrics export
- HTTP metrics endpoint (optional)

Usage:
    Can be started as subprocess from main trading system or run standalone.
"""

import os
import sys
import time
import logging
import signal
import argparse
import multiprocessing
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability.comprehensive_collector import ComprehensiveMetricsCollector
from observability.prometheus import PrometheusExporter
from observability.logger import setup_logger


class ObservabilityService:
    """
    Standalone observability service that runs as separate process.
    
    Collects comprehensive metrics and exports to:
    - CSV file (comprehensive_metrics.csv) - REQUIRED
    - Prometheus text file - OPTIONAL (--enable-prometheus flag)
    - Optional HTTP endpoint - OPTIONAL (--http-port)
    """
    
    def __init__(self, csv_path: str = None, prom_path: str = None, 
                 update_interval: float = 1.0, http_port: int = None,
                 enable_prometheus: bool = False):
        """
        Initialize observability service.
        
        Args:
            csv_path: Path to CSV metrics file
            prom_path: Path to Prometheus metrics file (only if enable_prometheus=True)
            update_interval: Seconds between updates
            http_port: Optional HTTP port for metrics endpoint
            enable_prometheus: Enable Prometheus export (default: False)
        """
        self.logger = setup_logger("cthulu.observability_service", level=logging.INFO)
        
        # Initialize collectors
        self.collector = ComprehensiveMetricsCollector(
            csv_path=csv_path,
            update_interval=update_interval
        )
        
        self.enable_prometheus = enable_prometheus
        self.prometheus = None
        if self.enable_prometheus:
            self.prometheus = PrometheusExporter(prefix="cthulu")
            self.prometheus._file_path = prom_path
            self.logger.info(f"Prometheus export ENABLED")
        else:
            self.logger.info(f"Prometheus export DISABLED (use --enable-prometheus to enable)")
        
        self.http_port = http_port
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Observability service initialized")
        self.logger.info(f"  CSV: {self.collector.csv_path}")
        if prom_path and self.enable_prometheus:
            self.logger.info(f"  Prometheus: {prom_path}")
        if http_port:
            self.logger.info(f"  HTTP: port {http_port}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def start(self):
        """Start the observability service"""
        self.logger.info("Starting observability service...")
        
        # Start metrics collection thread
        self.collector.start()
        
        # Start HTTP server if configured
        if self.http_port:
            self._start_http_server()
        
        self.running = True
        self.logger.info("Observability service started")
        
        # Main loop - export to Prometheus periodically (if enabled)
        try:
            while self.running:
                # Export to Prometheus only if enabled
                if self.enable_prometheus and self.prometheus:
                    snapshot = self.collector.get_current_snapshot()
                    self.prometheus.update_from_comprehensive_metrics(snapshot)
                    self.prometheus.write_to_file()
                
                # Sleep
                time.sleep(self.collector.update_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the observability service"""
        if not self.running:
            return
        
        self.logger.info("Stopping observability service...")
        self.running = False
        
        # Stop collector
        self.collector.stop()
        
        # Final export (if Prometheus enabled)
        if self.enable_prometheus and self.prometheus:
            try:
                snapshot = self.collector.get_current_snapshot()
                self.prometheus.update_from_comprehensive_metrics(snapshot)
                self.prometheus.write_to_file()
            except Exception as e:
                self.logger.error(f"Error in final export: {e}")
        
        self.logger.info("Observability service stopped")
    
    def _start_http_server(self):
        """Start HTTP metrics endpoint (optional)"""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            
            service = self
            
            class MetricsHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/metrics':
                        # Export Prometheus format (only if enabled)
                        if service.enable_prometheus and service.prometheus:
                            snapshot = service.collector.get_current_snapshot()
                            service.prometheus.update_from_comprehensive_metrics(snapshot)
                            content = service.prometheus.export_text()
                            
                            self.send_response(200)
                            self.send_header('Content-Type', 'text/plain; version=0.0.4')
                            self.end_headers()
                            self.wfile.write(content.encode())
                        else:
                            self.send_response(503)
                            self.send_header('Content-Type', 'text/plain')
                            self.end_headers()
                            self.wfile.write(b'Prometheus export disabled. Use --enable-prometheus flag.')
                    else:
                        self.send_response(404)
                        self.end_headers()
                
                def log_message(self, format, *args):
                    # Suppress request logging
                    pass
            
            server = HTTPServer(('0.0.0.0', self.http_port), MetricsHandler)
            
            import threading
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            
            self.logger.info(f"HTTP metrics endpoint started on port {self.http_port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start HTTP server: {e}")


def start_observability_process(csv_path: str = None, prom_path: str = None, 
                               update_interval: float = 1.0, http_port: int = None,
                               enable_prometheus: bool = False):
    """
    Start observability service as subprocess.
    
    Args:
        csv_path: Path to CSV file
        prom_path: Path to Prometheus file (only used if enable_prometheus=True)
        update_interval: Update interval in seconds
        http_port: Optional HTTP port
        enable_prometheus: Enable Prometheus export (default: False)
        
    Returns:
        Process object
    """
    def run_service():
        service = ObservabilityService(
            csv_path=csv_path,
            prom_path=prom_path,
            update_interval=update_interval,
            http_port=http_port,
            enable_prometheus=enable_prometheus
        )
        service.start()
    
    process = multiprocessing.Process(target=run_service, daemon=False)
    process.start()
    
    return process


def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Cthulu Observability Service')
    parser.add_argument('--csv', help='CSV metrics file path')
    parser.add_argument('--prometheus', help='Prometheus metrics file path')
    parser.add_argument('--interval', type=float, default=1.0, help='Update interval (seconds)')
    parser.add_argument('--http-port', type=int, help='HTTP metrics endpoint port')
    parser.add_argument('--enable-prometheus', action='store_true', 
                       help='Enable Prometheus export (default: disabled)')
    
    args = parser.parse_args()
    
    # Create service
    service = ObservabilityService(
        csv_path=args.csv,
        prom_path=args.prometheus,
        update_interval=args.interval,
        http_port=args.http_port,
        enable_prometheus=args.enable_prometheus
    )
    
    # Run
    service.start()


if __name__ == '__main__':
    main()
