# DendroLen — Registro de cambios

## 2.1.0 — 10 de octubre de 2026

Primera actualización desde la publicación inicial. Agrega construcción de
cronologías, edición de la serie durante la medición y más formatos de serie
maestra.

### Nuevo

**Construcción de cronologías** (`cronologia.py`). Estandarización y
cronologías estandarizadas sin salir del programa, en sus tres variantes
—cruda, estándar y residual— con spline de Cook y Peters, exponencial
negativa, recta, media móvil y media.

El código proviene de DPI para que ambos programas entreguen los mismos
índices y las mismas correlaciones. Comprobado: el ajuste de tendencia de los
dos devuelve la misma curva, con diferencia exactamente cero, en 350
comparaciones sobre los cinco métodos, incluidas series casi planas, con
asíntota pegada a cero, cortas y con huecos.

**Edición de la serie durante la medición.** Insertar y eliminar anillos en
cualquier posición, y desplazar la serie completa en el tiempo, sin
interrumpir la sesión ni volver a empezar.

**Persistencia de rutas.** La última carpeta usada se recuerda entre sesiones.

**Retomar una muestra existente.** El asistente de configuración abre un
archivo ya medido, lee su sidecar de anomalías y precarga los datos de la
muestra.

### Mejoras

- La serie maestra acepta más formatos y deduce la escala del archivo Tucson
  al leerlo, en vez de suponer una sola precisión.
- El ordenamiento de códigos al unir archivos sigue el orden natural de los
  códigos dendrocronológicos, no el alfabético.
- Los atajos de teclado se registran de forma centralizada.

### Corregido

- El archivo `.gitignore` del repositorio estaba subido con el nombre
  `.xdp-gitignore-xV6qzh`, que recibió del selector de archivos al copiarlo.
  Con ese nombre git no ignoraba nada.

**scipy pasa a ser dependencia obligatoria.** Era opcional, y el respaldo sin
scipy no era equivalente: el del spline sí daba el mismo resultado, pero el de
la exponencial negativa caía a un ajuste log-lineal, de modo que dos
instalaciones de DendroLen podían entregar cronologías distintas sin avisar.

Al verificarlo aparecieron tres divergencias más con DPI, que también se
corrigieron: DendroLen aceptaba ajustes exponenciales degenerados —asíntota
pegada a cero o sin decaimiento, que ARSTAN rechaza—, pasaba los huecos de la
serie al spline en vez de ajustar solo sobre los años con dato, y no forzaba
ventana impar en la media móvil, lo que desplaza la curva medio año.

### Notas

Se agrega `requirements.txt`, que antes no existía: las dependencias solo
estaban anotadas en el README. Ahora incluye scipy y el chequeo de arranque
también verifica numpy, pandas y scipy, que no comprobaba.

---

## 2.0.0 — 8 de junio de 2026

Versión inicial pública. Medición en tiempo real con carro de medición
USB-serial, co-datación en vivo con serie maestra, registro de anomalías,
exportación al formato Tucson y unión de archivos `.rwl`.
