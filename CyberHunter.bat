@echo off
REM ============================================================
REM  Navy Games - Cyber Hunter Reawakening
REM  THE single entry point. Everything else runs behind this.
REM
REM  Server target is read from revival_config.env:
REM    REVIVAL_SERVER_IP=127.0.0.1  -> local mode  (servers start on this PC)
REM    REVIVAL_SERVER_IP=<vps ip>   -> remote mode (servers already run there)
REM ============================================================
title Navy Games - Cyber Hunter Reawakening

REM Admin is required: the client stack edits hosts, binds low ports and
REM injects Frida into client.exe.
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

if exist "%~dp0launcher.exe.new" (
    move /y "%~dp0launcher.exe.new" "%~dp0launcher.exe" >nul 2>&1
)
if exist "%~dp0CyberHunterLauncher.exe.new" (
    move /y "%~dp0CyberHunterLauncher.exe.new" "%~dp0CyberHunterLauncher.exe" >nul 2>&1
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
