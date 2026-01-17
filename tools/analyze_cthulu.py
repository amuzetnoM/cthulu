#!/usr/bin/env python3
"""
Cthulu Code Analyzer - Automated System Analysis Tool

This tool scans the Cthulu codebase and generates:
- Code metrics (LOC, complexity, function counts)
- Dependency graphs
- Issue detection (oversized files, complexity warnings)
- JSON output for system map updates
- Performance bottleneck identification
- ML/RL component analysis

Usage:
    python analyze_cthulu.py [--output report.json] [--verbose]
"""

import ast
import os
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, asdict, field
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
    is_ml_component: bool = False
    ml_features: List[str] = field(default_factory=list)


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
    is_ml_module: bool = False


@dataclass
class MLComponentMetrics:
    """Metrics specifically for ML/RL components."""
    component_name: str
    component_type: str  # 'feature_pipeline', 'model', 'training', 'mlops'
    file_path: str
    features_count: int
    model_architecture: Optional[str]
    training_capabilities: List[str]
    dependencies: List[str]
    status: str  # 'implemented', 'partial', 'stub'


class CodeAnalyzer:
    """Analyzes Python codebase for metrics and issues."""
    
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.file_metrics: Dict[str, FileMetrics] = {}
        self.module_metrics: Dict[str, ModuleMetrics] = {}
        self.ml_components: Dict[str, MLComponentMetrics] = {}
        self.global_imports: Set[str] = set()
        
        # Complexity thresholds
        self.LARGE_FILE_LINES = 1000
        self.VERY_LARGE_FILE_LINES = 1500
        self.MAX_FUNCTIONS_PER_FILE = 50
        self.HIGH_COMPLEXITY_THRESHOLD = 15
        
        # Directories to skip
        self.SKIP_DIRS = {
            '.git', '.venv', 'venv', 'venv312', '__pycache__', 'node_modules',
            '.archive', 'build', 'dist', '.pytest_cache', 'site-packages',
            '.worktrees', 'worktrees', 'cthulu.worktrees'
        }
        
        # ML-related patterns for detection
        self.ML_PATTERNS = {
            'neural_network': ['forward', 'backward', 'relu', 'softmax', 'sigmoid', 'Q-Network', 'QNetwork'],
            'training': ['train', 'fit', 'epoch', 'batch', 'learning_rate', 'optimizer'],
            'feature_engineering': ['extract_features', 'FeaturePipeline', 'normalize', 'standardize'],
            'reinforcement_learning': ['Q-learning', 'PPO', 'epsilon', 'replay_buffer', 'reward'],
            'model_ops': ['registry', 'drift', 'retrain', 'versioning', 'MLOps'],
        }
        
        # Known ML modules
        self.ML_MODULES = {'ML_RL', 'cognition', 'training'}
    
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
        
        # Analyze ML components specifically
        self._analyze_ml_components()
        
        # Generate report
        report = self._generate_report()
        
        print("✅ Analysis complete!")
        return report
    
    def _analyze_ml_components(self):
        """Analyze ML/RL specific components."""
        ml_files = [
            f for f in self.file_metrics.values() 
            if f.is_ml_component or any(m in f.path for m in self.ML_MODULES)
        ]
        
        for metrics in ml_files:
            component = self._classify_ml_component(metrics)
            if component:
                self.ml_components[metrics.path] = component
    
    def _classify_ml_component(self, metrics: FileMetrics) -> Optional[MLComponentMetrics]:
        """Classify a file as an ML component."""
        path = metrics.path.lower()
        name = metrics.name.lower()
        
        # Determine component type
        if 'feature' in name or 'pipeline' in name:
            comp_type = 'feature_pipeline'
        elif 'rl' in name or 'position_sizer' in name or 'q_' in name:
            comp_type = 'reinforcement_learning'
        elif 'train' in name:
            comp_type = 'training'
        elif 'mlops' in name or 'registry' in name or 'drift' in name:
            comp_type = 'mlops'
        elif 'predict' in name or 'model' in name:
            comp_type = 'model'
        elif 'llm' in name or 'analysis' in name:
            comp_type = 'llm_analysis'
        else:
            comp_type = 'other'
        
        # Count features (heuristic based on class attributes)
        features_count = len(metrics.ml_features)
        
        # Determine model architecture
        architecture = None
        for feature in metrics.ml_features:
            if 'QNetwork' in feature or 'Q-Network' in feature:
                architecture = 'Q-Learning Network'
            elif 'PolicyNetwork' in feature:
                architecture = 'Policy Network (PPO)'
            elif 'Softmax' in feature:
                architecture = 'Softmax Classifier'
        
        # Determine training capabilities
        training_caps = []
        if any('train' in f.lower() for f in metrics.ml_features):
            training_caps.append('supervised_training')
        if any('replay' in f.lower() for f in metrics.ml_features):
            training_caps.append('experience_replay')
        if any('batch' in f.lower() for f in metrics.ml_features):
            training_caps.append('batch_training')
        
        # Determine status
        if metrics.functions > 5 and metrics.lines > 100:
            status = 'implemented'
        elif metrics.functions > 2:
            status = 'partial'
        else:
            status = 'stub'
        
        return MLComponentMetrics(
            component_name=metrics.name.replace('.py', ''),
            component_type=comp_type,
            file_path=metrics.path,
            features_count=features_count,
            model_architecture=architecture,
            training_capabilities=training_caps,
            dependencies=metrics.dependencies,
            status=status
        )
    
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
            ml_features = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                    # Check for ML-related functions
                    if any(p in node.name.lower() for p in ['train', 'predict', 'forward', 'backward', 'extract']):
                        ml_features.append(f"function:{node.name}")
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    # Check for ML-related classes
                    for pattern_name, patterns in self.ML_PATTERNS.items():
                        if any(p.lower() in node.name.lower() for p in patterns):
                            ml_features.append(f"class:{node.name}")
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    else:
                        if node.module:
                            imports.append(node.module)
            
            # Detect ML content in file
            is_ml = self._detect_ml_content(content, file_path, imports)
            
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
                dependencies=dependencies,
                is_ml_component=is_ml,
                ml_features=ml_features
            )
            
            # Track global imports
            self.global_imports.update(imports)
            
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _detect_ml_content(self, content: str, file_path: Path, imports: List[str]) -> bool:
        """Detect if file contains ML-related code."""
        # Check file path
        if any(m in str(file_path) for m in self.ML_MODULES):
            return True
        
        # Check imports
        ml_imports = ['numpy', 'sklearn', 'tensorflow', 'torch', 'pandas']
        if any(imp in imports for imp in ml_imports):
            return True
        
        # Check content patterns
        content_lower = content.lower()
        ml_keywords = ['neural', 'network', 'gradient', 'softmax', 'q-learning', 
                      'reinforcement', 'prediction', 'feature extraction',
                      'model training', 'epoch', 'batch_size']
        if any(kw in content_lower for kw in ml_keywords):
            return True
        
        return False
    
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
        
        # Generate ML analysis
        ml_analysis = self._generate_ml_analysis()
        
        report = {
            'summary': {
                'total_files': len(self.file_metrics),
                'total_lines': total_lines,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'total_modules': len(self.module_metrics),
                'critical_issues': len(critical_issues),
                'warning_issues': len(warning_issues),
                'ml_components': len(self.ml_components)
            },
            'modules': {
                name: asdict(metrics) 
                for name, metrics in self.module_metrics.items()
            },
            'ml_analysis': ml_analysis,
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
    
    def _generate_ml_analysis(self) -> Dict:
        """Generate detailed ML/RL analysis."""
        # Group by component type
        by_type = defaultdict(list)
        for path, comp in self.ml_components.items():
            by_type[comp.component_type].append(asdict(comp))
        
        # Count ML metrics
        ml_files = [f for f in self.file_metrics.values() if f.is_ml_component]
        total_ml_lines = sum(f.lines for f in ml_files)
        total_ml_functions = sum(f.functions for f in ml_files)
        
        # Identify architectures
        architectures = set()
        for comp in self.ml_components.values():
            if comp.model_architecture:
                architectures.add(comp.model_architecture)
        
        # Identify capabilities
        all_capabilities = set()
        for comp in self.ml_components.values():
            all_capabilities.update(comp.training_capabilities)
        
        return {
            'summary': {
                'total_ml_files': len(ml_files),
                'total_ml_lines': total_ml_lines,
                'total_ml_functions': total_ml_functions,
                'ml_architectures': list(architectures),
                'training_capabilities': list(all_capabilities)
            },
            'components_by_type': dict(by_type),
            'implementation_status': {
                'implemented': len([c for c in self.ml_components.values() if c.status == 'implemented']),
                'partial': len([c for c in self.ml_components.values() if c.status == 'partial']),
                'stub': len([c for c in self.ml_components.values() if c.status == 'stub'])
            }
        }
    
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
        
        # ML/RL Analysis
        if 'ml_analysis' in report:
            ml = report['ml_analysis']
            print(f"\n🤖 ML/RL Components:")
            print(f"   ML Files: {ml['summary']['total_ml_files']}")
            print(f"   ML Lines: {ml['summary']['total_ml_lines']:,}")
            print(f"   ML Functions: {ml['summary']['total_ml_functions']:,}")
            if ml['summary']['ml_architectures']:
                print(f"   Architectures: {', '.join(ml['summary']['ml_architectures'])}")
            if ml['summary']['training_capabilities']:
                print(f"   Capabilities: {', '.join(ml['summary']['training_capabilities'])}")
            print(f"\n   Implementation Status:")
            print(f"     ✅ Implemented: {ml['implementation_status']['implemented']}")
            print(f"     🔶 Partial: {ml['implementation_status']['partial']}")
            print(f"     ⬜ Stub: {ml['implementation_status']['stub']}")
            
            # List components by type
            if ml['components_by_type']:
                print(f"\n   Components by Type:")
                for comp_type, components in ml['components_by_type'].items():
                    print(f"     {comp_type}: {len(components)} files")
        
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
