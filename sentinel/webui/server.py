"""
SENTINEL WebUI Server
=====================
Provides real-time dashboard for monitoring Cthulu system health.
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentinel.core.guardian import SentinelGuardian


# Global reference to guardian instance
_guardian_instance = None


class SentinelRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Sentinel WebUI"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/" or self.path == "/index.html":
            self.serve_dashboard()
        elif self.path == "/api/status":
            self.serve_status_api()
        elif self.path == "/api/health":
            self.serve_health_api()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests for actions"""
        if self.path == "/api/restart-cthulu":
            self.action_restart_cthulu()
        elif self.path == "/api/stop-cthulu":
            self.action_stop_cthulu()
        elif self.path == "/api/start-mt5":
            self.action_start_mt5()
        elif self.path == "/api/enable-algo":
            self.action_enable_algo()
        else:
            self.send_error(404, "Not Found")
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html = self.generate_dashboard_html()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(html))
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_status_api(self):
        """Serve status JSON API"""
        if _guardian_instance:
            status = _guardian_instance.get_status_dict()
        else:
            status = {"error": "Guardian not initialized"}
        
        self.send_json(status)
    
    def serve_health_api(self):
        """Simple health check endpoint"""
        self.send_json({"status": "ok", "service": "sentinel"})
    
    def send_json(self, data):
        """Send JSON response"""
        body = json.dumps(data, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
    
    def send_json_response(self, success: bool, message: str):
        """Send action response"""
        self.send_json({"success": success, "message": message})
    
    def action_restart_cthulu(self):
        """Restart Cthulu action"""
        if _guardian_instance:
            _guardian_instance.stop_cthulu()
            success = _guardian_instance.start_cthulu()
            self.send_json_response(success, "Cthulu restarted" if success else "Failed to restart")
        else:
            self.send_json_response(False, "Guardian not initialized")
    
    def action_stop_cthulu(self):
        """Stop Cthulu action"""
        if _guardian_instance:
            success = _guardian_instance.stop_cthulu()
            self.send_json_response(success, "Cthulu stopped" if success else "Failed to stop")
        else:
            self.send_json_response(False, "Guardian not initialized")
    
    def action_start_mt5(self):
        """Start MT5 action"""
        if _guardian_instance:
            success = _guardian_instance.start_mt5()
            self.send_json_response(success, "MT5 started" if success else "Failed to start MT5")
        else:
            self.send_json_response(False, "Guardian not initialized")
    
    def action_enable_algo(self):
        """Enable algo trading action"""
        if _guardian_instance:
            success = _guardian_instance.enable_algo_trading()
            self.send_json_response(success, "Algo enabled" if success else "Failed to enable algo")
        else:
            self.send_json_response(False, "Guardian not initialized")
    
    def generate_dashboard_html(self) -> str:
        """Generate the dashboard HTML"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ SENTINEL - Cthulu Guardian</title>
    <style>
        :root {
            --bg-primary: #0a0f1e;
            --bg-secondary: #111827;
            --bg-card: #1a2332;
            --text-primary: #e4e4e7;
            --text-secondary: #9ca3af;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #374151;
        }
        
        .header h1 {
            font-size: 2em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .header h1 span {
            color: var(--accent-purple);
        }
        
        .uptime {
            background: var(--bg-card);
            padding: 10px 20px;
            border-radius: 8px;
            font-family: monospace;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #374151;
        }
        
        .card-title {
            font-size: 0.9em;
            color: var(--text-secondary);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .card-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
        }
        
        .status-healthy { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
        .status-degraded { background: rgba(245, 158, 11, 0.2); color: var(--accent-yellow); }
        .status-critical { background: rgba(239, 68, 68, 0.2); color: var(--accent-red); }
        .status-offline { background: rgba(107, 114, 128, 0.2); color: #6b7280; }
        .status-recovering { background: rgba(59, 130, 246, 0.2); color: var(--accent-blue); }
        
        .pulse {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .pulse-green { background: var(--accent-green); }
        .pulse-yellow { background: var(--accent-yellow); }
        .pulse-red { background: var(--accent-red); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        
        .actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary { background: var(--accent-blue); color: white; }
        .btn-success { background: var(--accent-green); color: white; }
        .btn-danger { background: var(--accent-red); color: white; }
        .btn-warning { background: var(--accent-yellow); color: black; }
        
        .btn:hover { transform: translateY(-2px); filter: brightness(1.1); }
        .btn:active { transform: translateY(0); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
        .metrics-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .metrics-table th,
        .metrics-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #374151;
        }
        
        .metrics-table th {
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        .error-log {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85em;
        }
        
        .error-item {
            padding: 8px;
            margin-bottom: 5px;
            background: rgba(239, 68, 68, 0.1);
            border-left: 3px solid var(--accent-red);
            border-radius: 4px;
        }
        
        .last-update {
            text-align: center;
            padding: 10px;
            color: var(--text-secondary);
            font-size: 0.85em;
        }
        
        .component-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #374151;
        }
        
        .component-status:last-child { border-bottom: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ <span>SENTINEL</span> Guardian</h1>
        <div class="uptime" id="uptime">Uptime: --:--:--</div>
    </div>
    
    <div class="grid">
        <div class="card">
            <div class="card-title">System State</div>
            <div class="card-value">
                <span class="status-indicator status-offline" id="system-state">
                    <span class="pulse pulse-red"></span>
                    OFFLINE
                </span>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">Cthulu Status</div>
            <div class="card-value" id="cthulu-state">--</div>
            <div class="card-subtitle" style="color: var(--text-secondary); margin-top: 5px;">
                PID: <span id="cthulu-pid">--</span>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">MT5 Status</div>
            <div class="card-value" id="mt5-state">--</div>
            <div class="card-subtitle" style="color: var(--text-secondary); margin-top: 5px;">
                PID: <span id="mt5-pid">--</span>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">Crash Count</div>
            <div class="card-value" style="color: var(--accent-red);" id="crash-count">0</div>
            <div class="card-subtitle" style="color: var(--text-secondary); margin-top: 5px;">
                Last: <span id="last-crash">Never</span>
            </div>
        </div>
    </div>
    
    <div class="grid">
        <div class="card">
            <div class="card-title">System Resources</div>
            <table class="metrics-table">
                <tr>
                    <td>CPU Usage</td>
                    <td id="cpu-percent">--%</td>
                </tr>
                <tr>
                    <td>Memory Usage</td>
                    <td id="memory-percent">--%</td>
                </tr>
                <tr>
                    <td>Recovery Attempts</td>
                    <td id="recovery-attempts">0</td>
                </tr>
            </table>
        </div>
        
        <div class="card">
            <div class="card-title">Quick Actions</div>
            <div class="actions" style="flex-direction: column;">
                <button class="btn btn-success" onclick="action('restart-cthulu')">
                    🔄 Restart Cthulu
                </button>
                <button class="btn btn-danger" onclick="action('stop-cthulu')">
                    ⛔ Stop Cthulu
                </button>
                <button class="btn btn-primary" onclick="action('start-mt5')">
                    📈 Start MT5
                </button>
                <button class="btn btn-warning" onclick="action('enable-algo')">
                    🤖 Enable Algo Trading
                </button>
            </div>
        </div>
    </div>
    
    <div class="card" style="margin-bottom: 30px;">
        <div class="card-title">Error Log</div>
        <div class="error-log" id="error-log">
            <div style="color: var(--text-secondary); text-align: center;">No errors recorded</div>
        </div>
    </div>
    
    <div class="last-update">
        Last updated: <span id="last-update">--</span>
    </div>
    
    <script>
        function formatUptime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
        
        function getStateClass(state) {
            const map = {
                'HEALTHY': 'status-healthy',
                'DEGRADED': 'status-degraded',
                'CRITICAL': 'status-critical',
                'OFFLINE': 'status-offline',
                'RECOVERING': 'status-recovering'
            };
            return map[state] || 'status-offline';
        }
        
        function getPulseClass(state) {
            const map = {
                'HEALTHY': 'pulse-green',
                'DEGRADED': 'pulse-yellow',
                'CRITICAL': 'pulse-red',
                'OFFLINE': 'pulse-red',
                'RECOVERING': 'pulse-yellow'
            };
            return map[state] || 'pulse-red';
        }
        
        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update system state
                const stateEl = document.getElementById('system-state');
                stateEl.className = `status-indicator ${getStateClass(data.system_state)}`;
                stateEl.innerHTML = `<span class="pulse ${getPulseClass(data.system_state)}"></span>${data.system_state}`;
                
                // Update other values
                document.getElementById('cthulu-state').textContent = data.cthulu_state;
                document.getElementById('cthulu-pid').textContent = data.cthulu_pid || '--';
                document.getElementById('mt5-state').textContent = data.mt5_state;
                document.getElementById('mt5-pid').textContent = data.mt5_pid || '--';
                document.getElementById('crash-count').textContent = data.crash_count;
                document.getElementById('last-crash').textContent = data.last_crash ? new Date(data.last_crash).toLocaleString() : 'Never';
                document.getElementById('cpu-percent').textContent = data.cpu_percent.toFixed(1) + '%';
                document.getElementById('memory-percent').textContent = data.memory_percent.toFixed(1) + '%';
                document.getElementById('recovery-attempts').textContent = data.recovery_attempts;
                document.getElementById('uptime').textContent = 'Uptime: ' + formatUptime(data.uptime_seconds);
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
                // Update error log
                const errorLog = document.getElementById('error-log');
                if (data.error_log && data.error_log.length > 0) {
                    errorLog.innerHTML = data.error_log.map(e => 
                        `<div class="error-item">${e}</div>`
                    ).join('');
                } else {
                    errorLog.innerHTML = '<div style="color: var(--text-secondary); text-align: center;">No errors recorded</div>';
                }
                
            } catch (error) {
                console.error('Failed to fetch status:', error);
            }
        }
        
        async function action(name) {
            try {
                const response = await fetch(`/api/${name}`, { method: 'POST' });
                const data = await response.json();
                alert(data.message);
                fetchStatus();
            } catch (error) {
                alert('Action failed: ' + error.message);
            }
        }
        
        // Initial fetch and polling
        fetchStatus();
        setInterval(fetchStatus, 3000);
    </script>
</body>
</html>'''


def start_webui_server(guardian: "SentinelGuardian", port: int = 8282):
    """Start the WebUI server"""
    global _guardian_instance
    _guardian_instance = guardian
    
    server = HTTPServer(("0.0.0.0", port), SentinelRequestHandler)
    server.serve_forever()
