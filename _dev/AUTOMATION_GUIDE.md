# System Map Automation Guide

**Created:** January 4, 2026  
**Purpose:** Automate system map updates for seamless maintenance  

---

## Overview

The enhanced `system_map.html` is designed to be automation-friendly with multiple update strategies. This guide provides implementation options for keeping the system map synchronized with code changes.

## Automation Strategies

### 1. GitHub Actions Workflow (Recommended)

**File:** `.github/workflows/update-system-map.yml`

```yaml
name: Update System Map
on:
    push:
        branches: [ main ]
        paths: 
            - '**/*.py'
            - 'OVERVIEW.md'
            - '_dev/**'

jobs:
    update-system-map:
        runs-on: ubuntu-latest
        steps:
        - uses: actions/checkout@v4
            with:
                fetch-depth: 0
                
        - name: Setup Python
            uses: actions/setup-python@v4
            with:
                python-version: '3.11'
                
        - name: Install dependencies
            run: |
                pip install ast-tools networkx jinja2
                
        - name: Scan codebase and update map
            run: python .github/scripts/update_system_map.py
            
        - name: Commit changes
            run: |
                git config --local user.email "action@github.com"
                git config --local user.name "GitHub Action"
                git add _dev/system_map.html
                git diff --staged --quiet || git commit -m "Auto-update system map"
                git push
```

**Scanner Script:** `.github/scripts/update_system_map.py`

```python
#!/usr/bin/env python3
"""
System Map Auto-Updater
Scans Python files and updates system_map.html with current architecture
"""
import ast
import os
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re

class SystemScanner:
        def __init__(self, project_root):
                self.project_root = Path(project_root)
                self.modules = defaultdict(list)
                self.dependencies = defaultdict(set)
                self.file_stats = {
                        'total_files': 0,
                        'total_lines': 0,
                        'subsystems': set(),
                        'strategies': 0,
                        'indicators': 0,
                        'exit_strategies': 0
                }

        def scan_directory(self, directory):
                """Scan directory for Python files and analyze structure"""
                py_files = list(directory.rglob('*.py'))
                
                for py_file in py_files:
                        if '__pycache__' in str(py_file) or 'venv' in str(py_file):
                                continue
                                
                        self.analyze_file(py_file)
                        
        def analyze_file(self, file_path):
                """Analyze a Python file for imports and structure"""
                try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                        # Count lines
                        lines = len(content.splitlines())
                        self.file_stats['total_lines'] += lines
                        self.file_stats['total_files'] += 1
                        
                        # Parse AST for imports
                        try:
                                tree = ast.parse(content)
                                imports = self.extract_imports(tree)
                                
                                # Categorize file
                                rel_path = file_path.relative_to(self.project_root)
                                subsystem = str(rel_path.parts[0]) if rel_path.parts else 'root'
                                
                                self.modules[subsystem].append({
                                        'file': str(rel_path),
                                        'imports': imports,
                                        'lines': lines
                                })
                                
                                self.file_stats['subsystems'].add(subsystem)
                                
                                # Count specific types
                                if 'strategy' in str(rel_path) and not rel_path.name.startswith('__'):
                                        self.file_stats['strategies'] += 1
                                elif 'indicators' in str(rel_path) and not rel_path.name.startswith('__'):
                                        self.file_stats['indicators'] += 1
                                elif 'exit' in str(rel_path) and not rel_path.name.startswith('__'):
                                        self.file_stats['exit_strategies'] += 1
                                        
                        except SyntaxError:
                                print(f"Syntax error in {file_path}")
                                
                except Exception as e:
                        print(f"Error analyzing {file_path}: {e}")
                        
        def extract_imports(self, tree):
                """Extract import statements from AST"""
                imports = []
                for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                                for alias in node.names:
                                        imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                        imports.append(node.module)
                return imports
                
        def update_html_stats(self, html_path):
                """Update statistics in system_map.html"""
                with open(html_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                # Update stats
                stats_updates = {
                        r'<div class="stat-number">\d+</div>\s*<div class="stat-label">Core Subsystems</div>':
                                f'<div class="stat-number">{len(self.file_stats["subsystems"])}</div>\n                <div class="stat-label">Core Subsystems</div>',
                        r'<div class="stat-number">\d+\+?</div>\s*<div class="stat-label">Python Files</div>':
                                f'<div class="stat-number">{self.file_stats["total_files"]}</div>\n                <div class="stat-label">Python Files</div>',
                        r'<div class="stat-number">\d+</div>\s*<div class="stat-label">Strategy Types</div>':
                                f'<div class="stat-number">{self.file_stats["strategies"]}</div>\n                <div class="stat-label">Strategy Types</div>',
                        r'<div class="stat-number">\d+</div>\s*<div class="stat-label">Technical Indicators</div>':
                                f'<div class="stat-number">{self.file_stats["indicators"]}</div>\n                <div class="stat-label">Technical Indicators</div>',
                        r'<div class="stat-number">\d+</div>\s*<div class="stat-label">Exit Strategies</div>':
                                f'<div class="stat-number">{self.file_stats["exit_strategies"]}</div>\n                <div class="stat-label">Exit Strategies</div>'
                }
                
                for pattern, replacement in stats_updates.items():
                        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                        
                # Update timestamp
                timestamp = datetime.now().strftime("%B %d, %Y - %H:%M UTC")
                content = re.sub(
                        r'Last updated: .+?UTC',
                        f'Last updated: {timestamp}',
                        content
                )
                
                # Update version badge with file count
                content = re.sub(
                        r'<div class="version-badge">\d+ Files Mapped</div>',
                        f'<div class="version-badge">{self.file_stats["total_files"]} Files Mapped</div>',
                        content
                )
                
                with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
        def generate_report(self):
                """Generate automation report"""
                return {
                        'timestamp': datetime.now().isoformat(),
                        'stats': dict(self.file_stats),
                        'subsystems': list(self.file_stats['subsystems']),
                        'total_lines': self.file_stats['total_lines']
                }

def main():
        scanner = SystemScanner('.')
        scanner.scan_directory(Path('.'))
        
        # Update HTML file
        html_path = Path('_dev/system_map.html')
        if html_path.exists():
                scanner.update_html_stats(html_path)
                print(f"Updated {html_path}")
        
        # Generate report
        report = scanner.generate_report()
        print(f"Scanned {report['stats']['total_files']} files")
        print(f"Total lines: {report['stats']['total_lines']}")
        print(f"Subsystems: {len(report['subsystems'])}")

if __name__ == '__main__':
        main()
```

