@echo off
REM Windows Startup Script for Bluetooth Game Launcher
REM This script runs minimized in the background

REM Change this to your Python installation path if needed
REM Leave as "python" if Python is in your PATH
set PYTHON_EXE=python

REM Change this to the folder containing your game files
REM Example: C:\Users\YourName\Documents\BluetoothGame
set GAME_FOLDER=%~dp0

REM Navigate to game folder
cd /d "%GAME_FOLDER%"

REM Check if Python is available
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo Python not found! Please install Python or update PYTHON_EXE path.
    pause
    exit /b 1
)

REM Run the launcher (minimized, hidden console)
start /min "" %PYTHON_EXE% bluetooth_game_launcher.py

REM Exit this script (launcher will keep running in background)
exit