#!/usr/bin/env python3
"""Construye el .deb de DendroLen para Debian/Ubuntu.

Paquete NATIVO: instala el código y declara las dependencias como paquetes del
sistema, en vez de empacar un intérprete entero. Pesa ~1 MB en vez de ~400 MB,
y usa el Qt del sistema, que es lo que hace que el tema claro/oscuro del
escritorio se respete.

Uso:   python3 construir_deb.py [carpeta_de_salida]

Empaqueta el código de SU PROPIA carpeta, así que basta con dejarlo junto a los
módulos y correrlo. Requiere dpkg-deb y fakeroot (vienen con Debian/Ubuntu).

Gemelo de `construir_deb.py` de DPI. Si arreglas algo acá, míralo también allá.
"""
import shutil, subprocess, sys
from pathlib import Path

# La carpeta donde vive este script es la que se empaqueta.
ORIGEN = Path(__file__).resolve().parent
SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else ORIGEN.parent / "paquetes"

# El identificador de escritorio TIENE que ser el mismo que el programa declara
# con setDesktopFileName() (main_dendro.py). Si no coinciden, en Wayland el
# ícono no aparece en el dock.
APP_ID = "moicedrus-dendrolen"

# Nombre del paquete Debian. La Policy 5.6.1 solo admite minúsculas, dígitos,
# «+», «-» y «.»: ni mayúsculas, ni espacios, ni guión bajo. El nombre visible
# con su capitalización va en Description y en el menú.
PAQUETE = "dendrolen"

# Contacto de soporte del paquete: va en el campo Maintainer, que es la
# dirección a la que escribe quien encuentra un problema de empaquetado.
MANTENEDOR = "Moisés E. Rojas-Badilla <moisese.rojasbadilla@gmail.com>"

sys.path.insert(0, str(ORIGEN))
from constantes import APP_VERSION as VERSION, APP_NAME  # noqa

RAIZ = SALIDA / f"{PAQUETE}_{VERSION}"
if RAIZ.exists():
    shutil.rmtree(RAIZ)

LIB = RAIZ / "usr/lib" / PAQUETE
BIN = RAIZ / "usr/bin"
APPS = RAIZ / "usr/share/applications"
DOC = RAIZ / "usr/share/doc" / PAQUETE
DEBIAN = RAIZ / "DEBIAN"
for d in (LIB, BIN, APPS, DOC, DEBIAN):
    d.mkdir(parents=True, exist_ok=True)

# ── 1. Código fuente ──────────────────────────────────────────────────────
#  · launcher.py es la entrada de PyInstaller para Windows: escribe el
#    crash_log junto a sys.executable, que en una instalación de sistema es
#    /usr/bin y no tiene permiso de escritura. La entrada acá es main_dendro.
#  · construir_deb.py es esta misma herramienta, no parte del programa.
_FUERA = {"launcher.py", "construir_deb.py"}
modulos = sorted(p.name for p in ORIGEN.glob("*.py") if p.name not in _FUERA)
for nombre in modulos:
    shutil.copy2(ORIGEN / nombre, LIB / nombre)
# El programa carga el ícono en tiempo de ejecución, relativo a su propio
# archivo (splash y ventana principal), así que tiene que viajar adentro.
shutil.copy2(ORIGEN / "DendroLen.ico", LIB / "DendroLen.ico")
print(f"código: {len(modulos)} módulos")

# ── 2. Íconos ─────────────────────────────────────────────────────────────
from PIL import Image

# Se prefiere un PNG grande si existe; si no, el .ico, que es el que ya usa el
# instalador de Windows. Su mayor tamaño interno es 256, así que no se ofrecen
# tamaños sobre eso: ampliar desde 256 se ve peor que dejar que el escritorio
# escale solo. Si algún día hay un PNG de 512 o más, se usa sin tocar nada.
_CANDIDATOS = ("dendrolen_icon.png", "DendroLen.png", "dendrolen.png",
               "DendroLen.ico")
_ruta_icono = next((ORIGEN / n for n in _CANDIDATOS if (ORIGEN / n).exists()), None)
if _ruta_icono is None:
    sys.exit("No encuentro el ícono: se esperaba alguno de " + ", ".join(_CANDIDATOS))
fuente = Image.open(_ruta_icono).convert("RGBA")

