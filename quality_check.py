#!/usr/bin/env python
"""
Quality Check Automation Script for Record Matcher
Performs static analysis, code quality checks, and identifies issues
"""

import os
import sys
import ast
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Set

class CodeQualityChecker:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        self.python_files = []
        
    def run_all_checks(self):
        """Run all quality checks"""
        print("=" * 80)
        print("RECORD MATCHER - AUTOMATED QUALITY CHECK")
        print("=" * 80)
        print()
        
        # Discover Python files
        self._discover_python_files()
        
        # Run checks
        self.check_imports()
        self.check_error_handling()
        self.check_hardcoded_values()
        self.check_code_style()
        self.check_security_issues()
        self.check_resource_management()
        self.check_threading_issues()
        self.check_documentation()
        self.check_pandas_usage()
        self.check_dependencies()
        
        # Generate report
        self._generate_report()
        
    def _discover_python_files(self):
        """Find all Python files in the project"""
        print("Discovering Python files...")
        for file in self.root_dir.rglob("*.py"):
            # Skip virtual environment and cache directories
            if any(part in file.parts for part in ['RecordMatcher_env', '__pycache__', 'output', 'build', 'dist']):
                continue
            self.python_files.append(file)
        print(f"   Found {len(self.python_files)} Python files\n")
        
    def check_imports(self):
        """Check for import issues"""
        print("Checking imports...")
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(file_path))
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in ['pickle']:
                                self.issues['security'].append({
                                    'file': file_path.name,
                                    'line': node.lineno,
                                    'issue': f"Using pickle (security risk): {alias.name}",
                                    'severity': 'HIGH'
                                })
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and 'xlrd' in node.module or 'xlwt' in node.module:
                            self.issues['deprecated'].append({
                                'file': file_path.name,
                                'line': node.lineno,
                                'issue': f"Using deprecated library: {node.module}",
                                'severity': 'MEDIUM'
                            })
            except Exception as e:
                self.issues['parse_errors'].append({
                    'file': file_path.name,
                    'error': str(e)
                })
        
        print(f"   [OK] Import check complete\n")
        
    def check_error_handling(self):
        """Check for poor error handling practices"""
        print("Checking error handling...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(file_path))
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        # Check for bare except
                        if node.type is None:
                            self.issues['error_handling'].append({
                                'file': file_path.name,
                                'line': node.lineno,
                                'issue': "Bare except clause (catches all exceptions)",
                                'severity': 'HIGH'
                            })
                        # Check for pass in except
                        if (len(node.body) == 1 and 
                            isinstance(node.body[0], ast.Pass)):
                            self.issues['error_handling'].append({
                                'file': file_path.name,
                                'line': node.lineno,
                                'issue': "Silent exception handling (except: pass)",
                                'severity': 'HIGH'
                            })
            except Exception as e:
                pass
                
        print(f"   [OK] Error handling check complete\n")
        
    def check_hardcoded_values(self):
        """Check for hardcoded values that should be configurable"""
        print("Checking for hardcoded values...")
        
        patterns = [
            (r'HDFC Bank A/c No\.', 'Bank account number hardcoded'),
            (r'ICICI Bank A/c No\.', 'Bank account number hardcoded'),
            (r'recordmatcher-firebase-adminsdk', 'Firebase credentials path hardcoded'),
            (r'APPDATA.*\\\\Record Matcher', 'Hardcoded Windows path'),
            (r'\.xlsx|\.xls|\.fil', 'File extensions hardcoded'),
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    for pattern, description in patterns:
                        if re.search(pattern, line):
                            self.issues['hardcoded_values'].append({
                                'file': file_path.name,
                                'line': i,
                                'issue': description,
                                'severity': 'MEDIUM'
                            })
            except Exception as e:
                pass
                
        print(f"   [OK] Hardcoded values check complete\n")
        
    def check_code_style(self):
        """Check code style issues"""
        print("Checking code style...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    # Check for old-style string formatting
                    if re.search(r"'[^']*'\s*\+\s*\w+\s*\+\s*'", line) or \
                       re.search(r'"[^"]*"\s*\+\s*\w+\s*\+\s*"', line):
                        self.issues['code_style'].append({
                            'file': file_path.name,
                            'line': i,
                            'issue': "Use f-strings instead of string concatenation",
                            'severity': 'LOW'
                        })
                    
                    # Check for print statements (should use logging)
                    if re.search(r'^\s*print\(', line):
                        self.stats['print_statements'] += 1
                    
                    # Check line length
                    if len(line.rstrip()) > 120:
                        self.stats['long_lines'] += 1
                        
            except Exception as e:
                pass
                
        print(f"   [OK] Code style check complete\n")
        
    def check_security_issues(self):
        """Check for security vulnerabilities"""
        print("Checking security issues...")
        
        security_patterns = [
            (r'password\s*=\s*["\']', 'Hardcoded password found'),
            (r'pickle\.load', 'Pickle usage (arbitrary code execution risk)'),
            (r'os\.system', 'Using os.system (command injection risk)'),
            (r'eval\(', 'Using eval() (code injection risk)'),
            (r'exec\(', 'Using exec() (code injection risk)'),
        ]
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    for pattern, description in security_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.issues['security'].append({
                                'file': file_path.name,
                                'line': i,
                                'issue': description,
                                'severity': 'CRITICAL'
                            })
            except Exception as e:
                pass
                
        print(f"   [OK] Security check complete\n")
        
    def check_resource_management(self):
        """Check for resource management issues"""
        print("Checking resource management...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                # Check for file operations without context managers
                for i, line in enumerate(lines, 1):
                    if re.search(r'open\(.*\)', line) and 'with' not in line:
                        # Check if previous line has 'with'
                        if i > 1 and 'with' not in lines[i-2]:
                            self.issues['resource_management'].append({
                                'file': file_path.name,
                                'line': i,
                                'issue': "File opened without context manager (with statement)",
                                'severity': 'MEDIUM'
                            })
                    
                    # Check for workbook operations
                    if 'xlrd.open_workbook' in line or 'xlwt.Workbook' in line:
                        self.stats['excel_operations'] += 1
                        
            except Exception as e:
                pass
                
        print(f"   [OK] Resource management check complete\n")
        
    def check_threading_issues(self):
        """Check for threading problems"""
        print("Checking threading issues...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    # Check for daemon threads
                    if 'daemon=True' in line:
                        self.issues['threading'].append({
                            'file': file_path.name,
                            'line': i,
                            'issue': "Daemon thread usage (can cause data corruption)",
                            'severity': 'HIGH'
                        })
                    
                    # Check for threading.Thread without pool
                    if 'threading.Thread' in line:
                        self.stats['thread_creations'] += 1
                        
            except Exception as e:
                pass
                
        print(f"   [OK] Threading check complete\n")
        
    def check_documentation(self):
        """Check documentation coverage"""
        print("Checking documentation...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content, filename=str(file_path))
                    
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            self.stats['missing_docstrings'] += 1
                        else:
                            self.stats['has_docstrings'] += 1
                            
            except Exception as e:
                pass
                
        print(f"   [OK] Documentation check complete\n")
        
    def check_pandas_usage(self):
        """Check for inefficient pandas usage"""
        print("Checking pandas usage...")
        
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    # Check for deprecated append
                    if '.append(' in line and 'df' in line.lower():
                        self.issues['pandas'].append({
                            'file': file_path.name,
                            'line': i,
                            'issue': "Using deprecated DataFrame.append() - use pd.concat()",
                            'severity': 'MEDIUM'
                        })
                    
                    # Check for iterrows (usually inefficient)
                    if '.iterrows()' in line:
                        self.issues['pandas'].append({
                            'file': file_path.name,
                            'line': i,
                            'issue': "Using .iterrows() - consider vectorized operations",
                            'severity': 'LOW'
                        })
                        
            except Exception as e:
                pass
                
        print(f"   [OK] Pandas usage check complete\n")
        
    def check_dependencies(self):
        """Check requirements.txt for issues"""
        print("Checking dependencies...")
        
        req_file = self.root_dir / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Check for old pandas
                if 'pandas==0.24.2' in line:
                    self.issues['dependencies'].append({
                        'package': 'pandas',
                        'issue': 'Very outdated version (0.24.2 from 2019)',
                        'recommendation': 'Update to pandas>=2.0.0',
                        'severity': 'HIGH'
                    })
                
                # Check for xlrd/xlwt
                if 'xlrd' in line or 'xlwt' in line:
                    self.issues['dependencies'].append({
                        'package': line.split('==')[0],
                        'issue': 'Deprecated library for xlsx files',
                        'recommendation': 'Use openpyxl exclusively',
                        'severity': 'MEDIUM'
                    })
        else:
            self.issues['dependencies'].append({
                'issue': 'requirements.txt not found',
                'severity': 'LOW'
            })
            
        print(f"   [OK] Dependencies check complete\n")
        
    def _generate_report(self):
        """Generate and print the quality report"""
        print("\n" + "=" * 80)
        print("QUALITY CHECK REPORT")
        print("=" * 80)
        print()
        
        # Summary statistics
        print("[STATISTICS]")
        print("-" * 80)
        print(f"  Python files analyzed:      {len(self.python_files)}")
        print(f"  Print statements found:     {self.stats.get('print_statements', 0)}")
        print(f"  Long lines (>120 chars):    {self.stats.get('long_lines', 0)}")
        print(f"  Thread creations:           {self.stats.get('thread_creations', 0)}")
        print(f"  Excel operations:           {self.stats.get('excel_operations', 0)}")
        
        total_funcs = self.stats.get('has_docstrings', 0) + self.stats.get('missing_docstrings', 0)
        if total_funcs > 0:
            doc_coverage = (self.stats.get('has_docstrings', 0) / total_funcs) * 100
            print(f"  Documentation coverage:     {doc_coverage:.1f}%")
        print()
        
        # Issues by category
        total_issues = sum(len(issues) for issues in self.issues.values())
        print(f"[ISSUES FOUND]: {total_issues}")
        print("-" * 80)
        
        severity_order = {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3, 'LOW': 4}
        
        for category, issues_list in sorted(self.issues.items()):
            if not issues_list:
                continue
                
            print(f"\n[{category.upper().replace('_', ' ')}] ({len(issues_list)} issues)")
            print("   " + "-" * 76)
            
            # Sort by severity
            if isinstance(issues_list[0], dict) and 'severity' in issues_list[0]:
                issues_list = sorted(issues_list, 
                                   key=lambda x: severity_order.get(x.get('severity', 'LOW'), 5))
            
            # Show up to 10 issues per category
            for issue in issues_list[:10]:
                if isinstance(issue, dict):
                    severity = issue.get('severity', 'INFO')
                    file_name = issue.get('file', 'N/A')
                    line = issue.get('line', '?')
                    description = issue.get('issue', str(issue))
                    
                    severity_symbol = {
                        'CRITICAL': '[!]',
                        'HIGH': '[H]',
                        'MEDIUM': '[M]',
                        'LOW': '[L]'
                    }.get(severity, '[I]')
                    
                    print(f"   {severity_symbol} [{severity}] {file_name}:{line}")
                    print(f"      {description}")
            
            if len(issues_list) > 10:
                print(f"   ... and {len(issues_list) - 10} more issues")
        
        # Recommendations
        print("\n")
        print("[TOP RECOMMENDATIONS]")
        print("-" * 80)
        
        recommendations = []
        
        if self.issues.get('error_handling'):
            recommendations.append("1. Replace bare except clauses with specific exception handling")
        
        if self.issues.get('security'):
            recommendations.append("2. Address security issues immediately (pickle, hardcoded credentials)")
        
        if self.issues.get('threading'):
            recommendations.append("3. Replace daemon threads with proper thread management")
        
        if self.issues.get('pandas'):
            recommendations.append("4. Update pandas usage (replace append with concat)")
        
        if self.issues.get('deprecated'):
            recommendations.append("5. Replace deprecated libraries (xlrd/xlwt with openpyxl)")
        
        if self.stats.get('print_statements', 0) > 50:
            recommendations.append("6. Replace print statements with proper logging")
        
        if self.stats.get('missing_docstrings', 0) > 50:
            recommendations.append("7. Add docstrings to functions and classes")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {rec}")
        
        if not recommendations:
            print(f"  [OK] No major issues found!")
        
        print()
        print("=" * 80)
        print(f"Quality check complete! Total issues: {total_issues}")
        print("=" * 80)
        print()
        
        # Save report to file
        self._save_report_to_file(total_issues)
        
    def _save_report_to_file(self, total_issues):
        """Save detailed report to JSON file"""
        report_file = self.root_dir / 'quality_report.json'
        
        report_data = {
            'total_files': len(self.python_files),
            'total_issues': total_issues,
            'statistics': dict(self.stats),
            'issues': {k: v for k, v in self.issues.items()}
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"[REPORT] Detailed report saved to: {report_file}")
        print()


def main():
    """Main entry point"""
    # Get the script directory
    script_dir = Path(__file__).parent
    
    # Run quality checks
    checker = CodeQualityChecker(script_dir)
    checker.run_all_checks()
    
    # Exit with code based on critical issues
    critical_issues = len(checker.issues.get('security', []))
    if critical_issues > 0:
        print(f"[WARNING]: {critical_issues} critical security issues found!")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
