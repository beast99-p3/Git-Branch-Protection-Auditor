@echo off
REM GitHub Branch Protection Auditor - Quick Run Script
REM Usage: run_auditor.bat [basic|issues]

echo ================================================
echo  GitHub SOC 2 Branch Protection Auditor
echo ================================================

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it.
    echo.
    echo Required settings:
    echo   - GITHUB_ORG: Your GitHub organization name
    echo   - GITHUB_TOKEN: Personal Access Token with repo:read and read:org scopes
    echo.
    pause
    exit /b 1
)

REM Load environment variables from .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%b"=="" (
        set %%a=%%b
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Determine which script to run
if "%1"=="lite" (
    echo Running LITE auditor (legacy version)...
    echo.
    python github_auditor_lite.py
) else if "%1"=="personal" (
    echo Running PERSONAL auditor (legacy version)...
    echo.
    python github_auditor_personal.py
) else (
    echo Running UNIFIED auditor (auto-detects org/personal)...
    echo.
    python github_auditor.py
)

echo.
echo ================================================
echo  Audit Complete!
echo ================================================
pause
