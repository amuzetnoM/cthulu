#!/usr/bin/env python3
"""
Cthulu Code Analyzer - Automated System Analysis Tool

This tool scans the Cthulu codebase and generates:
- Code metrics (LOC, complexity, function counts)
- Dependency graphs
- Issue detection (oversized files, complexity warnings)
- JSON output for system map updates
- Performance bottleneck identification

Usage:
    python analyze_cthulu.py [--output report.json] [--verbose]
"""

import ast
import os
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys


@dataclass
class FileMetrics:
    """Metrics for a single Python file."""
    path: str
    name: str
    lines: int
    functions: int
    classes: int
    imports: List[str]
    complexity_score: int
    issues: List[str]
    dependencies: List[str]


@dataclass
class ModuleMetrics:
    """Metrics for a module/directory."""
    name: str
    path: str
    total_lines: int
    total_functions: int
    total_classes: int
    files: List[str]
    dependencies: Set[str]
    issues: List[str]
    complexity: str


class CodeAnalyzer:
    """Analyzes Python codebase for metrics and issues."""
    
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.file_metrics: Dict[str, FileMetrics] = {}
        self.module_metrics: Dict[str, ModuleMetrics] = {}
        self.global_imports: Set[str] = set()
        
        # Complexity thresholds
        self.LARGE_FILE_LINES = 1000
        self.VERY_LARGE_FILE_LINES = 1500
        self.MAX_FUNCTIONS_PER_FILE = 50
        self.HIGH_COMPLEXITY_THRESHOLD = 15
        
        # Directories to skip
        self.SKIP_DIRS = {
            '.git', '.venv', 'venv', '__pycache__', 'node_modules',
            '.archive', 'build', 'dist', '.pytest_cache'
        }
    
    def analyze(self) -> Dict:
        """Run full analysis on codebase."""
        print("🔍 Starting Cthulu codebase analysis...")
        
        # Scan all Python files
        python_files = self._find_python_files()
        print(f"📁 Found {len(python_files)} Python files")
        
        # Analyze each file
        for file_path in python_files:
            self._analyze_file(file_path)
        
        # Aggregate module metrics
        self._aggregate_modules()
        
        # Generate report
        report = self._generate_report()
        
        print("✅ Analysis complete!")
        return report
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the repository."""
        python_files = []
        for root, dirs, files in os.walk(self.root):
            # Remove skip directories from dirs in-place
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Count lines
            lines = len(content.splitlines())
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                # Skip files with syntax errors
                return
            
            # Count functions and classes
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    else:
                        if node.module:
                            imports.append(node.module)
            
            # Calculate complexity score (simple heuristic)
            complexity_score = self._calculate_complexity(tree, lines, len(functions))
            
            # Detect issues
            issues = self._detect_file_issues(file_path, lines, len(functions), complexity_score)
            
            # Extract internal dependencies
            dependencies = self._extract_dependencies(imports)
            
            # Store metrics
            relative_path = str(file_path.relative_to(self.root))
            self.file_metrics[relative_path] = FileMetrics(
                path=relative_path,
                name=file_path.name,
                lines=lines,
                functions=len(functions),
                classes=len(classes),
                imports=imports,
                complexity_score=complexity_score,
                issues=issues,
                dependencies=dependencies
            )
            
            # Track global imports
            self.global_imports.update(imports)
            
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _calculate_complexity(self, tree: ast.AST, lines: int, functions: int) -> int:
        """Calculate complexity score for a file."""
        # Count control flow statements
        control_flow = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                control_flow += 1
        
        # Simple scoring: lines/100 + functions/10 + control_flow/10
        score = (lines // 100) + (functions // 10) + (control_flow // 10)
        return score
    
    def _detect_file_issues(self, file_path: Path, lines: int, functions: int, complexity: int) -> List[str]:
        """Detect issues in a file."""
        issues = []
        
        if lines > self.VERY_LARGE_FILE_LINES:
            issues.append(f"CRITICAL: Very large file ({lines} lines) - needs refactoring")
        elif lines > self.LARGE_FILE_LINES:
            issues.append(f"WARNING: Large file ({lines} lines) - consider splitting")
        
        if functions > self.MAX_FUNCTIONS_PER_FILE:
            issues.append(f"WARNING: Many functions ({functions}) - consider modularization")
        
        if complexity > self.HIGH_COMPLEXITY_THRESHOLD:
            issues.append(f"WARNING: High complexity score ({complexity}) - needs simplification")
        
        # Check for TODO/FIXME
        try:
            with open(self.root / file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'TODO' in content or 'FIXME' in content:
                    issues.append("INFO: Contains TODO/FIXME markers")
        except:
            pass
        
        return issues
    
    def _extract_dependencies(self, imports: List[str]) -> List[str]:
        """Extract internal dependencies from imports."""
        internal_deps = []
        for imp in imports:
            # Extract top-level module name
            parts = imp.split('.')
            if parts:
                module = parts[0]
                # Check if it's an internal module (not stdlib or external)
                if module not in ['os', 'sys', 'ast', 'json', 're', 'pathlib', 'typing', 
                                  'collections', 'dataclasses', 'argparse', 'datetime',
                                  'pandas', 'numpy', 'MetaTrader5', 'd3', 'flask']:
                    internal_deps.append(module)
        
        return list(set(internal_deps))
    
    def _aggregate_modules(self):
        """Aggregate file metrics into module metrics."""
        modules = defaultdict(lambda: {
            'files': [],
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'dependencies': set(),
            'issues': []
        })
        
        for file_path, metrics in self.file_metrics.items():
            # Determine module name (top-level directory)
            parts = Path(file_path).parts
            if len(parts) > 1:
                module_name = parts[0]
            else:
                module_name = 'root'
            
            modules[module_name]['files'].append(file_path)
            modules[module_name]['total_lines'] += metrics.lines
            modules[module_name]['total_functions'] += metrics.functions
            modules[module_name]['total_classes'] += metrics.classes
            modules[module_name]['dependencies'].update(metrics.dependencies)
            modules[module_name]['issues'].extend(metrics.issues)
        
        # Convert to ModuleMetrics
        for module_name, data in modules.items():
            # Determine complexity
            avg_lines_per_file = data['total_lines'] / len(data['files']) if data['files'] else 0
            if avg_lines_per_file > 1000:
                complexity = "Very High"
            elif avg_lines_per_file > 500:
                complexity = "High"
            elif avg_lines_per_file > 200:
                complexity = "Medium"
            else:
                complexity = "Low"
            
            self.module_metrics[module_name] = ModuleMetrics(
                name=module_name,
                path=module_name,
                total_lines=data['total_lines'],
                total_functions=data['total_functions'],
                total_classes=data['total_classes'],
                files=data['files'],
                dependencies=data['dependencies'],
                issues=data['issues'][:5],  # Top 5 issues
                complexity=complexity
            )
    
    def _generate_report(self) -> Dict:
        """Generate comprehensive report."""
        # Count total metrics
        total_lines = sum(m.lines for m in self.file_metrics.values())
        total_functions = sum(m.functions for m in self.file_metrics.values())
        total_classes = sum(m.classes for m in self.file_metrics.values())
        
        # Find top issues
        all_issues = []
        for metrics in self.file_metrics.values():
            for issue in metrics.issues:
                all_issues.append({
                    'file': metrics.path,
                    'issue': issue,
                    'lines': metrics.lines,
                    'complexity': metrics.complexity_score
                })
        
        # Sort by severity
        critical_issues = [i for i in all_issues if 'CRITICAL' in i['issue']]
        warning_issues = [i for i in all_issues if 'WARNING' in i['issue']]
        
        # Find largest files
        largest_files = sorted(
            self.file_metrics.values(),
            key=lambda x: x.lines,
            reverse=True
        )[:10]
        
        # Find most complex files
        most_complex = sorted(
            self.file_metrics.values(),
            key=lambda x: x.complexity_score,
            reverse=True
        )[:10]
        
        # Generate dependency graph
        dependency_graph = self._build_dependency_graph()
        
        report = {
            'summary': {
                'total_files': len(self.file_metrics),
                'total_lines': total_lines,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'total_modules': len(self.module_metrics),
                'critical_issues': len(critical_issues),
                'warning_issues': len(warning_issues)
            },
            'modules': {
                name: asdict(metrics) 
                for name, metrics in self.module_metrics.items()
            },
            'top_issues': {
                'critical': critical_issues,
                'warnings': warning_issues[:10]
            },
            'largest_files': [
                {
                    'path': m.path,
                    'lines': m.lines,
                    'functions': m.functions,
                    'complexity': m.complexity_score
                }
                for m in largest_files
            ],
            'most_complex_files': [
                {
                    'path': m.path,
                    'lines': m.lines,
                    'functions': m.functions,
                    'complexity': m.complexity_score
                }
                for m in most_complex
            ],
            'dependency_graph': dependency_graph,
            'recommendations': self._generate_recommendations(critical_issues, warning_issues)
        }
        
        return report
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build module dependency graph."""
        graph = {}
        for module_name, metrics in self.module_metrics.items():
            graph[module_name] = list(metrics.dependencies)
        return graph
    
    def _generate_recommendations(self, critical_issues: List, warning_issues: List) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []
        
        if critical_issues:
            recommendations.append(
                f"URGENT: Address {len(critical_issues)} critical issues immediately. "
                "These files are too large and need refactoring."
            )
        
        if len(warning_issues) > 20:
            recommendations.append(
                f"HIGH PRIORITY: {len(warning_issues)} warnings detected. "
                "Consider technical debt cleanup sprint."
            )
        
        # Check for large modules
        large_modules = [m for m in self.module_metrics.values() if m.total_lines > 5000]
        if large_modules:
            recommendations.append(
                f"Consider splitting {len(large_modules)} large modules into smaller, "
                "more focused components."
            )
        
        return recommendations
    
    def print_summary(self, report: Dict):
        """Print analysis summary to console."""
        print("\n" + "="*70)
        print("📊 CTHULU CODEBASE ANALYSIS SUMMARY")
        print("="*70)
        
        summary = report['summary']
        print(f"\n📈 Overall Metrics:")
        print(f"   Total Files: {summary['total_files']}")
        print(f"   Total Lines: {summary['total_lines']:,}")
        print(f"   Total Functions: {summary['total_functions']:,}")
        print(f"   Total Classes: {summary['total_classes']:,}")
        print(f"   Total Modules: {summary['total_modules']}")
        
        print(f"\n⚠️  Issues Detected:")
        print(f"   Critical: {summary['critical_issues']}")
        print(f"   Warnings: {summary['warning_issues']}")
        
        if report['top_issues']['critical']:
            print(f"\n🔴 Top Critical Issues:")
            for issue in report['top_issues']['critical'][:5]:
                print(f"   • {issue['file']}")
                print(f"     {issue['issue']}")
        
        print(f"\n📏 Largest Files:")
        for f in report['largest_files'][:5]:
            print(f"   • {f['path']}: {f['lines']:,} lines, {f['functions']} functions")
        
        print(f"\n🧠 Most Complex Files:")
        for f in report['most_complex_files'][:5]:
            print(f"   • {f['path']}: complexity {f['complexity']}")
        
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze Cthulu codebase for metrics and issues'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='codebase_analysis.json',
        help='Output JSON file path'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--root',
        type=str,
        default='.',
        help='Root directory to analyze'
    )
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = CodeAnalyzer(args.root)
    report = analyzer.analyze()
    
    # Print summary
    analyzer.print_summary(report)
    
    # Save to JSON
    with open(args.output, 'w') as f:
        # Convert sets to lists for JSON serialization
        def convert_sets(obj):
            if isinstance(obj, set):
                return list(obj)
            return obj
        
        json.dump(report, f, indent=2, default=convert_sets)
    
    print(f"\n💾 Full report saved to: {args.output}")
    print(f"📊 Use this data to update system_map.html with latest metrics")


if __name__ == '__main__':
    main()
