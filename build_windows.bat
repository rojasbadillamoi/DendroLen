@echo off
REM =========================================================
REM  build_windows.bat -- Construir DendroLen (Modo Carpeta)
REM =========================================================

echo.
echo --- DendroLen Build para Windows (Modo Carpeta) ---
echo --- MoiCedrus - Moises E. Rojas Badilla ---
echo.

REM -- 1. Verificar Python --
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado en PATH.
    pause
    exit /b 1
)

REM -- 2. Crear entorno virtual --
if not exist "build_env" (
    echo [1/5] Creando entorno virtual de build...
    python -m venv build_env
) else (
    echo [1/5] Entorno virtual ya existe.
)

call build_env\Scripts\activate.bat

REM -- 3. Instalar dependencias --
echo [2/5] Instalando dependencias...
python -m pip install --upgrade pip
pip install PyQt6 matplotlib pyserial pandas numpy openpyxl pyinstaller

if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias. Revisa tu conexion a internet.
    pause
    exit /b 1
)

REM -- 4. Limpiar builds anteriores --
echo [3/5] Limpiando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist\DendroLen" rmdir /s /q dist\DendroLen
if exist "dist\DendroLen.exe" del /q "dist\DendroLen.exe"

REM -- 5. Construir --
echo [4/5] Construyendo con PyInstaller (Generando carpeta)...
pyinstaller DendroLen.spec --noconfirm

if errorlevel 1 (
    echo [ERROR] PyInstaller fallo.
    pause
    exit /b 1
)

REM -- 6. Verificar resultado --
echo [5/5] Verificando...
if exist "dist\DendroLen\DendroLen.exe" (
    echo.
    echo [EXITO] Build completado correctamente.
    echo El programa esta en la carpeta: dist\DendroLen\
    echo.
) else (
    echo [ERROR] No se encontro la carpeta generada.
)

pause