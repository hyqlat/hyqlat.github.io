# Local citation updater for hyqlat.github.io
# Usage (recommended): from repo root run
#   powershell -ExecutionPolicy Bypass -File .\google_scholar_crawler\run_local.ps1

# ====== EDIT THESE THREE VALUES ======
$GOOGLE_SCHOLAR_ID = "r533xwkAAAAJ"
$PROXY_URL         = "127.0.0.1:7897"    # Clash Verge default mixed port
$STATS_BRANCH      = "google-scholar-stats"
# =====================================

$ErrorActionPreference = "Stop"

try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function PauseExit([string]$msg, [string]$color) {
    Write-Host ""
    Write-Host $msg -ForegroundColor $color
    Write-Host ""
    Read-Host "Press Enter to exit" | Out-Null
    exit 1
}

# ---------- 1) Locate script directory ----------
$scriptPath = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptPath)) { $scriptPath = $MyInvocation.MyCommand.Path }
if ([string]::IsNullOrWhiteSpace($scriptPath)) { $scriptPath = $MyInvocation.MyCommand.Definition }
if ([string]::IsNullOrWhiteSpace($scriptPath)) { $scriptPath = $PSCommandPath }

if (-not [string]::IsNullOrWhiteSpace($scriptPath)) {
    # PSScriptRoot is already a directory; PSCommandPath is a file. Handle both.
    if (Test-Path -LiteralPath $scriptPath -PathType Leaf) {
        $scriptDir = Split-Path -Parent $scriptPath
    } else {
        $scriptDir = $scriptPath
    }
} else {
    $scriptDir = (Get-Location).Path
    Write-Host "[!] Script path unresolved, fallback to current directory" -ForegroundColor Yellow
}

if ([string]::IsNullOrWhiteSpace($scriptDir) -or -not (Test-Path -LiteralPath $scriptDir)) {
    PauseExit "[X] Cannot determine script directory. Run from repo root instead:" "Red"
}

# ---------- 2) Walk up to find git repo root ----------
$repoDir = $null
$cur = $scriptDir
for ($i = 0; $i -lt 6; $i++) {
    if (-not $cur) { break }
    if (Test-Path -LiteralPath (Join-Path $cur ".git")) { $repoDir = $cur; break }
    $parent = Split-Path -Parent $cur
    if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $cur) { break }
    $cur = $parent
}

if (-not $repoDir) {
    Write-Host ""
    Write-Host "[X] Git repo root not found" -ForegroundColor Red
    Write-Host "    Script dir : $scriptDir"
    Write-Host "    Searched upward for .git, nothing found."
    Write-Host "    Make sure this script lives INSIDE the hyqlat.github.io repo"
    Write-Host "    (e.g. google_scholar_crawler\) and the repo is a git checkout."
    Write-Host ""
    Read-Host "Press Enter to exit" | Out-Null
    exit 1
}

Write-Host "Script dir : $scriptDir"
Write-Host "Repo root  : $repoDir" -ForegroundColor Cyan

Set-Location -LiteralPath $repoDir

# ---------- 3) Validate required setting ----------
if ([string]::IsNullOrWhiteSpace($GOOGLE_SCHOLAR_ID) -or $GOOGLE_SCHOLAR_ID -eq "PUT_YOUR_SCHOLAR_ID_HERE") {
    PauseExit "[X] Please fill in GOOGLE_SCHOLAR_ID at line 7 of this script first" "Red"
}

# ---------- 4) Find Python ----------
$py = $null
foreach ($cand in @("python", "py", "python3")) {
    try {
        $null = & $cand --version 2>&1
        if ($LASTEXITCODE -eq 0) { $py = $cand; break }
    } catch {}
}
if (-not $py) { PauseExit "[X] Python not found. Please install Python 3.10+" "Red" }
Write-Host "Python     : $(& $py --version 2>&1)" -ForegroundColor Green

# ---------- 5) Check dependencies ----------
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Cyan
# 临时放宽错误处理：Python 把 traceback 写到 stderr 会被当成 terminating error
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$probe = & $py -c "import scholarly, bibtexparser" 2>&1
$probeCode = $LASTEXITCODE
$ErrorActionPreference = $prevEAP
if ($probeCode -ne 0) {
    Write-Host "Installing dependencies (first run takes 1-2 min)..." -ForegroundColor Yellow
    $req = Join-Path $scriptDir "requirements.txt"
    if (Test-Path -LiteralPath $req) {
        & $py -m pip install -r $req
    } else {
        & $py -m pip install "scholarly==1.7.11" "bibtexparser<2" "httpx<0.28" "requests[socks]"
    }
    if ($LASTEXITCODE -ne 0) { PauseExit "[X] Dependency install failed. Check network / pip mirror" "Red" }
}
Write-Host "Dependencies OK" -ForegroundColor Green

# ---------- 6) Check proxy port ----------
Write-Host ""
Write-Host "Checking proxy $PROXY_URL ..." -ForegroundColor Cyan
if ($PROXY_URL -match "^(.+):(\d+)$") {
    $hostPart = $Matches[1]
    $port = [int]$Matches[2]
    $tcp = New-Object System.Net.Sockets.TcpClient
    try {
        $iar = $tcp.BeginConnect($hostPart, $port, $null, $null)
        if (-not $iar.AsyncWaitHandle.WaitOne(3000)) {
            PauseExit "[X] Proxy port $PROXY_URL timed out. Is Clash Verge running with mixed port $port ?" "Red"
        }
        $tcp.EndConnect($iar)
        Write-Host "Proxy port reachable" -ForegroundColor Green
    } catch {
        PauseExit "[X] Cannot connect to $PROXY_URL . Open Clash Verge and check mixed port is $port" "Red"
    } finally { $tcp.Close() }
} else {
    Write-Host "[!] PROXY_URL should be host:port , port check skipped" -ForegroundColor Yellow
}

# ---------- 7) Run crawl ----------
$env:GOOGLE_SCHOLAR_ID = $GOOGLE_SCHOLAR_ID
$env:PROXY_URL         = $PROXY_URL
$env:STATS_BRANCH      = $STATS_BRANCH
$env:PYTHONIOENCODING  = "utf-8"
$env:REPO_DIR          = $repoDir

Write-Host ""
Write-Host "Start crawling..." -ForegroundColor Cyan
Write-Host "----------------------------------------"
& $py (Join-Path $scriptDir "update_citations.py") --push
$code = $LASTEXITCODE
Write-Host "----------------------------------------"

if ($code -eq 0) {
    Write-Host "DONE. Badge data updated." -ForegroundColor Green
} else {
    Write-Host "FAILED. See log above." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit" | Out-Null
