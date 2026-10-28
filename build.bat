@echo off
REM Tek tikla derleme: release\Rostek klasorunu hazirlar.
cd /d "%~dp0"
"venv\Scripts\python.exe" build_release.py
echo.
pause
