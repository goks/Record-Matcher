# Quality Check Runner Script for Record Matcher
# PowerShell Script

param(
    [switch]$Verbose,
    [switch]$SaveReport,
    [switch]$FixStyle
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=".PadRight(79, '=') -ForegroundColor Cyan
Write-Host "RECORD MATCHER - AUTOMATED QUALITY CHECK RUNNER" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=".PadRight(79, '=') -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if Python is available
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $PythonVersion = python --version 2>&1
    Write-Host "  Found: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python 3.7 or higher" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Run quality check
Write-Host "Running quality checks..." -ForegroundColor Yellow
Write-Host ""

try {
    if ($Verbose) {
        python quality_check.py --verbose
    } else {
        python quality_check.py
    }
    
    $ExitCode = $LASTEXITCODE
    
    if ($ExitCode -eq 0) {
        Write-Host ""
        Write-Host "Quality check completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Quality check completed with warnings!" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR running quality check: $_" -ForegroundColor Red
    exit 1
}

# Check if report was generated
if (Test-Path "quality_report.json") {
    Write-Host ""
    Write-Host "Quality report generated: quality_report.json" -ForegroundColor Cyan
    
    # Display report summary
    $Report = Get-Content "quality_report.json" | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "Quick Summary:" -ForegroundColor Cyan
    Write-Host "  Files analyzed: $($Report.total_files)" -ForegroundColor White
    Write-Host "  Total issues:   $($Report.total_issues)" -ForegroundColor White
    
    if ($Report.total_issues -gt 0) {
        Write-Host ""
        Write-Host "Issue breakdown:" -ForegroundColor Cyan
        foreach ($category in $Report.issues.PSObject.Properties) {
            $count = $category.Value.Count
            if ($count -gt 0) {
                Write-Host "  - $($category.Name): $count" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host "=".PadRight(79, '=') -ForegroundColor Cyan
Write-Host ""

# Optional: Open report in default JSON viewer
if ($SaveReport -and (Test-Path "quality_report.json")) {
    Write-Host "Opening report..." -ForegroundColor Cyan
    Start-Process "quality_report.json"
}

exit $ExitCode
