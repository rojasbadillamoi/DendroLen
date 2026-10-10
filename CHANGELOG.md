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
índices y las mismas correlaciones. La única diferencia de implementación es
el solver del spline: DPI usa scipy y DendroLen lo resuelve con numpy cuando
scipy no está instalado, para no volverlo una dependencia obligatoria del
instalador. Se verificó que ambos caminos coinciden hasta 1×10⁻¹¹ en valor
relativo.

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

### Notas

Se agrega `requirements.txt`, que antes no existía: las dependencias solo
estaban anotadas en el README.

---

## 2.0.0 — 8 de junio de 2026

Versión inicial pública. Medición en tiempo real con carro de medición
USB-serial, co-datación en vivo con serie maestra, registro de anomalías,
exportación al formato Tucson y unión de archivos `.rwl`.
