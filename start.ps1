# ============================================================================
# Genesys Cloud Utilities Suite - Startup Script
# ============================================================================
#
# This script starts the application. On first run, it will launch the
# setup wizard to configure credentials.
#
# Usage: .\start.ps1
#
# ============================================================================

param(
    [switch]$SkipSetup
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Streamlit settings
$env:STREAMLIT_SERVER_HEADLESS = "true"
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

# ----------------------------------------------------------------------------
# Banner
# ----------------------------------------------------------------------------

Clear-Host
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Genesys Cloud Utilities Suite" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------------------------
# First-Time Run Detection
# ----------------------------------------------------------------------------

# Check for credentials in persistent environment (not just current session)
$persistentClientId = [System.Environment]::GetEnvironmentVariable("GENESYS_CLIENT_ID", "User")
if (-not $persistentClientId) {
    $persistentClientId = [System.Environment]::GetEnvironmentVariable("GENESYS_CLIENT_ID", "Machine")
}

if (-not $persistentClientId -and -not $SkipSetup) {
    Write-Host "[!] First-time setup required" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   No Genesys Cloud credentials found." -ForegroundColor Gray
    Write-Host "   The setup wizard will help you configure your credentials." -ForegroundColor Gray
    Write-Host ""

    $runSetup = Read-Host "   Run setup wizard now? (Y/n)"

    if ($runSetup -ne 'n' -and $runSetup -ne 'N') {
        & "$scriptPath\setup.ps1"
        exit $LASTEXITCODE
    } else {
        Write-Host ""
        Write-Host "[!] Continuing without stored credentials." -ForegroundColor Yellow
        Write-Host "    You can enter credentials manually in the app." -ForegroundColor Gray
        Write-Host "    To run setup later: .\setup.ps1" -ForegroundColor Gray
        Write-Host ""
    }
} elseif ($persistentClientId) {
    # Load persistent credentials into current session if not already set
    if (-not $env:GENESYS_CLIENT_ID) {
        $env:GENESYS_CLIENT_ID = [System.Environment]::GetEnvironmentVariable("GENESYS_CLIENT_ID", "User")
        if (-not $env:GENESYS_CLIENT_ID) {
            $env:GENESYS_CLIENT_ID = [System.Environment]::GetEnvironmentVariable("GENESYS_CLIENT_ID", "Machine")
        }
    }
    if (-not $env:GENESYS_CLIENT_SECRET) {
        $env:GENESYS_CLIENT_SECRET = [System.Environment]::GetEnvironmentVariable("GENESYS_CLIENT_SECRET", "User")
        if (-not $env:GENESYS_CLIENT_SECRET) {
            $env:GENESYS_CLIENT_SECRET = [System.Environment]::GetEnvironmentVariable("GENESYS_CLIENT_SECRET", "Machine")
        }
    }
    if (-not $env:GENESYS_REGION) {
        $env:GENESYS_REGION = [System.Environment]::GetEnvironmentVariable("GENESYS_REGION", "User")
        if (-not $env:GENESYS_REGION) {
            $env:GENESYS_REGION = [System.Environment]::GetEnvironmentVariable("GENESYS_REGION", "Machine")
        }
    }

    Write-Host "[OK] Credentials loaded" -ForegroundColor Green
    $clientIdPreview = $env:GENESYS_CLIENT_ID.Substring(0, [Math]::Min(8, $env:GENESYS_CLIENT_ID.Length))
    Write-Host "     Client ID: $clientIdPreview..." -ForegroundColor Gray
    Write-Host "     Region: $($env:GENESYS_REGION)" -ForegroundColor Gray
    Write-Host ""
}

# ----------------------------------------------------------------------------
# Dependency Check
# ----------------------------------------------------------------------------

Write-Host "[..] Checking dependencies..." -ForegroundColor Gray

$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
}

if (-not $pythonCmd) {
    Write-Host "[X] Python not found. Please install Python 3.8+" -ForegroundColor Red
    Write-Host "    Download from: https://www.python.org/downloads/" -ForegroundColor Gray
    exit 1
}

# Check for streamlit
$streamlitCheck = & $pythonCmd -c "import streamlit" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Installing dependencies..." -ForegroundColor Yellow
    & $pythonCmd -m pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[OK] Dependencies ready" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------------------
# Start Application
# ----------------------------------------------------------------------------

Write-Host "[>>] Starting application..." -ForegroundColor Cyan
Write-Host "     URL: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "     Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host "     For help: .\help.ps1" -ForegroundColor Gray
Write-Host ""

# Run Streamlit
& $pythonCmd -m streamlit run app.py
