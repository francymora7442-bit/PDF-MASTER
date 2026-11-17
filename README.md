# PDF MASTER

Aplicación de escritorio para Windows (Python + PySide6) para gestionar PDF e imágenes **100 % en local**:
unir PDF, convertir JPG/PNG a PDF, organizar páginas visualmente e historial de archivos.

## Estructura
```
PDF_MASTER/
├── main.py                 # punto de entrada
├── requirements.txt
├── build_exe.bat           # genera el .exe con PyInstaller
├── assets/icons/           # app.png y app.ico
├── ui/                     # interfaz (PySide6)
│   ├── main_window.py  home.py  merge_pdf.py  jpg_to_pdf.py  png_to_pdf.py
│   ├── image_pdf_base.py  organize_pdf.py  history.py  settings.py
│   └── widgets.py  dialogs.py  styles.py
├── core/                   # lógica sin interfaz
│   ├── pdf_common.py  pdf_merger.py  image_converter.py  pdf_organizer.py
│   └── history_manager.py  settings_manager.py
├── utils/                  # file_manager.py  workers.py  image_utils.py
└── tools/generate_icon.py
```

## Instalación (Windows 10/11)
1. Instala Python 3.11 o 3.12 (64 bits) desde https://www.python.org/downloads/ y marca **Add python.exe to PATH**.
2. Abre la carpeta `PDF_MASTER` en Visual Studio Code (Archivo → Abrir carpeta).
3. Abre la terminal integrada: menú Terminal → Nueva terminal (`Ctrl + ñ`). Debe ser **PowerShell**.
4. Copia y pega, línea por línea:
```
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```
Si PowerShell bloquea la activación: ejecuta `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repite la línea `.venv\Scripts\Activate.ps1`.

## Crear el .exe
Con el entorno virtual activado:
```
.\build_exe.bat
```
o manualmente:
```
python -m PyInstaller --noconfirm --clean --windowed --name "PDF MASTER" --icon "assets\icons\app.ico" --add-data "assets;assets" main.py
```
El programa queda en `dist\PDF MASTER\PDF MASTER.exe` (doble clic). Copia **toda** la carpeta `dist\PDF MASTER` donde quieras.
(Opcional, un solo archivo: añade `--onefile`; arranca más lento.)

## Datos de la aplicación
Historial y configuración se guardan en `%APPDATA%\PDF_MASTER\` (`history.json`, `config.json`).

## Problemas frecuentes
| Error | Solución |
|---|---|
| `python no se reconoce como comando` | Reinstala Python marcando *Add to PATH* y reabre VS Code. |
| `ModuleNotFoundError: PySide6` / `fitz` | El entorno no está activo: `.venv\Scripts\Activate.ps1` y `pip install -r requirements.txt`. |
| No se puede ejecutar scripts (Activate.ps1) | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| El .exe no abre / se cierra | Compila sin `--windowed` para ver el error en consola. |
| Antivirus bloquea el .exe | Es habitual con PyInstaller; añade una excepción a la carpeta `dist`. |
| «No se pudo guardar» | El PDF de destino está abierto en otro programa; ciérralo o cambia el nombre. |
