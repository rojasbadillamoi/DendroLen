# 🌲 DendroLen v2.1

**Aplicación de escritorio para medición de anillos de árboles en tiempo real con carro de medición USB-serial.**

Desarrollada por **Moisés E. Rojas Badilla** como parte de la suite **MoiCedrus**.

---

## Descripción

DendroLen es una herramienta especializada para dendrocronólogos que permite medir anchos de anillos de árboles en tiempo real mediante un carro de medición VRO conectado por puerto USB-serial. Las mediciones se exportan directamente al formato estándar Tucson (`.rwl`), compatible con COFECHA, ARSTAN, dplR y el resto del ecosistema dendrocronológico.

Incluye un módulo de co-datación en vivo con serie maestra, que calcula y visualiza la correlación entre la serie que se está midiendo y una cronología de referencia, actualizado en tiempo real a medida que avanza la medición.

---

## Características principales

### Medición y captura

- **Medición en tiempo real** mediante carro VRO con comunicación USB-serial
- **Detección automática de adaptadores USB-serial** (FTDI, CH340, CP210x), excluyendo Bluetooth
- **Unidades configurables** del carro: 0.001 mm (µm) o 0.01 mm
- **Detección automática de reset/retroceso** del encoder con resincronización sin pérdida de datos
- **Edición en caliente** del año de inicio y código de serie durante la medición
- **Mediciones recientes**: panel que escanea archivos `.rwl` de la carpeta y permite retomar sesiones previas con un clic
- **Señales auditivas no bloqueantes** diferenciadas por evento (medición, década, guardado), con implementación nativa por sistema operativo

### Co-datación en vivo

- **Correlación global (r de Pearson)** sobre diferencias logarítmicas, método estándar COFECHA (Holmes 1983)
- **Correlación deslizante** en ventanas configurables (5, 10, 15, 20, 30, 50, 100 años)
- **Visualización superpuesta** de la serie en medición y la maestra, con normalización z-score automática cuando hay solape ≥ 5 años
- **Fondos coloreados por calidad** de cada segmento (verde oscuro/claro, naranja, rojo según umbrales de r)
- **Zoom interactivo** con rueda del mouse, doble clic para autorange
- **Formatos de serie maestra soportados**: Tucson (`.rwl`, `.txt`), CooRecorder (`.wid`), Excel (`.xlsx`, `.xls`), CSV

### Cronologías

- **Construcción de cronologías estandarizadas** sin salir del programa, en sus tres variantes: cruda, estándar y residual
- **Métodos de ajuste**: spline de Cook y Peters (rigidez configurable, 32 años por defecto), exponencial negativa, recta, media móvil y media
- **Agregación por media biponderada** de Tukey
- **Mismo núcleo numérico que DPI**: ambos programas entregan los mismos índices y las mismas correlaciones, verificado hasta 1×10⁻¹¹ en valor relativo

### Edición durante la medición

- **Insertar y eliminar anillos** en cualquier posición de la serie
- **Desplazar la serie completa** en el tiempo, sin reiniciar la sesión
- **Retomar una muestra existente**: el asistente abre un archivo ya medido, lee su sidecar de anomalías y precarga los datos

### Registro de anomalías

Marcado directo durante la medición mediante teclas de función. Cada anomalía se asigna al último anillo medido y funciona como toggle:

- **Frost ring** (FR), **Light ring** (LR), **Anillo falso** (AF), **Missing ring** (MR)
- **Fuego** (FU), **Golpe** (GO), **Otro** (OT)

Las anomalías se exportan en un sidecar `.rwl.anom.json` con metadatos completos de la muestra (año de médula, corteza, especie) y eventos indexados por año y por tipo.

### Exportación y persistencia

- **Formato Tucson estándar ITRDB** (`.rwl`): primera línea parcial cuando el año no es múltiplo de 10, alineación a década, valores en campos de 6 caracteres, terminador `-9999`
- **Persistencia de ruta**: la última carpeta usada se abre por defecto en sesiones futuras
- **Guardado automático al pausar** para protección contra pérdida de datos
- **Unión de archivos integrada (DendroUnir)**: combinar múltiples `.rwl` con detección de duplicados y tres estrategias de resolución (renombrar, mantener primero, promediar). Exporta a `.rwl`, Excel, o ambos

### Interfaz

