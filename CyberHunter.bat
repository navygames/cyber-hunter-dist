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

if exist "%~dp0CyberHunterLauncher.exe" (
    start "" "%~dp0CyberHunterLauncher.exe"
    exit /b
)
if exist "%~dp0launcher.exe" (
    start "" "%~dp0launcher.exe"
    exit /b
)
if exist "%~dp0Release\CyberHunterLauncher.exe" (
    start "" "%~dp0Release\CyberHunterLauncher.exe"
    exit /b
)
if exist "%~dp0Release\launcher.exe" (
    start "" "%~dp0Release\launcher.exe"
    exit /b
)
if exist "%~dp0Launcher\dist\CyberHunterLauncher.exe" (
    start "" "%~dp0Launcher\dist\CyberHunterLauncher.exe"
    exit /b
)
if exist "%~dp0Launcher\dist\launcher.exe" (
    start "" "%~dp0Launcher\dist\launcher.exe"
    exit /b
)

where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    cd /d "%~dp0Launcher"
    start "" pythonw run_launcher.py
    exit /b
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    cd /d "%~dp0Launcher"
    start "" python run_launcher.py
    exit /b
)

py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    cd /d "%~dp0Launcher"
    start "" py -3 run_launcher.py
    exit /b
)

REM Search well-known python installation paths
for %%P in (
    "C:\Python314\pythonw.exe"
    "C:\Python313\pythonw.exe"
    "C:\Python312\pythonw.exe"
    "C:\Python311\pythonw.exe"
    "C:\Python310\pythonw.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python314\pythonw.exe"
    "%ProgramFiles%\Python313\pythonw.exe"
    "%ProgramFiles%\Python312\pythonw.exe"
    "%ProgramFiles%\Python311\pythonw.exe"
    "%ProgramFiles%\Python310\pythonw.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if exist %%P (
        cd /d "%~dp0Launcher"
        start "" %%P run_launcher.py
        exit /b
    )
)

echo [!] Python was not found on PATH or standard directories.
echo     Install 64-bit Python 3.10+ (tick "Add to PATH"), then:
echo         pip install -r requirements.txt
pause
exit /b 1
