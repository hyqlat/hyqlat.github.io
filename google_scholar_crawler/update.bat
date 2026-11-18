@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM  Update Google Scholar citation data and push to stats branch
REM  Just double-click this file.
REM  Location: <repo>\google_scholar_crawler\update.bat
REM ============================================================

cd /d "%~dp0.."
echo [INFO] Repo root: %CD%
echo.

REM --- 1) Check working tree cleanliness ---
set DIRTY=
for /f "usebackq delims=" %%A in (`git status --porcelain`) do set DIRTY=1

if defined DIRTY (
    echo [WARN] Uncommitted changes detected:
    git status --short
    echo.
    echo [WARN] Commit or stash them first, then run again.
    echo        git add . ^&^& git commit -m "wip"
    echo     or git stash
    echo.
    pause
    exit /b 1
)

REM --- 2) Run the PowerShell updater ---
echo [INFO] Starting updater...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_local.ps1"
set RC=%ERRORLEVEL%

echo.
if "%RC%"=="0" (
    echo [OK] Done.
) else (
    echo [FAIL] Exit code = %RC%
)
echo.
pause
endlocal
