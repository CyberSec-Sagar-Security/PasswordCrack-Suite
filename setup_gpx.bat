@echo off
REM GPX Setup Script for Windows
REM This script installs all GPU detection dependencies

echo ============================================
echo   PasswordCrack GPX Setup
echo   Installing GPU/CPU Detection Packages
echo ============================================
echo.

echo [1/3] Installing GPUtil (Cross-platform GPU detection)...
pip install gputil>=1.4.0
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install gputil
    pause
    exit /b 1
)
echo    ^>^> GPUtil installed successfully!
echo.

echo [2/3] Installing pynvml (NVIDIA GPU support)...
pip install pynvml>=11.5.0
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install pynvml
    pause
    exit /b 1
)
echo    ^>^> pynvml installed successfully!
echo.

echo [3/3] Installing psutil (System information)...
pip install psutil>=5.9.0
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install psutil
    pause
    exit /b 1
)
echo    ^>^> psutil installed successfully!
echo.

echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo Next steps:
echo   1. Run: python -m passwordcrack
echo   2. Click "Diagnostics" button to verify GPU detection
echo   3. Click "Rescan Devices" to detect your GPU
echo.
echo For troubleshooting, see: GPX_TROUBLESHOOTING.md
echo.

pause