- **Temas oscuro y claro** con detección automática del tema del sistema operativo (GNOME, KDE, macOS, Windows)
- **Tamaño de fuente adaptable** a la resolución de pantalla
- **Paneles redimensionables** mediante splitters horizontales y verticales
- **Botones adaptativos**: texto completo en ventanas anchas, solo ícono en pantallas estrechas
- **Tipografía monoespaciada** (JetBrains Mono / Fira Mono / DejaVu Sans Mono) para alineación correcta de datos Tucson
- **Splash screen** con progreso de carga durante el arranque

### Multiplataforma

- **Linux**: Ubuntu 22.04+ y derivadas
- **macOS**: compatible nativamente
- **Windows 10/11**: distribución como ejecutable portable (`.zip`) o instalador profesional (`.exe`), sin requerir Python instalado

---

## Requisitos

- Python 3.10 o superior
- Linux, macOS o Windows

### Dependencias Python

```bash
pip install -r requirements.txt
```

### Hardware

- Carro de medición con encoder VRO y salida USB-serial (adaptador FTDI, CH340, CP210x o similar)
- Puerto USB-A o USB-C disponible

---

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/rojasbadillamoi/DendroLen.git
cd DendroLen

# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate    # Linux/macOS
# venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python3 main_dendro.py
```

### Script de lanzamiento (Linux/macOS)

Para tener un acceso directo, crea un archivo `DendroLen.sh`:

```bash
#!/bin/bash
cd "/ruta/a/DendroLen"
source venv/bin/activate
python3 main_dendro.py
```

```bash
chmod +x DendroLen.sh
./DendroLen.sh
```

---

## Estructura del proyecto

```
DendroLen/
├── main_dendro.py              # Punto de entrada, verificación de dependencias
├── constantes.py               # Parámetros globales, especies, anomalías, temas
├── tema_manager.py             # Gestor de tema oscuro/claro (singleton)
├── ventana_principal.py        # Ventana principal, navegación entre pantallas
├── dialogo_config.py           # Pantalla 1: asistente de configuración
├── dialogo_nueva_muestra.py    # Modal de nueva muestra
├── dialogo_ayuda.py            # Modal de atajos de teclado
├── panel_medicion.py           # Pantalla 2: panel de medición en tiempo real
├── serial_worker.py            # Hilo QThread de lectura del puerto serie
├── serie_maestra.py            # Panel de co-datación con serie maestra
├── tucson_writer.py            # Escritura de archivos Tucson y sidecar JSON
├── cronologia.py               # Estandarización y construcción de cronologías
└── modulo_unir.py              # Módulo integrado de unión de archivos .rwl
```

---

## Uso rápido

### 1. Configurar la sesión

Al iniciar el programa aparece el asistente de configuración:

- **Código de muestra**: identificador de la serie (ej. `CHI001A`). Hasta 8 caracteres conforme al estándar Tucson.
- **Año de inicio**: año del primer anillo medido (médula). Rango: −10.000 a 2.200 (incluye series subfósiles).
- **Especie**: selecciona de la lista o escribe libremente. Las especies agregadas se guardan persistentemente para sesiones futuras.
- **Puerto serie**: se detecta automáticamente. Usa el botón ⟳ para refrescar.
- **Velocidad (baud)**: 9600 por defecto (VRO estándar).
- **Unidades del carro**: 0.001 mm (µm) o 0.01 mm según el modelo del encoder.
- **Archivo de salida**: nombre del archivo `.rwl`. El programa preguntará dónde guardarlo al primer guardado.

### 2. Fijar la referencia

Una vez conectado el carro, colócalo en la posición de inicio (médula) y **presiona el botón del carro** para fijar la referencia. El programa mostrará el mensaje de confirmación en el registro.

### 3. Medir

Desplaza el carro hacia la corteza. Cada vez que el encoder registra un nuevo anillo, aparece automáticamente en:
- La barra de información superior (último valor, año actual, n° anillos, promedio, contador de anomalías)
- El registro de medición con timestamps
- La vista previa Tucson en vivo
- El gráfico de co-datación

### 4. Guardar

| Acción | Atajo | Descripción |
|--------|-------|-------------|
| Guardar y continuar | `Ctrl+G` | Guarda el archivo y sigue midiendo |
| Guardar y cerrar radio | `Ctrl+S` | Guarda y vuelve al asistente |

El primer guardado abre un explorador para elegir la ubicación. Los siguientes guardados usan la misma ruta.

---

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `Ctrl+G` | Guardar y continuar midiendo |
| `Ctrl+S` | Guardar y cerrar radio |
| `Ctrl+Z` | Deshacer / remedir el último anillo |
| `Ctrl+P` | Pausar / reanudar recepción del carro |
| `Ctrl+Y` | Editar año de inicio en caliente |
| `F1` | Mostrar ayuda (tabla de atajos) |
| `F2` | Marcar Frost ring (FR) |
| `F3` | Marcar Light ring (LR) |
| `F4` | Marcar Anillo falso (AF) |
| `F5` | Marcar Missing ring (MR) |
| `F6` | Marcar Fuego (FU) |
| `F7` | Marcar Golpe (GO) |
| `F8` | Marcar Otro (OT) |
| `F9` | Reconectar puerto serie |

> Las anomalías se marcan sobre el **último anillo medido** y funcionan como toggle: presionar la misma tecla nuevamente elimina la marca.

---

## Archivos generados

### Archivo Tucson (`.rwl`)

Formato estándar con identificador de 8 caracteres, año de 4 dígitos y valores en milésimas de mm, 10 valores por línea, terminado en `-9999`. Compatible con COFECHA, ARSTAN, dplR y cualquier software dendrocronológico estándar.

### Sidecar de anomalías (`.rwl.anom.json`)

Generado automáticamente al registrar anomalías. Estructura:

```json
{
  "CHI001A": {
    "anio_medula": 1750,
    "anio_corteza": 2023,
    "especie": "Nothofagus obliqua",
    "eventos": {
      "1816": "FR",
      "1960": "LR"
    },
    "eventos_por_tipo": {
      "FR": [1816],
      "LR": [1960]
    }
  }
}
```

---

## Co-datación en vivo

El panel de co-datación (parte inferior de la pantalla de medición) muestra:

- **Curva azul**: serie en construcción (normalizada z-score cuando hay solape ≥ 5 años)
- **Curva naranja punteada**: serie maestra de referencia
- **Fondos coloreados por correlación deslizante**:
  - 🟢 Verde oscuro: r ≥ 0.50
  - 🟢 Verde claro: r ≥ 0.35
  - 🟡 Naranja: r ≥ 0.15
  - 🔴 Rojo: r < 0.15
- **Etiquetas r=**: valor de correlación al fondo de cada segmento
- **Barra inferior**: r global, símbolo de calidad (●●●), y r por ventanas temporales

---

## Notas técnicas

- Las mediciones se almacenan internamente en **milésimas de mm** (enteros), igual que el formato Tucson original
- La correlación usa **diferencias logarítmicas** (método estándar COFECHA, Holmes 1983)
- La normalización z-score se aplica automáticamente cuando hay solape ≥ 5 años
- El lector Tucson acepta años en el rango −10.000 a 2.200 para series subfósiles
- La detección de puerto prioriza adaptadores USB-serial e incluye verificación por `hwid`

---

## Cómo citar

Si usas DendroLen en una publicación científica, por favor cítalo así:

> Rojas Badilla, M. E. (2026). *DendroLen* [Software]. Zenodo. https://doi.org/10.5281/zenodo.20616206

Ese DOI es el **de concepto**: apunta siempre a la versión más reciente, así que no hay que cambiarlo al publicar una versión nueva. Si necesitas citar una versión exacta, usa el DOI de esa versión, que Zenodo muestra en la página del registro.

El archivo `CITATION.cff` del repositorio contiene los metadatos completos para gestores de referencias bibliográficas. GitHub también provee la cita en formato APA y BibTeX mediante el botón "Cite this repository" en la barra lateral del repositorio.

---

## Suite MoiCedrus

DendroLen forma parte de **MoiCedrus**, una suite de herramientas dendrocronológicas open source desarrolladas en Python/PyQt6 para investigadores y estudiantes:

- **[Dendro Pixel Interface (DPI)](https://github.com/rojasbadillamoi/DPI)** — Medición y co-fechado de anillos a partir de imágenes escaneadas
- **DendroEventos** — Análisis de eventos cambiales (en desarrollo)
- **RetroClimex** — Función de respuesta climática y reconstrucción (en desarrollo)

---

## Licencia

DendroLen se distribuye bajo licencia **[GNU General Public License v3.0](LICENSE.txt)**.

---

## Autor

**Moisés E. Rojas Badilla**  
📧 moisese.rojasbadilla@gmail.com  
🔬 ORCID: [0000-0002-1101-2280](https://orcid.org/0000-0002-1101-2280)
