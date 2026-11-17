@echo off
REM Genera PDF MASTER como programa de Windows (carpeta dist\PDF MASTER).
REM Ejecutar desde la carpeta del proyecto, con el entorno virtual activado o creado en .venv
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python -m PyInstaller --noconfirm --clean --windowed --name "PDF MASTER" --icon "assets\icons\app.ico" --add-data "assets;assets" main.py
echo.
echo Listo. Abre la carpeta dist\PDF MASTER y ejecuta "PDF MASTER.exe".
pause
