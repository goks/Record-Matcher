# Quick Start Guide - Record Matcher v2

## ⚠️ IMPORTANT: Use the Virtual Environment!

The application **MUST** be run using the virtual environment to avoid dependency conflicts.

### Why?
- **System Python:** Has incompatible numpy 2.x (causes crashes)
- **Virtual Environment:** Has compatible pandas 1.3.1 + numpy 1.21.1 ✅

---

## Running the Application

### Method 1: Activate Virtual Environment (Recommended)

```powershell
# 1. Activate the virtual environment
.\RecordMatcher_env\Scripts\Activate.ps1

# 2. Run the application
python main.py

# 3. When done, deactivate
deactivate
```

### Method 2: Direct Execution (No Activation)

```powershell
# Run directly using venv Python
.\RecordMatcher_env\Scripts\python.exe main.py
```

---

## Common Issues

### Issue: `ValueError: numpy.dtype size changed`

**Cause:** Using system Python with incompatible numpy version

**Solution:** Use virtual environment as shown above

### Issue: `ModuleNotFoundError: No module named 'xlrd'`

**Cause:** Dependencies not installed in virtual environment

**Solution:**
```powershell
.\RecordMatcher_env\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: Application won't start

**Check:**
1. Are you using the virtual environment?
2. Is PySide2/Qt installed? `pip show PySide2`
3. Are all dependencies installed? `pip list`

---

## Development Setup

### Installing Dependencies

```powershell
# Activate virtual environment
.\RecordMatcher_env\Scripts\Activate.ps1

# Install all requirements
pip install -r requirements.txt

# Verify installation
python -c "import core; print('Success!')"
```

### Running Tests

```powershell
# Activate venv first
.\RecordMatcher_env\Scripts\Activate.ps1

# Run test suite
python test_suite.py

# Run quality check
python quality_check.py
```

### Running Quality Checks

```powershell
# Quality check (works with system Python - no dependencies)
python quality_check.py

# Pre-commit checks
.\pre_commit_check.ps1
```

---

## Virtual Environment Details

**Location:** `.\RecordMatcher_env\`

**Python Version:** 3.9.13

**Key Dependencies:**
- pandas==1.3.1 (compatible)
- numpy==1.21.1 (compatible)
- PySide2==5.15.2
- xlrd==1.2.0
- firebase-admin==5.0.0
- openpyxl==3.0.2

**Note:** Do NOT upgrade pandas or numpy without testing thoroughly!

---

## VS Code Configuration (Optional)

Add to `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}\\RecordMatcher_env\\Scripts\\python.exe",
    "python.terminal.activateEnvironment": true
}
```

This ensures VS Code uses the correct Python interpreter.

---

## Building Executable (Future)

When creating .exe with auto-py-to-exe or PyInstaller:

```powershell
# Activate venv first
.\RecordMatcher_env\Scripts\Activate.ps1

# Then use PyInstaller
pyinstaller main.spec
```

---

## Dependency Upgrade Plan (Future)

Current versions are **outdated** but **working**:

### Phase 1 - Critical Updates
1. pandas: 1.3.1 → 2.x (requires code changes for deprecated methods)
2. numpy: 1.21.1 → 1.26.x (compatible with pandas 2.x)
3. xlrd/xlwt → openpyxl (already installed, just need migration)

### Phase 2 - Security Updates
1. firebase-admin: 5.0.0 → latest
2. python-dateutil → latest
3. requests: 2.26.0 → latest

**See `suggestions.md` for complete upgrade roadmap.**

---

## Help & Support

**Documentation:**
- `README.md` - Application overview
- `CORE_FEATURES.md` - Feature documentation
- `suggestions.md` - Optimization roadmap
- `QA_README.md` - Quality assurance guide
- `CHANGELOG.md` - Change history

**Issue:** App won't run?
1. Check you're using virtual environment
2. Check `quality_report.json` for issues
3. Run `python -c "import core"` to test imports

**Need to reset environment?**
```powershell
# Delete and recreate venv
Remove-Item -Recurse -Force RecordMatcher_env
python -m venv RecordMatcher_env
.\RecordMatcher_env\Scripts\Activate.ps1
pip install -r requirements.txt
```
