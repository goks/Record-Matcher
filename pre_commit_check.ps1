# Pre-Commit Quality Gate Script
# Run this before committing code changes

param(
    [switch]$SkipTests,
    [switch]$Quick
)

$ErrorActionPreference = "Continue"
$script:FailCount = 0
$script:PassCount = 0

function Write-Status {
    param($Message, $Type = "Info")
    
    $symbols = @{
        "Pass" = "[OK]"
        "Fail" = "[FAIL]"
        "Info" = "[INFO]"
        "Warn" = "[WARN]"
    }
    
    $colors = @{
        "Pass" = "Green"
        "Fail" = "Red"
        "Info" = "Cyan"
        "Warn" = "Yellow"
    }
    
    Write-Host "$($symbols[$Type]) " -NoNewline -ForegroundColor $colors[$Type]
    Write-Host $Message
}

function Test-PythonSyntax {
    Write-Host ""
    Write-Host "=== Python Syntax Check ===" -ForegroundColor Cyan
    
    $pythonFiles = Get-ChildItem -Path . -Filter "*.py" -Recurse | 
        Where-Object { $_.FullName -notmatch "RecordMatcher_env|__pycache__|output|build" }
    
    $allValid = $true
    
    foreach ($file in $pythonFiles) {
        Write-Host "Checking $($file.Name)... " -NoNewline
        
        $result = python -m py_compile $file.FullName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK" -ForegroundColor Green
        } else {
            Write-Host "FAILED" -ForegroundColor Red
            Write-Host "  Error: $result" -ForegroundColor Red
            $allValid = $false
        }
    }
    
    if ($allValid) {
        Write-Status "All Python files have valid syntax" "Pass"
        $script:PassCount++
        return $true
    } else {
        Write-Status "Some Python files have syntax errors" "Fail"
        $script:FailCount++
        return $false
    }
}

function Test-CodeQuality {
    Write-Host ""
    Write-Host "=== Code Quality Check ===" -ForegroundColor Cyan
    
    if (Test-Path "quality_check.py") {
        python quality_check.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Quality check passed" "Pass"
            $script:PassCount++
            return $true
        } else {
            Write-Status "Quality check found critical issues" "Fail"
            $script:FailCount++
            return $false
        }
    } else {
        Write-Status "quality_check.py not found, skipping" "Warn"
        return $true
    }
}

function Test-UnitTests {
    if ($SkipTests) {
        Write-Status "Unit tests skipped (--SkipTests flag)" "Warn"
        return $true
    }
    
    Write-Host ""
    Write-Host "=== Unit Tests ===" -ForegroundColor Cyan
    
    if (Test-Path "test_suite.py") {
        python test_suite.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "All tests passed" "Pass"
            $script:PassCount++
            return $true
        } else {
            Write-Status "Some tests failed" "Fail"
            $script:FailCount++
            return $false
        }
    } else {
        Write-Status "test_suite.py not found, skipping" "Warn"
        return $true
    }
}

function Test-FileStructure {
    Write-Host ""
    Write-Host "=== File Structure Check ===" -ForegroundColor Cyan
    
    $requiredFiles = @(
        "main.py",
        "core.py",
        "requirements.txt",
        "data.json"
    )
    
    $allPresent = $true
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Host "  [OK] $file" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $file" -ForegroundColor Red
            $allPresent = $false
        }
    }
    
    if ($allPresent) {
        Write-Status "All required files present" "Pass"
        $script:PassCount++
        return $true
    } else {
        Write-Status "Some required files are missing" "Fail"
        $script:FailCount++
        return $false
    }
}

