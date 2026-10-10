# DendroLen — Guía completa de empaquetado para Windows

## Resumen de entregables

Al final de este proceso tendrás dos distribuciones:

| Distribución | Archivo | Uso típico |
|---|---|---|
| **Portable** | `DendroLen_v2.0_Portable_Win64.zip` | USB, laboratorio, sin permisos admin |
| **Instalador** | `DendroLen_v2.0_Setup_Win64.exe` | Instalación permanente, menú Inicio, asociar .rwl |

---

## Paso 0 — Preparar la carpeta del proyecto

Crear una carpeta limpia con todos los archivos:

```
C:\DendroLen_build\
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
├── DendroLen.ico               ← ícono generado
├── DendroLen.spec              ← spec PyInstaller (onedir)
├── DendroLen_onefile.spec      ← spec PyInstaller (onefile, alternativo)
├── DendroLen_installer.iss     ← script Inno Setup
├── build_windows.bat           ← script automático de build
└── README.md
```

---

## Paso 1 — Instalar herramientas (una sola vez)

### Python 3.10+
- Descargar desde https://python.org
- **Marcar "Add Python to PATH"** durante la instalación

### Inno Setup 6 (solo si quieres el instalador)
- Descargar desde https://jrsoftware.org/isinfo.php
- Instalar con todas las opciones por defecto
- Incluir los packs de idioma (Spanish)

---

## Paso 2 — Construir el ejecutable con PyInstaller

### Opción automática

```cmd
cd C:\DendroLen_build
build_windows.bat
```

### Opción manual

```cmd
cd C:\DendroLen_build

REM Crear entorno virtual
python -m venv build_env
build_env\Scripts\activate

REM Instalar dependencias
pip install PyQt6 matplotlib pyserial pandas numpy openpyxl pyinstaller

REM Construir (modo onedir — recomendado)
pyinstaller DendroLen.spec --noconfirm
```

Al terminar, el ejecutable queda en `dist\DendroLen\DendroLen.exe`.

### Verificar que funciona

```cmd
dist\DendroLen\DendroLen.exe
```

La app debe abrir sin errores. El puerto serial no se va a detectar si no hay un carro conectado, pero la interfaz debe cargar completa.

---

## Paso 3a — Distribución portable (.zip)

Simplemente comprimir la carpeta `dist\DendroLen\`:

```cmd
REM Con PowerShell (incluido en Windows 10/11)
powershell Compress-Archive -Path dist\DendroLen\* -DestinationPath DendroLen_v2.0_Portable_Win64.zip
```

O clic derecho → "Comprimir en archivo ZIP" en el explorador.

El usuario descomprime y ejecuta `DendroLen.exe`. No necesita instalar nada.

---

## Paso 3b — Crear el instalador con Inno Setup

1. Abrir **Inno Setup Compiler** (se instaló en el Paso 1)
2. Menú File → Open → seleccionar `DendroLen_installer.iss`
3. Clic en **Build → Compile** (o Ctrl+F9)
4. El instalador se genera en `Output\DendroLen_v2.0_Setup_Win64.exe`

### Qué hace el instalador

- Wizard de instalación bilingüe (español/inglés)
- Instala en `C:\Program Files\DendroLen\` (o carpeta del usuario si no hay admin)
- Crea acceso directo en el menú Inicio bajo `MoiCedrus\DendroLen`
- Opción de crear acceso directo en el escritorio
- Opción de asociar archivos `.rwl` con DendroLen
- Desinstalador completo en "Agregar o quitar programas"
- Detecta instalaciones previas y ofrece desinstalar primero
- Compresión LZMA2 ultra (reduce ~40% el tamaño)

---

## Paso 4 — Probar en una máquina limpia

Esto es importante antes de distribuir. Idealmente probar en una PC que NO tenga Python instalado:

1. Verificar que el `.exe` o instalador funciona
2. Verificar que el tema oscuro/claro se detecta
3. Conectar un carro VRO y verificar detección del puerto serial
4. Cargar una serie maestra `.rwl` y verificar el panel de co-datación
5. Hacer una medición corta y guardar el `.rwl`

Si algo falla, construir temporalmente con `console=True` en el `.spec` para ver los errores.

---

## Estructura final de archivos para distribución

```
Releases/
├── DendroLen_v2.0_Portable_Win64.zip    (~80-120 MB comprimido)
├── DendroLen_v2.0_Setup_Win64.exe       (~60-90 MB con LZMA2)
└── README.md
```

---

## Notas sobre firma de código (opcional)

Sin firma digital, Windows SmartScreen mostrará una advertencia al ejecutar el instalador por primera vez. El usuario puede saltarla con "Más información → Ejecutar de todas formas".

Para evitar esto, necesitas un certificado de firma de código. Opciones:

- **SSL.com**: ~$70/año (el más económico para open source)
- **Sectigo/Comodo**: ~$80/año
- **SignPath.io**: gratis para proyectos open source alojados en GitHub

El proceso es: comprar certificado → recibes un archivo `.pfx` → firmar con:

```cmd
signtool sign /f certificado.pfx /p contraseña /tr http://timestamp.ssl.com /td sha256 DendroLen_v2.0_Setup_Win64.exe
```

Para un proyecto académico, la advertencia de SmartScreen es aceptable. La firma es un nice-to-have si el software se distribuye más ampliamente.

---

## Problemas frecuentes

### El .exe no abre / se cierra inmediatamente
Cambiar `console=False` a `console=True` en el `.spec`, reconstruir, y ejecutar desde CMD para ver el error.

### "Windows protected your PC" (SmartScreen)
Normal sin firma. Clic en "More info" → "Run anyway".

### Antivirus marca falso positivo
Común con PyInstaller. El modo `onedir` tiene menos falsos positivos que `onefile`. Reportar al proveedor de antivirus.

### El puerto serial no aparece
El usuario necesita el driver del adaptador USB: FTDI, CH340, o CP210x según su hardware.

### matplotlib muestra error de backend
Verificar que `matplotlib.backends.backend_qtagg` está en `hiddenimports` del `.spec`.