# El original puede no ser exactamente cuadrado; se centra en un lienzo
# cuadrado transparente para que no quede deformado al reducir.
lado_max = max(fuente.size)
cuadrado = Image.new("RGBA", (lado_max, lado_max), (0, 0, 0, 0))
cuadrado.paste(fuente, ((lado_max - fuente.width) // 2,
                        (lado_max - fuente.height) // 2))

tamanos = [t for t in (16, 24, 32, 48, 64, 128, 256, 512) if t <= lado_max]
for lado in tamanos:
    destino = RAIZ / f"usr/share/icons/hicolor/{lado}x{lado}/apps"
    destino.mkdir(parents=True, exist_ok=True)
    cuadrado.resize((lado, lado), Image.LANCZOS).save(destino / f"{APP_ID}.png")

# Copia en pixmaps para los entornos de escritorio antiguos que todavía la
# buscan ahí en vez de en el árbol hicolor.
pix = RAIZ / "usr/share/pixmaps"
pix.mkdir(parents=True, exist_ok=True)
cuadrado.resize((min(256, lado_max),) * 2, Image.LANCZOS).save(pix / f"{APP_ID}.png")
print(f"íconos: {len(tamanos)} tamaños desde {_ruta_icono.name} "
      f"{fuente.size} -> {tamanos}")

# ── 3. Lanzador ───────────────────────────────────────────────────────────
lanzador = BIN / "dendrolen"
lanzador.write_text(
    "#!/bin/sh\n"
    "# Lanzador de DendroLen\n"
    f'exec python3 /usr/lib/{PAQUETE}/main_dendro.py "$@"\n')
lanzador.chmod(0o755)

# ── 4. Entrada de escritorio ──────────────────────────────────────────────
# El nombre del archivo TIENE que ser APP_ID.desktop: en Wayland el compositor
# no puede leer el ícono desde la ventana y lo busca por este nombre, que es el
# que la aplicación declara con setDesktopFileName().
(APPS / f"{APP_ID}.desktop").write_text(
    "[Desktop Entry]\n"
    "Type=Application\n"
    f"Name={APP_NAME}\n"
    "GenericName=Dendrocronología\n"
    "Comment=Medición de anillos en carro de medición\n"
    "Exec=dendrolen %f\n"
    f"Icon={APP_ID}\n"
    "Terminal=false\n"
    # Una sola categoría PRINCIPAL (Science). Con varias, el menú del
    # escritorio muestra la aplicación repetida una vez por categoría.
    # Geoscience es categoría adicional y requiere Science, así que es válida.
    "Categories=Science;Geoscience;\n"
    "Keywords=dendrocronologia;anillos;arboles;carro;velmex;tree-ring;\n"
    "StartupNotify=true\n", encoding="utf-8")

# ── 4 bis. Metadatos AppStream ────────────────────────────────────────────
# Esto es lo que lee el Centro de Software de Ubuntu (GNOME Software). NO lee
# el archivo «control» de Debian: sin este XML la aplicación aparece sin
# licencia, sin sitio web y sin fecha de última actualización.
#
# La fecha de publicación se toma de CITATION.cff para no tener dos fuentes
# que se contradigan.
import re as _re
_cff = (ORIGEN / "CITATION.cff").read_text(encoding="utf-8")
_m = _re.search(r'^date-released:\s*"?(\d{4}-\d{2}-\d{2})"?', _cff, _re.M)
FECHA = _m.group(1) if _m else "1970-01-01"

# Identificador en notación de dominio invertido, que es lo que pide AppStream.
# Todo en minúsculas: cambiar el identificador una vez publicado hace que el
# Centro de Software lo trate como otra aplicación.
APPSTREAM_ID = "io.github.rojasbadillamoi.dendrolen"

METAINFO = RAIZ / "usr/share/metainfo"
METAINFO.mkdir(parents=True, exist_ok=True)
(METAINFO / f"{APPSTREAM_ID}.metainfo.xml").write_text(
    f"""<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>{APPSTREAM_ID}</id>
  <launchable type="desktop-id">{APP_ID}.desktop</launchable>

  <name>{APP_NAME}</name>
  <summary>Medición de anillos en carro de medición</summary>
  <summary xml:lang="en">Tree-ring measurement with a sliding stage</summary>

  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0-only</project_license>

  <developer id="io.github.rojasbadillamoi">
    <name>Moisés E. Rojas-Badilla</name>
  </developer>

  <description>
    <p>
      Programa de escritorio para medir el ancho de los anillos de crecimiento
      en tiempo real con un carro de medición conectado por puerto USB-serial,
      y escribirlos directamente en formato Tucson.
    </p>
    <p>Incluye:</p>
    <ul>
      <li>Lectura del encoder en vivo, con detección automática del adaptador USB-serial.</li>
      <li>Co-datación contra una serie maestra mientras se mide, con correlación deslizante.</li>
      <li>Edición de la serie durante la medición: insertar, eliminar y desplazar anillos.</li>
      <li>Registro de anomalías por tecla: anillos de helada, anillos claros, falsos y ausentes.</li>
      <li>Construcción de cronologías estandarizadas, con el mismo núcleo numérico que DPI.</li>
      <li>Unión de archivos Tucson con resolución de códigos duplicados.</li>
    </ul>
    <p>
      Las series se exportan en formato Tucson, compatible con COFECHA, ARSTAN,
      CDendro y dplR.
    </p>
    <p>
      Parte de la MoiCedrus Dendrochronological Suite, desarrollada por
      Moisés E. Rojas-Badilla.
    </p>
  </description>

  <categories>
    <category>Science</category>
    <category>Geoscience</category>
  </categories>

  <keywords>
    <keyword>dendrocronología</keyword>
    <keyword>anillos</keyword>
    <keyword>árboles</keyword>
    <keyword>cofechado</keyword>
    <keyword>dendrochronology</keyword>
    <keyword>tree rings</keyword>
    <keyword>crossdating</keyword>
    <keyword>Velmex</keyword>
  </keywords>

  <url type="homepage">https://rojasbadillamoi.github.io/DendroLen/</url>
  <url type="bugtracker">https://github.com/rojasbadillamoi/DendroLen/issues</url>
  <url type="vcs-browser">https://github.com/rojasbadillamoi/DendroLen</url>

  <releases>
    <release version="{VERSION}" date="{FECHA}"/>
  </releases>

  <!-- Sin contenido sensible. GNOME Software muestra un aviso si falta. -->
  <content_rating type="oars-1.1"/>
</component>
""", encoding="utf-8")

# ── 5. Metadatos del paquete ──────────────────────────────────────────────
# python3-serial es pyserial: sin él el programa abre pero no puede leer el
# carro, que es su razón de ser, así que va en Depends y no en Recommends.
# scipy es obligatoria desde 2.1.0: sin ella el ajuste de la exponencial
# negativa cae a otro método y DendroLen dejaría de coincidir con DPI.
DEPENDS = ", ".join([
    "python3 (>= 3.10)", "python3-pyqt6", "python3-serial", "python3-numpy",
    "python3-pandas", "python3-scipy", "python3-matplotlib", "python3-openpyxl",
])
(DEBIAN / "control").write_text(
    f"Package: {PAQUETE}\n"
    f"Version: {VERSION}\n"
    "Section: science\n"
    "Priority: optional\n"
    "Architecture: all\n"
    f"Depends: {DEPENDS}\n"
    f"Maintainer: {MANTENEDOR}\n"
    "Homepage: https://rojasbadillamoi.github.io/DendroLen/\n"
    f"Description: {APP_NAME} - medicion de anillos en carro de medicion\n"
    " Programa de escritorio para medir el ancho de los anillos de\n"
    " crecimiento en tiempo real con un carro conectado por puerto\n"
    " USB-serial, y escribirlos en formato Tucson.\n"
    " .\n"
    " Incluye co-datacion contra una serie maestra mientras se mide,\n"
    " edicion de la serie en caliente, registro de anomalias por tecla\n"
    " y construccion de cronologias estandarizadas.\n"
    " .\n"
    " Parte de la MoiCedrus Dendrochronological Suite, desarrollada por\n"
    " Moises E. Rojas-Badilla.\n", encoding="utf-8")

(DOC / "copyright").write_text(
    "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n"
    f"Upstream-Name: {APP_NAME}\n"
    "Source: https://github.com/rojasbadillamoi/DendroLen\n\n"
    "Files: *\n"
    "Copyright: 2026 Moises Rojas-Badilla\n"
    "License: GPL-3.0\n", encoding="utf-8")

shutil.copy2(ORIGEN / "CHANGELOG.md", DOC / "changelog.md")
subprocess.run(["gzip", "-9n", str(DOC / "changelog.md")], check=True)

# postinst/postrm: refrescar las cachés de iconos y de menú
(DEBIAN / "postinst").write_text(
    "#!/bin/sh\nset -e\n"
    "if [ -x /usr/bin/gtk-update-icon-cache ]; then\n"
    "    gtk-update-icon-cache -q /usr/share/icons/hicolor || true\n"
    "fi\n"
    "if [ -x /usr/bin/update-desktop-database ]; then\n"
    "    update-desktop-database -q /usr/share/applications || true\n"
    "fi\n"
    "exit 0\n")
(DEBIAN / "postinst").chmod(0o755)
shutil.copy2(DEBIAN / "postinst", DEBIAN / "postrm")

# ── 6. Construir ──────────────────────────────────────────────────────────
deb = SALIDA / f"{PAQUETE}_{VERSION}_all.deb"
subprocess.run(["fakeroot", "dpkg-deb", "--build", str(RAIZ), str(deb)],
               check=True)
print(f"\n.deb construido: {deb}  ({deb.stat().st_size/1024:.0f} KB)")
