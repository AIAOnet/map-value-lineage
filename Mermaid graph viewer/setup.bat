@echo off
echo Installing the local Mermaid renderer...
cd /d "%~dp0"
call npm install
if errorlevel 1 (
  echo.
  echo Setup failed. Check that Node.js is installed and try again.
  pause
  exit /b 1
)
echo.
echo Setup complete. Start the viewer with run_viewer.bat.
pause
