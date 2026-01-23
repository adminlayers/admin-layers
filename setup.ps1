# ============================================================================
# Genesys Cloud Utilities Suite - First Time Setup
# ============================================================================
#
# This script captures your Genesys Cloud credentials and stores them as
# persistent environment variables for future use.
#
# Run with: .\setup.ps1
# Run as Administrator for system-wide variables, or as user for user-only.
#
# ============================================================================

param(
    [switch]$Force,
    [switch]$SystemWide
)

$ErrorActionPreference = "Stop"

# ----------------------------------------------------------------------------
# Banner
# ----------------------------------------------------------------------------

Clear-Host
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Genesys Cloud Utilities Suite - First Time Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   This wizard will configure your Genesys Cloud credentials" -ForegroundColor Gray
Write-Host "   and store them securely as environment variables." -ForegroundColor Gray
Write-Host ""

# ----------------------------------------------------------------------------
# Check for existing credentials
# ----------------------------------------------------------------------------

$existingClientId = [System.Environment]::GetEnvironmentVariable("GENESYS_CLIENT_ID", "User")
if (-not $existingClientId) {
    $existingClientId = [System.Environment]::GetEnvironmentVariable("GENESYS_CLIENT_ID", "Machine")
}

if ($existingClientId -and -not $Force) {
    Write-Host "[!] Existing credentials detected" -ForegroundColor Yellow
    Write-Host "    Client ID: $($existingClientId.Substring(0, [Math]::Min(8, $existingClientId.Length)))..." -ForegroundColor Gray
    Write-Host ""
    $response = Read-Host "    Overwrite existing credentials? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host ""
        Write-Host "[OK] Setup cancelled. Existing credentials preserved." -ForegroundColor Green
        Write-Host "     Run with -Force to skip this prompt." -ForegroundColor Gray
        Write-Host ""
        exit 0
    }
    Write-Host ""
}

# ----------------------------------------------------------------------------
# Credential Input
# ----------------------------------------------------------------------------

Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "   Step 1: Enter Genesys Cloud Credentials" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   If you don't have credentials yet, request them from IT" -ForegroundColor Gray
Write-Host "   using the IT_ONBOARDING.md document in this folder." -ForegroundColor Gray
Write-Host ""

# Client ID
do {
    $clientId = Read-Host "   Client ID"
    $clientId = $clientId.Trim()
    if (-not $clientId) {
        Write-Host "   [!] Client ID is required" -ForegroundColor Red
    } elseif ($clientId.Length -lt 10) {
        Write-Host "   [!] Client ID appears too short" -ForegroundColor Red
        $clientId = ""
    }
} while (-not $clientId)

# Client Secret (masked input)
do {
    $secureSecret = Read-Host "   Client Secret" -AsSecureString
    $clientSecret = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureSecret)
    )
    $clientSecret = $clientSecret.Trim()
    if (-not $clientSecret) {
        Write-Host "   [!] Client Secret is required" -ForegroundColor Red
    } elseif ($clientSecret.Length -lt 10) {
        Write-Host "   [!] Client Secret appears too short" -ForegroundColor Red
        $clientSecret = ""
    }
} while (-not $clientSecret)

Write-Host ""

# ----------------------------------------------------------------------------
# Region Selection
# ----------------------------------------------------------------------------

Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "   Step 2: Select Genesys Cloud Region" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

$regions = @(
    @{ Index = 1;  Name = "US East (default)";    Domain = "mypurecloud.com" }
    @{ Index = 2;  Name = "US West";              Domain = "usw2.pure.cloud" }
    @{ Index = 3;  Name = "Canada";               Domain = "cac1.pure.cloud" }
    @{ Index = 4;  Name = "EU Ireland";           Domain = "mypurecloud.ie" }
    @{ Index = 5;  Name = "EU London";            Domain = "euw2.pure.cloud" }
    @{ Index = 6;  Name = "EU Frankfurt";         Domain = "mypurecloud.de" }
    @{ Index = 7;  Name = "Asia Pacific Sydney";  Domain = "mypurecloud.com.au" }
    @{ Index = 8;  Name = "Asia Pacific Tokyo";   Domain = "mypurecloud.jp" }
    @{ Index = 9;  Name = "Asia Pacific Seoul";   Domain = "apne2.pure.cloud" }
    @{ Index = 10; Name = "Asia Pacific Mumbai";  Domain = "aps1.pure.cloud" }
    @{ Index = 11; Name = "South America";        Domain = "sae1.pure.cloud" }
    @{ Index = 12; Name = "Middle East";          Domain = "mec1.pure.cloud" }
)

foreach ($region in $regions) {
    $prefix = if ($region.Index -lt 10) { " " } else { "" }
    Write-Host "   $prefix$($region.Index). $($region.Name)" -ForegroundColor Gray
    Write-Host "       $($region.Domain)" -ForegroundColor DarkGray
}

Write-Host ""

do {
    $regionInput = Read-Host "   Select region (1-12, default=1)"
    if (-not $regionInput) { $regionInput = "1" }

    $regionIndex = 0
    if ([int]::TryParse($regionInput, [ref]$regionIndex) -and $regionIndex -ge 1 -and $regionIndex -le 12) {
        $selectedRegion = $regions | Where-Object { $_.Index -eq $regionIndex }
    } else {
        Write-Host "   [!] Please enter a number between 1 and 12" -ForegroundColor Red
        $selectedRegion = $null
    }
} while (-not $selectedRegion)

$regionDomain = $selectedRegion.Domain

Write-Host ""
Write-Host "   Selected: $($selectedRegion.Name) ($regionDomain)" -ForegroundColor Green
Write-Host ""

