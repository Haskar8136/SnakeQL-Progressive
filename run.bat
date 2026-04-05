@echo off
title SnakeQL-Progressive - Snake AI Trainer
color 0A

echo ================================================
echo    🐍 SnakeQL-Progressive - Snake AI Trainer
echo ================================================
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check Python version
python --version
echo.

REM Create folders
if not exist "pkl" mkdir pkl
if not exist "logs" mkdir logs

echo [OK] Folders ready
echo.

REM Show menu
:menu
cls
echo ================================================
echo                    MAIN MENU
echo ================================================
echo.
echo  1. Train Model
echo  2. Test Model (Demo Mode)
echo  3. List Available Models
echo  4. Clean Models
echo  0. Exit
echo.
set /p option="Select an option: "

if "%option%"=="1" goto train
if "%option%"=="2" goto demo
if "%option%"=="3" goto list
if "%option%"=="4" goto clean
if "%option%"=="0" goto exit
goto menu

:train
cls
echo ================================================
echo            Starting Trainer...
echo ================================================
python trainer.py
pause
goto menu

:demo
cls
echo ================================================
echo              Available Models:
echo ================================================
dir pkl\*.pkl 2>nul
echo.
set /p size="Enter board size (5x5, 10x10, 20x15): "
python play.py --size %size%
pause
goto menu

:list
cls
echo ================================================
echo              Available Models:
echo ================================================
dir pkl\*.pkl 2>nul
if errorlevel 1 (
    echo No models found.
)
echo.
pause
goto menu

:clean
cls
echo ================================================
echo              Clean Models
echo ================================================
dir pkl\*.pkl 2>nul
echo.
set /p confirm="Delete ALL models? (y/n): "
if /i "%confirm%"=="y" (
    del /q pkl\*.pkl 2>nul
    echo [OK] All models deleted.
) else (
    echo Cancelled.
)
pause
goto menu

:exit
echo.
echo Thanks for using SnakeQL-Progressive!
timeout /t 2 >nul
exit /b 0
