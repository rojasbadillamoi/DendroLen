# Guía de distribución — DendroLen para Windows

## Resumen

Esta guía explica cómo empaquetar DendroLen en un ejecutable `.exe` para Windows usando **PyInstaller**. Se incluyen dos modalidades:

- **onedir** (carpeta): una carpeta con `DendroLen.exe` + DLLs. Inicio rápido (~2-3 s). Ideal para distribuir como `.zip`.
- **onefile** (archivo único): un solo `DendroLen.exe`. Más lento al iniciar (~5-10 s, descomprime a temp). Más fácil de compartir.

---

## Requisitos previos en Windows

1. **Python 3.10+** instalado desde [python.org](https://python.org)
   - Durante la instalación, marcar **"Add Python to PATH"**
2. **Git** (opcional, si vas a clonar el repo)

---

## Opción A: Build automático con script

Copiar todos los archivos `.py` del proyecto junto con los archivos de build a una carpeta, y ejecutar:

```cmd
cd C:\ruta\a\DendroLen
build_windows.bat
```

El ejecutable queda en `dist\DendroLen\DendroLen.exe`.

---

## Opción B: Build manual paso a paso

```cmd
REM 1. Crear entorno virtual
cd C:\ruta\a\DendroLen
python -m venv build_env
build_env\Scripts\activate

REM 2. Instalar dependencias
pip install PyQt6 matplotlib pyserial pandas numpy openpyxl pyinstaller

REM 3. Build onedir (recomendado)
pyinstaller DendroLen.spec --noconfirm

REM    — o build onefile —
pyinstaller DendroLen_onefile.spec --noconfirm
```

---

## Estructura de carpeta para el build

Antes de ejecutar PyInstaller, la carpeta debe contener:

```
DendroLen/
├── main_dendro.py
├── constantes.py
├── tema_manager.py
├── ventana_principal.py
├── dialogo_config.py
├── dialogo_nueva_muestra.py
├── dialogo_ayuda.py
├── panel_medicion.py
├── serial_worker.py
├── serie_maestra.py
├── tucson_writer.py
├── DendroLen.spec              ← archivo de build onedir
├── DendroLen_onefile.spec      ← archivo de build onefile
├── build_windows.bat           ← script automático
└── DendroLen.ico               ← (opcional) ícono de la app
```

---

## Ícono de la aplicación (opcional)

Si quieres un ícono personalizado para el `.exe`:

1. Crea una imagen de 256×256 px (PNG)
2. Conviértela a `.ico` usando un servicio online o con Python:

```python
from PIL import Image
img = Image.open("DendroLen.png")
img.save("DendroLen.ico", format="ICO", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
```

3. Coloca `DendroLen.ico` en la carpeta del proyecto. Los `.spec` lo detectan automáticamente.

---

## Distribución

### Como .zip (recomendado para onedir)

1. Comprimir toda la carpeta `dist\DendroLen\` en un `.zip`
2. El usuario descomprime y ejecuta `DendroLen.exe`
3. Tamaño estimado: ~80-120 MB comprimido

### Como instalador con Inno Setup (opcional, más profesional)

Si quieres un instalador `.exe` tipo "wizard" con acceso directo en el menú Inicio:

1. Descargar [Inno Setup](https://jrsoftware.org/isinfo.php) (gratis)
2. Usar el script `inno_setup.iss` incluido más abajo
3. Compilar → genera `DendroLen_Setup.exe`

---

## Problemas comunes y soluciones

### 1. "No module named 'serial'" o similar al ejecutar el .exe

El módulo no fue detectado por PyInstaller. Agregar a `hiddenimports` en el `.spec` y reconstruir.

### 2. El .exe se cierra inmediatamente sin mostrar nada

Construir temporalmente con `console=True` en el `.spec` para ver los errores:

```python
exe = EXE(
    ...
    console=True,   # ← cambiar temporalmente
)
```

### 3. matplotlib muestra ventana en blanco

Asegurar que `matplotlib.backends.backend_qtagg` está en `hiddenimports` (ya incluido en los spec).

### 4. El puerto serial no se detecta

El usuario necesita el driver del adaptador USB-serial instalado:
- **FTDI**: [ftdichip.com/drivers](https://ftdichip.com/drivers/)
- **CH340**: buscar "CH340 driver Windows"
- **CP210x**: [silabs.com/developers/usb-to-uart-bridge-vcp-drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)

### 5. Windows SmartScreen bloquea el .exe

Esto pasa porque el ejecutable no está firmado. Opciones:
- El usuario hace clic en "Más información" → "Ejecutar de todas formas"
- Firmar el ejecutable con un certificado de firma de código (costo ~$70-200/año)
- Distribuir con un instalador (Inno Setup) reduce la frecuencia de este aviso

### 6. Antivirus marca falso positivo

Común con PyInstaller. Soluciones:
- Subir el `.exe` a [VirusTotal](https://virustotal.com) para verificar que es falso positivo
- Reportar al proveedor de antivirus como falso positivo
- Usar `--onedir` (menos falsos positivos que `--onefile`)

---

## Script Inno Setup (opcional)

Guardar como `inno_setup.iss` y compilar con Inno Setup:

```iss
[Setup]
AppName=DendroLen
AppVersion=2.0.0
AppPublisher=MoiCedrus - Moisés E. Rojas Badilla
DefaultDirName={autopf}\DendroLen
DefaultGroupName=MoiCedrus
OutputBaseFilename=DendroLen_v2.0_Setup
Compression=lzma2/ultra64
SolidCompression=yes
; UninstallDisplayIcon={app}\DendroLen.exe

[Files]
Source: "dist\DendroLen\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\DendroLen"; Filename: "{app}\DendroLen.exe"
Name: "{commondesktop}\DendroLen"; Filename: "{app}\DendroLen.exe"

[Run]
Filename: "{app}\DendroLen.exe"; Description: "Iniciar DendroLen"; Flags: postinstall nowait
```

---

## Build para macOS y Linux (futuro)

### macOS
```bash
pyinstaller DendroLen.spec --noconfirm
# Genera dist/DendroLen/ — se puede empaquetar como .dmg con create-dmg
```

### Linux
```bash
pyinstaller DendroLen.spec --noconfirm
# Genera dist/DendroLen/ — distribuir como .tar.gz o crear AppImage
```

---

## Notas sobre pyserial en Windows

El acceso al puerto serial en Windows usa la API nativa de Windows a través de pyserial. Los nombres de puerto son `COM1`, `COM2`, etc. La función `listar_puertos()` en `serial_worker.py` ya maneja esto correctamente con `serial.tools.list_ports`, que funciona cross-platform.

La detección de tema del sistema en `constantes.py` usa `gsettings` (Linux) y `defaults` (macOS). En Windows ninguno de estos funciona, pero el fallback de PyQt6 (`palette().window().color().lightness()`) sí detecta correctamente el modo oscuro de Windows 10/11.