# ----------------------------------------------------------------------------
# Storage Scope
# ----------------------------------------------------------------------------

Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "   Step 3: Storage Scope" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   1. Current User Only (recommended)" -ForegroundColor Gray
Write-Host "      Credentials available only to your Windows account" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   2. All Users (requires Administrator)" -ForegroundColor Gray
Write-Host "      Credentials available to all users on this computer" -ForegroundColor DarkGray
Write-Host ""

do {
    $scopeInput = Read-Host "   Select scope (1-2, default=1)"
    if (-not $scopeInput) { $scopeInput = "1" }

    if ($scopeInput -eq "1") {
        $scope = "User"
        $scopeName = "Current User"
    } elseif ($scopeInput -eq "2") {
        $scope = "Machine"
        $scopeName = "All Users"

        # Check for admin rights
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin) {
            Write-Host ""
            Write-Host "   [!] System-wide storage requires Administrator privileges" -ForegroundColor Red
            Write-Host "       Please run this script as Administrator, or choose option 1" -ForegroundColor Yellow
            $scope = $null
        }
    } else {
        Write-Host "   [!] Please enter 1 or 2" -ForegroundColor Red
        $scope = $null
    }
} while (-not $scope)

Write-Host ""

# ----------------------------------------------------------------------------
# Confirmation
# ----------------------------------------------------------------------------

Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "   Review Configuration" -ForegroundColor White
Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   Client ID:     $($clientId.Substring(0, [Math]::Min(8, $clientId.Length)))..." -ForegroundColor White
Write-Host "   Client Secret: ****" -ForegroundColor White
Write-Host "   Region:        $($selectedRegion.Name)" -ForegroundColor White
Write-Host "   Domain:        $regionDomain" -ForegroundColor White
Write-Host "   Storage:       $scopeName" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "   Save these credentials? (Y/n)"
if ($confirm -eq 'n' -or $confirm -eq 'N') {
    Write-Host ""
    Write-Host "[X] Setup cancelled." -ForegroundColor Yellow
    exit 1
}

# ----------------------------------------------------------------------------
# Save Credentials
# ----------------------------------------------------------------------------

Write-Host ""
Write-Host "[..] Saving credentials..." -ForegroundColor Gray

try {
    [System.Environment]::SetEnvironmentVariable("GENESYS_CLIENT_ID", $clientId, $scope)
    [System.Environment]::SetEnvironmentVariable("GENESYS_CLIENT_SECRET", $clientSecret, $scope)
    [System.Environment]::SetEnvironmentVariable("GENESYS_REGION", $regionDomain, $scope)

    # Also set for current session
    $env:GENESYS_CLIENT_ID = $clientId
    $env:GENESYS_CLIENT_SECRET = $clientSecret
    $env:GENESYS_REGION = $regionDomain

    Write-Host "[OK] Credentials saved successfully!" -ForegroundColor Green
} catch {
    Write-Host "[X] Failed to save credentials: $_" -ForegroundColor Red
    exit 1
}

# ----------------------------------------------------------------------------
# Verify Connection (optional)
# ----------------------------------------------------------------------------

Write-Host ""
$testConnection = Read-Host "   Test connection now? (Y/n)"

if ($testConnection -ne 'n' -and $testConnection -ne 'N') {
    Write-Host ""
    Write-Host "[..] Testing connection to Genesys Cloud..." -ForegroundColor Gray

    # Check for Python
    $pythonCmd = $null
    if (Get-Command python -ErrorAction SilentlyContinue) { $pythonCmd = "python" }
    elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $pythonCmd = "python3" }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $pythonCmd = "py" }

    if ($pythonCmd) {
        $testScript = @"
import sys
sys.path.insert(0, '.')
try:
    from genesys_cloud import GenesysAuth
    auth = GenesysAuth.from_config()
    if auth:
        success, message = auth.authenticate()
        if success:
            print("SUCCESS")
        else:
            print(f"FAILED:{message}")
    else:
        print("FAILED:Could not load configuration")
except Exception as e:
    print(f"FAILED:{e}")
"@

        $result = $testScript | & $pythonCmd - 2>&1

        if ($result -eq "SUCCESS") {
            Write-Host "[OK] Connection successful! Authenticated to Genesys Cloud." -ForegroundColor Green
        } else {
            $errorMsg = $result -replace "FAILED:", ""
            Write-Host "[!] Connection test failed: $errorMsg" -ForegroundColor Yellow
            Write-Host "    Credentials were saved. You can test again by running the app." -ForegroundColor Gray
        }
    } else {
        Write-Host "[!] Python not found. Skipping connection test." -ForegroundColor Yellow
        Write-Host "    Install Python and dependencies, then run start.ps1" -ForegroundColor Gray
    }
}

# ----------------------------------------------------------------------------
# Complete
# ----------------------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Your credentials are now stored as environment variables." -ForegroundColor Gray
Write-Host "   They will persist across reboots and terminal sessions." -ForegroundColor Gray
Write-Host ""
Write-Host "   Next steps:" -ForegroundColor White
Write-Host "   1. Close and reopen any terminal windows" -ForegroundColor Gray
Write-Host "   2. Run .\start.ps1 to launch the application" -ForegroundColor Gray
Write-Host ""
Write-Host "   To update credentials later, run: .\setup.ps1 -Force" -ForegroundColor DarkGray
Write-Host "   To remove credentials, run: .\uninstall.ps1" -ForegroundColor DarkGray
Write-Host ""

# Ask to start app
$startNow = Read-Host "   Start the application now? (Y/n)"
if ($startNow -ne 'n' -and $startNow -ne 'N') {
    Write-Host ""
    & "$PSScriptRoot\start.ps1"
}
