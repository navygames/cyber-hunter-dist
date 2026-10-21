@echo off
title Navy Games - Cyber Hunter Reawakening

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Requesting Administrator privileges...
    powershell -NoProfile -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

if not exist "revival_config.env" (
    if exist "revival_config.env.example" (
        echo [*] First run - creating revival_config.env from the example.
        copy /Y "revival_config.env.example" "revival_config.env" >nul
    )
)

if exist "%~dp0launcher.exe" (
    start "" "%~dp0launcher.exe"
    exit /b
)

if exist "%~dp0CyberHunterLauncher.exe" (
    start "" "%~dp0CyberHunterLauncher.exe"
    exit /b
)

where pythonw >nul 2>&1
if errorlevel 1 (
    echo [!] Python was not found on PATH.
    echo     Install 64-bit Python 3.10+ ^(tick "Add to PATH"^), then:
    echo         pip install -r requirements.txt
    pause
    exit /b 1
)

cd /d "%~dp0Launcher"
start "" pythonw run_launcher.py
