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
índices y las mismas correlaciones. La cronología se construye igual que la
auto-cronología de DPI al cargar un archivo de referencia con varias series
—spline de Cook 32, residual, media biponderada—, que es la ruta equivalente,
no la pestaña Cronología de DPI con sus opciones ARSTAN.

Comprobado en dos niveles. El ajuste de tendencia devuelve la misma curva en
350 comparaciones sobre los cinco métodos, con diferencia exactamente cero,
incluidas series casi planas, con asíntota pegada a cero, cortas y con huecos.
Y la cronología completa coincide también con diferencia cero: 264
comparaciones sintéticas sobre tres tipos, cinco métodos y tres agregaciones,
más cinco colecciones reales de 19 a 82 series.

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

Al verificarlo aparecieron tres divergencias más en el ajuste de tendencia,
que también se corrigieron: DendroLen aceptaba ajustes exponenciales
degenerados —asíntota pegada a cero o sin decaimiento, que ARSTAN rechaza—,
pasaba los huecos de la serie al spline en vez de ajustar solo sobre los años
con dato, y no forzaba ventana impar en la media móvil, lo que desplaza la
curva medio año.

**La cronología tenía otras cuatro.** Comparar el ajuste de tendencia no
alcanzaba: la cronología residual pasa además por un modelo autorregresivo y
una media robusta, y ahí los dos programas hacían cosas distintas. Medido
sobre cinco colecciones reales de 19 a 82 series, deshaciendo cada corrección
contra el código actual, en índices de media ≈ 1:

| diferencia | DendroLen tenía | error máximo |
|---|---|---|
| constante del biweight | 6 en vez de 9, y mínimo 3 en vez de 6 | 0,072–0,089 |
| años previos al inicio | los primeros p sin modelar | 0,018–0,084 |
| estimador AR | Yule-Walker en vez de Burg | 0,002–0,010 |
| orden AR agrupado | mediana de los órdenes por serie | 0,000 |

El retropronóstico importa porque sin él los primeros años quedan con el
índice crudo, y ese valor entra en la media de recentrado y desplaza la serie
entera.

El orden agrupado sale en cero porque el criterio corregido —ver abajo— elige
AR(1) en las cinco colecciones, y la mediana de los órdenes por serie también.
Coinciden en la práctica, pero el código tiene que coincidir igual: con el
criterio anterior esa misma fila llegaba a 0,233.

**El criterio del orden AR agrupado estaba mal en los dos**, y se corrigió en
DPI 2.4.1 y acá. Se elegía por el primer mínimo local del AIC con `n` igual a
la suma de los largos de todas las series; con eso la penalización queda nula,
la traza sale monótona y el orden lo termina decidiendo cuántas series tiene la
colección —AR(1) con 19 a 43 series, AR(10) con 70 a 82, con la misma
autocorrelación de primer orden—. Ahora es BIC sobre el largo mediano con
techo en el orden 3, el mismo criterio que la ruta por serie.

### Notas

Se agrega `requirements.txt`, que antes no existía: las dependencias solo
estaban anotadas en el README. Ahora incluye scipy y el chequeo de arranque
también verifica numpy, pandas y scipy, que no comprobaba.

---

## 2.0.0 — 8 de junio de 2026

Versión inicial pública. Medición en tiempo real con carro de medición
USB-serial, co-datación en vivo con serie maestra, registro de anomalías,
exportación al formato Tucson y unión de archivos `.rwl`.
