"""
Health Check Module

Provides health and readiness endpoints for monitoring MT5 connectivity
and system status. Useful for container orchestration and alerting.
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    latency_ms: float
    timestamp: datetime
    details: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {}
        }


class HealthChecker:
    """
    Health check coordinator for Herald trading system.
    
    Performs checks on:
    - MT5 connectivity
    - Database availability
    - Account status
    - System resources
    """
    
    def __init__(self, connector=None, database=None):
        """
        Initialize health checker.
        
        Args:
            connector: MT5Connector instance (optional)
            database: Database instance (optional)
        """
        self.logger = logging.getLogger("cthulhu.health")
        self.connector = connector
        self.database = database
        self._last_check: Optional[Dict[str, HealthCheckResult]] = None
        self._last_check_time: Optional[datetime] = None
        
    def check_mt5_connection(self) -> HealthCheckResult:
        """Check MT5 terminal connectivity."""
        start = time.perf_counter()
        
        if self.connector is None:
            return HealthCheckResult(
                name="mt5_connection",
                status=HealthStatus.UNHEALTHY,
                message="MT5 connector not configured",
                latency_ms=0,
                timestamp=datetime.now()
            )
        
        try:
            is_connected = self.connector.is_connected()
            latency = (time.perf_counter() - start) * 1000
            
            if is_connected:
                account_info = self.connector.get_account_info()
                return HealthCheckResult(
                    name="mt5_connection",
                    status=HealthStatus.HEALTHY,
                    message="Connected to MT5",
                    latency_ms=latency,
                    timestamp=datetime.now(),
                    details={
                        "server": self.connector.config.server if hasattr(self.connector, 'config') else "unknown",
                        "trade_allowed": account_info.get("trade_allowed", False) if account_info else False
                    }
                )
            else:
                return HealthCheckResult(
                    name="mt5_connection",
                    status=HealthStatus.UNHEALTHY,
                    message="Not connected to MT5",
                    latency_ms=latency,
                    timestamp=datetime.now()
                )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name="mt5_connection",
                status=HealthStatus.UNHEALTHY,
                message=f"MT5 check failed: {str(e)}",
                latency_ms=latency,
                timestamp=datetime.now()
            )
    
    def check_database(self) -> HealthCheckResult:
        """Check database connectivity."""
        start = time.perf_counter()
        
        if self.database is None:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database not configured (optional)",
                latency_ms=0,
                timestamp=datetime.now()
            )
        
        try:
            # Try to get metrics or do a simple query
            if hasattr(self.database, 'get_metrics'):
                self.database.get_metrics()
            latency = (time.perf_counter() - start) * 1000
            
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database accessible",
                latency_ms=latency,
                timestamp=datetime.now()
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name="database",
                status=HealthStatus.DEGRADED,
                message=f"Database check failed: {str(e)}",
                latency_ms=latency,
                timestamp=datetime.now()
            )
    
    def check_account_status(self) -> HealthCheckResult:
        """Check trading account status."""
        start = time.perf_counter()
        
        if self.connector is None or not self.connector.is_connected():
            return HealthCheckResult(
                name="account_status",
                status=HealthStatus.UNHEALTHY,
                message="Cannot check account - not connected",
                latency_ms=0,
                timestamp=datetime.now()
            )
        
        try:
            account_info = self.connector.get_account_info()
            latency = (time.perf_counter() - start) * 1000
            
            if not account_info:
                return HealthCheckResult(
                    name="account_status",
                    status=HealthStatus.UNHEALTHY,
                    message="Failed to get account info",
                    latency_ms=latency,
                    timestamp=datetime.now()
                )
            
            trade_allowed = account_info.get("trade_allowed", False)
            margin_level = account_info.get("margin_level", 0)
            
            # Check margin level (if < 100%, account at risk)
            if margin_level > 0 and margin_level < 100:
                status = HealthStatus.DEGRADED
                message = f"Low margin level: {margin_level:.1f}%"
            elif not trade_allowed:
                status = HealthStatus.DEGRADED
                message = "Trading not allowed on account"
            else:
                status = HealthStatus.HEALTHY
                message = "Account ready for trading"
            
            return HealthCheckResult(
                name="account_status",
                status=status,
                message=message,
                latency_ms=latency,
                timestamp=datetime.now(),
                details={
                    "balance": account_info.get("balance", 0),
                    "equity": account_info.get("equity", 0),
                    "margin_level": margin_level,
                    "trade_allowed": trade_allowed
                }
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return HealthCheckResult(
                name="account_status",
                status=HealthStatus.UNHEALTHY,
                message=f"Account check failed: {str(e)}",
                latency_ms=latency,
                timestamp=datetime.now()
            )
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Returns:
            Dict with overall status and individual check results
        """
        checks = [
            self.check_mt5_connection(),
            self.check_database(),
            self.check_account_status(),
        ]
        
        self._last_check = {c.name: c for c in checks}
        self._last_check_time = datetime.now()
        
        # Determine overall status
        statuses = [c.status for c in checks]
        if HealthStatus.UNHEALTHY in statuses:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        
        total_latency = sum(c.latency_ms for c in checks)
        
        return {
            "status": overall.value,
            "timestamp": self._last_check_time.isoformat(),
            "total_latency_ms": round(total_latency, 2),
            "checks": {c.name: c.to_dict() for c in checks}
        }
    
    def liveness(self) -> Dict[str, Any]:
        """
        Kubernetes liveness probe.
        Returns healthy if the process is running.
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "cthulhu"
        }
    
    def readiness(self) -> Dict[str, Any]:
        """
        Kubernetes readiness probe.
        Returns healthy only if MT5 is connected and ready to trade.
        """
        mt5_check = self.check_mt5_connection()
        account_check = self.check_account_status()
        
        if mt5_check.status == HealthStatus.HEALTHY and account_check.status == HealthStatus.HEALTHY:
            return {
                "status": "ready",
                "timestamp": datetime.now().isoformat(),
                "service": "cthulhu"
            }
        else:
            return {
                "status": "not_ready",
                "timestamp": datetime.now().isoformat(),
                "service": "cthulhu",
                "reason": mt5_check.message if mt5_check.status != HealthStatus.HEALTHY else account_check.message
            }
