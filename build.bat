@echo off
REM Tek tikla derleme: release\Rostek klasorunu ve release\Rostek-<surum>.zip dosyasini hazirlar.
REM Surum adi sorulur; bos birakilirsa bugunun tarihi kullanilir.
cd /d "%~dp0"
set /p VERSION=Surum (ornek v1.0, bos = tarih):
"venv\Scripts\python.exe" build_release.py %VERSION%
echo.
pause
