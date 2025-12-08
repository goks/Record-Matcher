# Record Matcher - Quality Assurance Scripts

This directory contains automated quality assurance tools for the Record Matcher application.

## Scripts Overview

### 1. `quality_check.py`
Comprehensive static analysis tool that checks for:
- Import issues and deprecated libraries
- Error handling problems (bare excepts, silent failures)
- Security vulnerabilities (hardcoded credentials, pickle usage)
- Code style issues (string concatenation, line length)
- Resource management problems
- Threading issues (daemon threads, lack of thread pools)
- Documentation coverage
- Pandas usage inefficiencies
- Dependency issues

**Usage:**
```powershell
python quality_check.py
```

**Output:**
- Console report with detailed findings
- `quality_report.json` - Detailed JSON report

### 2. `run_quality_check.ps1`
PowerShell wrapper script for easy execution of quality checks.

**Usage:**
```powershell
.\run_quality_check.ps1
```

**Options:**
```powershell
.\run_quality_check.ps1 -Verbose      # Show detailed output
.\run_quality_check.ps1 -SaveReport   # Open report after generation
```

### 3. `test_suite.py`
Comprehensive unit and integration test suite covering:
- Validation functions (path, date, cheque number, amount)
- JSON data loading
- TableSnapshot operations
- Edge cases and boundary conditions
- Integration scenarios

**Usage:**
```powershell
python test_suite.py
```

## Quick Start

1. **Run Quality Check:**
   ```powershell
   .\run_quality_check.ps1
   ```

2. **Run Tests:**
   ```powershell
   python test_suite.py
   ```

3. **View Reports:**
   - Quality report: `quality_report.json`
   - Test results: Console output

## Integration with Development Workflow

### Before Committing Code
```powershell
# Run both quality check and tests
python quality_check.py
python test_suite.py
```

### Continuous Integration
Add to your CI/CD pipeline:
```yaml
- name: Quality Check
  run: python quality_check.py
  
- name: Run Tests
  run: python test_suite.py
```

## Understanding the Reports

### Quality Check Severity Levels
- 🔴 **CRITICAL**: Security issues, must fix immediately
- 🟠 **HIGH**: Major issues affecting stability/performance
- 🟡 **MEDIUM**: Important improvements needed
- 🟢 **LOW**: Minor style/documentation issues

### Common Issues Found

#### Security Issues
- Hardcoded credentials in source code
- Pickle usage (arbitrary code execution risk)
- Path injection vulnerabilities

#### Performance Issues
- Deprecated pandas.append() usage
- Inefficient pandas operations
- Resource leaks (Excel files not closed)

#### Code Quality Issues
- Bare except clauses
- Missing error handling
- Lack of documentation
- Print statements instead of logging

## Fixing Issues

### Priority Order
1. Fix all CRITICAL security issues
2. Fix HIGH severity issues (threading, resource management)
3. Fix MEDIUM issues (deprecated libraries, performance)
4. Address LOW issues (style, documentation)

### Example Fixes

**Before (Bare Except):**
```python
try:
    process_data()
except:
    pass
```

**After:**
```python
import logging

try:
    process_data()
except FileNotFoundError as e:
    logging.error(f"File not found: {e}")
except ValueError as e:
    logging.error(f"Invalid data: {e}")
```

**Before (Deprecated Pandas):**
```python
df = df.append(new_row, ignore_index=True)
```

**After:**
```python
df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
```

**Before (Daemon Thread):**
```python
x = threading.Thread(target=func, daemon=True)
x.start()
```

**After:**
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor() as executor:
    executor.submit(func)
```

## Extending the Tests

### Adding New Test Cases

```python
class TestNewFeature(unittest.TestCase):
    def test_feature_behavior(self):
        """Test description"""
        result = new_feature()
        self.assertEqual(result, expected_value)
```

### Adding New Quality Checks

```python
def check_new_pattern(self):
    """Check for new pattern"""
    for file_path in self.python_files:
        # Your check logic here
        if issue_found:
            self.issues['category'].append({
                'file': file_path.name,
                'line': line_number,
                'issue': 'Description',
                'severity': 'MEDIUM'
            })
```

## Troubleshooting

### Quality Check Fails to Run
- Ensure Python 3.7+ is installed
- Check all dependencies are installed: `pip install -r requirements.txt`
- Verify you're in the correct directory

### Tests Fail
- Check if `core.py` is accessible
- Ensure all required modules are installed
- Verify file paths are correct

### Permission Errors
- Run PowerShell as Administrator if needed
- Check file permissions on temp directories

## Future Improvements

- [ ] Add performance profiling
- [ ] Integrate with pre-commit hooks
- [ ] Add code coverage reporting
- [ ] Create automated fix suggestions
- [ ] Add more comprehensive integration tests
- [ ] Add load testing for large datasets

## Contact & Support

For issues or questions about these QA tools, refer to the main project documentation or create an issue in the repository.