### 2. Pre-commit Hook (Local Development)

**File:** `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Pre-commit hook to update system map

echo "Checking for system changes..."

# Check if Python files were modified
if git diff --cached --name-only | grep -E '\.py$|OVERVIEW\.md|_dev/' > /dev/null; then
        echo "Python files changed, updating system map..."
        
        # Run the scanner
        python .github/scripts/update_system_map.py
        
        # Add updated files to commit
        git add _dev/system_map.html
        
        echo "System map updated"
fi
```

### 3. Integration with Monitoring System

**File:** `observability/system_map_updater.py`

```python
"""
Real-time System Map Updater
Integrates with existing monitoring to update map with live data
"""
import json
import re
from datetime import datetime
from pathlib import Path

class LiveSystemMapUpdater:
        def __init__(self, html_path='_dev/system_map.html'):
                self.html_path = Path(html_path)
                
        def update_live_stats(self, metrics_data):
                """Update HTML with live system metrics"""
                if not self.html_path.exists():
                        return
                        
                with open(self.html_path, 'r') as f:
                        content = f.read()
                        
                # Update with live data from MetricsCollector
                live_updates = {
                        'uptime': metrics_data.get('uptime_hours', 0),
                        'trades_today': metrics_data.get('trades_today', 0),
                        'win_rate': metrics_data.get('win_rate', 0.0),
                        'active_positions': metrics_data.get('active_positions', 0)
                }
                
                # Insert live data section
                live_section = f"""
                <div class="live-stats" id="liveStats">
                        <h3>Live System Status</h3>
                        <div class="live-grid">
                                <div class="live-item">
                                        <span class="live-value">{live_updates['uptime']:.1f}h</span>
                                        <span class="live-label">Uptime</span>
                                </div>
                                <div class="live-item">
                                        <span class="live-value">{live_updates['trades_today']}</span>
                                        <span class="live-label">Trades Today</span>
                                </div>
                                <div class="live-item">
                                        <span class="live-value">{live_updates['win_rate']:.1%}</span>
                                        <span class="live-label">Win Rate</span>
                                </div>
                                <div class="live-item">
                                        <span class="live-value">{live_updates['active_positions']}</span>
                                        <span class="live-label">Open Positions</span>
                                </div>
                        </div>
                </div>
                """
                
                # Insert before footer
                content = content.replace('<div class="footer">', live_section + '\n        <div class="footer">')
                
                with open(self.html_path, 'w') as f:
                        f.write(content)

# Integration with existing metrics collection
def update_system_map_with_live_data():
        """Call this from observability/metrics.py"""
        from observability.metrics import MetricsCollector
        
        metrics = MetricsCollector()
        current_metrics = metrics.get_current_metrics()
        
        updater = LiveSystemMapUpdater()
        updater.update_live_stats(current_metrics)
```