function Test-Dependencies {
    Write-Host ""
    Write-Host "=== Dependencies Check ===" -ForegroundColor Cyan
    
    if (Test-Path "requirements.txt") {
        Write-Host "Checking if all dependencies can be imported..."
        
        $testScript = @"
import sys
failed = []
try:
    import firebase_admin
except ImportError:
    failed.append('firebase_admin')
try:
    import openpyxl
except ImportError:
    failed.append('openpyxl')
try:
    import PySide2
except ImportError:
    failed.append('PySide2')
try:
    import pandas
except ImportError:
    failed.append('pandas')
try:
    import xlrd
except ImportError:
    failed.append('xlrd')
try:
    import xlwt
except ImportError:
    failed.append('xlwt')

if failed:
    print("MISSING: " + ", ".join(failed))
    sys.exit(1)
else:
    print("ALL OK")
    sys.exit(0)
"@
        
        $result = python -c $testScript 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Status "All required dependencies available" "Pass"
            $script:PassCount++
            return $true
        } else {
            Write-Status "Missing dependencies: $result" "Fail"
            Write-Host "  Run: pip install -r requirements.txt" -ForegroundColor Yellow
            $script:FailCount++
            return $false
        }
    } else {
        Write-Status "requirements.txt not found" "Warn"
        return $true
    }
}

function Test-SecurityIssues {
    Write-Host ""
    Write-Host "=== Security Scan ===" -ForegroundColor Cyan
    
    $issues = @()
    
    # Check for hardcoded passwords
    $passwordFiles = Get-ChildItem -Path . -Filter "*.py" -Recurse |
        Where-Object { $_.FullName -notmatch "RecordMatcher_env|__pycache__" } |
        Select-String -Pattern 'password\s*=\s*[''"]' -CaseSensitive:$false
    
    if ($passwordFiles) {
        $issues += "Hardcoded passwords found"
        foreach ($match in $passwordFiles) {
            Write-Host "  Found in: $($match.Filename):$($match.LineNumber)" -ForegroundColor Yellow
        }
    }
    
    # Check for API keys/secrets in code
    $secretFiles = Get-ChildItem -Path . -Filter "*.py" -Recurse |
        Where-Object { $_.FullName -notmatch "RecordMatcher_env|__pycache__" } |
        Select-String -Pattern "api[_-]?key|secret|token" -CaseSensitive:$false
    
    if ($secretFiles) {
        Write-Host "  Potential secrets in code (review required):" -ForegroundColor Yellow
        foreach ($match in $secretFiles | Select-Object -First 5) {
            Write-Host "    $($match.Filename):$($match.LineNumber)" -ForegroundColor Yellow
        }
    }
    
    if ($issues.Count -eq 0) {
        Write-Status "No obvious security issues found" "Pass"
        $script:PassCount++
        return $true
    } else {
        Write-Status "Security issues detected: $($issues -join ', ')" "Warn"
        return $true
    }
}

function Show-Summary {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "SUMMARY" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "Checks Passed: " -NoNewline
    Write-Host $script:PassCount -ForegroundColor Green
    
    Write-Host "Checks Failed: " -NoNewline
    Write-Host $script:FailCount -ForegroundColor $(if ($script:FailCount -gt 0) { "Red" } else { "Green" })
    
    Write-Host ""
    
    if ($script:FailCount -eq 0) {
        Write-Host "[OK] All checks passed! Code is ready to commit." -ForegroundColor Green
        return $true
    } else {
        Write-Host "[FAIL] Some checks failed. Please fix issues before committing." -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "RECORD MATCHER - PRE-COMMIT QUALITY GATE" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

$startTime = Get-Date

# Run all checks
Test-FileStructure
Test-PythonSyntax

if (-not $Quick) {
    Test-Dependencies
    Test-SecurityIssues
    Test-CodeQuality
    Test-UnitTests
} else {
    Write-Host ""
    Write-Host "Quick mode: Skipping detailed checks" -ForegroundColor Yellow
}

# Show summary
$success = Show-Summary

$elapsed = (Get-Date) - $startTime
$elapsedSeconds = [math]::Round($elapsed.TotalSeconds, 1)
Write-Host ""
Write-Host "Completed in $elapsedSeconds seconds" -ForegroundColor Cyan
Write-Host ""

# Exit with appropriate code
if ($success) {
    exit 0
} else {
    exit 1
}