### 4. Scheduled Update via Windows Task Scheduler

**File:** `scripts/update_system_map.ps1`

```powershell
# PowerShell script for Windows Task Scheduler
# Run daily at 2 AM to update system map

$ProjectRoot = "C:\workspace\cthulu"
cd $ProjectRoot

# Activate Python environment if needed
if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
}

# Run the update script
python .github\scripts\update_system_map.py

# Commit changes if Git is available
if (Get-Command git -ErrorAction SilentlyContinue) {
        git add _dev\system_map.html
        $changes = git status --porcelain
        if ($changes) {
                git commit -m "Scheduled system map update"
                Write-Host "System map updated and committed"
        } else {
                Write-Host "No changes to commit"
        }
} else {
        Write-Host "Git not available, changes not committed"
}

Write-Host "System map update completed at $(Get-Date)"
```

## Integration Points

### With Existing Systems

1. **MetricsCollector Integration**
     ```python
     # In observability/metrics.py
     def collect_metrics(self):
             # ... existing code ...
             
             # Update system map with live stats
             if hasattr(self, 'update_system_map'):
                     self.update_system_map_with_live_data()
     ```

2. **Trading Loop Integration**
     ```python
     # In core/trading_loop.py
     def main_loop(self):
             # ... existing code ...
             
             # Periodic system map update (every 1000 loops)
             if self.loop_count % 1000 == 0:
                     self.update_system_map_stats()
     ```

3. **Database Integration**
     ```sql
     -- Track system map updates
     CREATE TABLE system_map_updates (
             id INTEGER PRIMARY KEY,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
             files_scanned INTEGER,
             subsystems_found INTEGER,
             update_type TEXT  -- 'scheduled', 'git_hook', 'manual'
     );
     ```

## Implementation Priority

### Phase 1: Basic Automation (Week 1)
- [ ] Implement GitHub Actions workflow
- [ ] Create update scanner script
- [ ] Test with sample commits

### Phase 2: Enhanced Automation (Week 2)
- [ ] Add pre-commit hook
- [ ] Integrate with metrics collection
- [ ] Add live status indicators

### Phase 3: Advanced Features (Week 3)
- [ ] Real-time WebSocket updates
- [ ] Automated dependency graph generation
- [ ] Integration with CI/CD pipeline

## Success Metrics

- **Automation Coverage:** 100% of changes trigger updates
- **Accuracy:** System map reflects actual code structure within 1 hour
- **Maintenance Overhead:** < 5 minutes/week manual intervention
- **Developer Experience:** Zero friction for contributors

## Monitoring & Alerting

### GitHub Actions Notifications
```yaml
- name: Notify on failure
    if: failure()
    uses: 8398a7/action-slack@v3
    with:
        status: failure
        text: "System map update failed"
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Log Integration
```python
import logging

logger = logging.getLogger('system_map_automation')
logger.info("Starting automated system map update")
logger.error("System map update failed: {error}")
logger.info("System map updated successfully")
```

## Maintenance Notes

### Weekly Tasks
- [ ] Review automation logs
- [ ] Validate system map accuracy
- [ ] Update automation scripts if needed

### Monthly Tasks  
- [ ] Performance review of automation
- [ ] Update dependencies
- [ ] Backup automation configurations

### As-Needed Tasks
- [ ] Add new subsystems to scanner
- [ ] Update HTML template for new features
- [ ] Extend integration points

---

**Next Steps:**
1. Choose automation strategy (GitHub Actions recommended)
2. Implement Phase 1 components
3. Test with live system
4. Expand to full automation suite

**Questions/Issues:** Document in `_dev/AUTOMATION_ISSUES.md`
