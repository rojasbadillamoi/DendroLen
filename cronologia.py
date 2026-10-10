"""
cronologia.py — DendroLen

Construcción de cronologías estandarizadas, con el mismo método que el botón
Crono de DPI. El código viene de modulo_codatacion.py de DPI para que ambos
programas entreguen exactamente los mismos índices y las mismas correlaciones.

scipy es dependencia obligatoria, igual que en DPI. Antes era opcional y eso
tenía una consecuencia que no se veía: el respaldo del spline da el mismo
resultado, pero el de la exponencial negativa caía a un ajuste log-lineal, que
es la aproximación clásica y NO el mismo valor. Dos instalaciones de DendroLen
podían entregar cronologías distintas sin avisar.

Comprobado: `_fit_trend` de los dos programas devuelve la MISMA curva, con
diferencia exactamente cero, en 350 comparaciones sobre los cinco métodos
—series con decaimiento fuerte y suave, casi planas, crecientes, con asíntota
pegada a cero, cortas de 3 a 15 años y con huecos de NaN—. Lo que hizo falta
para eso, además de scipy, fue portar tres cosas que no eran evidentes: el
rechazo de los ajustes exponenciales degenerados, el tratamiento de los huecos
en el spline y la ventana impar de la media móvil.

Valores por defecto, iguales a los de DPI:
    tipo        residual
    método      spline de Cook & Peters, rigidez 32 años
    agregación  media biponderada
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RIGIDEZ_SPLINE_DEFECTO = 32   # años, estilo COFECHA
ORDEN_AR_MAXIMO        = 3    # COFECHA llega hasta 3
METODOS_DETREND        = ("spline", "negexp", "linear", "media_movil", "media")
TIPOS_CRONOLOGIA       = ("raw", "standard", "residual")


# =============================================================================
# AGREGACIÓN
# =============================================================================

def biweight_mean(values, c: float = 9.0, minimo: int = 6) -> float:
    """Media biponderada de Tukey, al modo de ARSTAN.

    Con menos de seis observaciones devuelve la MEDIANA: verificado contra una
    corrida de ARSTAN sobre un archivo de exactamente tres series, donde su
    cronología cruda es exactamente la mediana (r = 1,000000). Con pocos datos
    la desviación absoluta mediana es un estimador pésimo de la escala y la
    ponderación queda arbitraria.

    Constante 9, la de `tbrm` de dplR, que es la referencia publicada.
    """
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan
    if len(x) < max(int(minimo), 1):
        return float(np.median(x))
    m = np.median(x)
    mad = np.median(np.abs(x - m))
    if mad <= 0:
        return float(m)
    u = (x - m) / (c * mad + 1e-6)
    w = np.where(np.abs(u) <= 1, (1 - u ** 2) ** 2, 0.0)
    if w.sum() <= 0:
        return float(m)
    return float(np.sum(w * x) / np.sum(w))


# =============================================================================
# SPLINE DE COOK & PETERS (1981)
# =============================================================================

def _resolver_banda(ab: np.ndarray, qty: np.ndarray) -> np.ndarray:
    """Resuelve el sistema pentadiagonal simétrico del spline.

    Usa scipy si está instalado y, si no, arma la matriz densa y la resuelve
    con numpy. Ambos caminos dan el mismo resultado.
    """
    try:
        from scipy.linalg import solveh_banded
        return solveh_banded(ab, qty, lower=False)
    except Exception:
        pass
    m = len(qty)
    A = np.zeros((m, m), dtype=float)
    np.fill_diagonal(A, ab[2, :])
    if m > 1:
        e = ab[1, 1:]
        A[np.arange(m - 1), np.arange(1, m)] = e
        A[np.arange(1, m), np.arange(m - 1)] = e
    if m > 2:
        f = ab[0, 2:]
        A[np.arange(m - 2), np.arange(2, m)] = f
        A[np.arange(2, m), np.arange(m - 2)] = f
    return np.linalg.solve(A, qty)


def spline_cook(y: np.ndarray, nyrs: float = 32.0, f: float = 0.5) -> np.ndarray:
    """Spline cúbico de suavizado de Cook & Peters (1981).

    Es el spline estándar de la dendrocronología (ARSTAN, COFECHA, dplR): se
    define por su respuesta de frecuencia. Con los valores por defecto, una
    oscilación de `nyrs` años conserva el 50% de su amplitud; las más rápidas
    se atenúan y las más lentas pasan casi intactas.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < 4:
        return np.full(n, float(np.mean(y)) if n else 0.0)

    nyrs = max(float(nyrs), 2.5)
    f = min(max(float(f), 1e-6), 1.0 - 1e-6)
    w = 2.0 * np.pi / nyrs
    cw = np.cos(w)
    lam = (1.0 / f - 1.0) * (2.0 + cw) / (12.0 * (1.0 - cw) ** 2)

    m = n - 2
    ab = np.zeros((3, m))
    if m > 2:
        ab[0, 2:] = lam
    if m > 1:
        ab[1, 1:] = 1.0 / 6.0 - 4.0 * lam
    ab[2, :] = 2.0 / 3.0 + 6.0 * lam

    qty = y[:-2] - 2.0 * y[1:-1] + y[2:]
    try:
        c = _resolver_banda(ab, qty)
    except Exception:
        return np.full(n, float(np.mean(y)))

    cp = np.zeros(n + 2)
    cp[2:2 + m] = c
    qc = cp[2:n + 2] - 2.0 * cp[1:n + 1] + cp[0:n]
    return y - lam * qc


# =============================================================================
# AJUSTE DE TENDENCIA
# =============================================================================

def _fit_trend(values: np.ndarray, metodo: str,
               ventana_mm: int | None = None,
               rigidez: int | None = None) -> np.ndarray:
    """Ajusta la curva de tendencia según el método indicado."""
    y = np.asarray(values, dtype=float)
    x = np.arange(len(y), dtype=float)
    n = len(y)
    if n == 0:
        return y.copy()
    if n < 3:
        return np.full(n, float(np.mean(y)))

    metodo = (metodo or "spline").lower()
    finito = np.isfinite(y)
    x_fit, y_fit = x[finito], y[finito]
    if len(y_fit) < 3:
        return np.full(n, float(np.nanmean(y)) if np.any(finito) else 0.0)

    def _recta():
        p = np.polyfit(x_fit, y_fit, 1)
        return np.polyval(p, x)

    if metodo in {"spline", "spl", "cubic_spline"}:
        # Spline en ESCALA LINEAL con piso en el 10 % de la media, idéntico al
        # de DPI. Tres detalles que parecen menores y no lo son:
        #
        # 1. El spline se ajusta solo sobre los valores FINITOS. Pasarle los
        #    huecos propaga NaN a toda la serie.
        # 2. El piso sale de la media de los valores POSITIVOS. Con la media de
        #    todos, un par de valores negativos lo bajan y el recorte cambia.
        # 3. Si hubo huecos, la curva se interpola de vuelta a la rejilla
        #    completa de años.
        try:
            _y = np.asarray(y_fit, dtype=float)
            _sp = np.asarray(spline_cook(
                _y, nyrs=float(rigidez or RIGIDEZ_SPLINE_DEFECTO), f=0.5))
            _pos = _y[_y > 0]
            _piso = 0.10 * float(np.nanmean(_pos)) if _pos.size else 1e-6
            tend = np.maximum(_sp, _piso)
            if len(tend) != len(x):
                tend = np.interp(x, x_fit, tend)
            media = float(np.nanmean(y_fit))
            tend = np.where(np.isfinite(tend) & (tend > 0), tend, media)
            return tend
        except Exception:
            return _recta()

    if metodo in {"negexp", "exp", "exponencial"}:
        # Opción 1 de ARSTAN: «neg expon curve (k>0), no = opt 4». Idéntico al
        # de DPI, incluido el rechazo de los ajustes degenerados, que es lo que
        # hace que los dos programas den la misma curva.
        #
        # El ajuste exponencial falla mucho más seguido de lo que uno supondría,
        # y cuando falla el respaldo de ARSTAN es su opción 4 —regresión lineal
        # de cualquier pendiente—, no la media horizontal, que es su opción 6.
        #
        # Sin el rechazo, el optimizador empuja los parámetros contra el borde y
        # devuelve una exponencial casi plana que «converge» pero que ARSTAN
        # descarta: una exponencial que no decae es una recta disfrazada.
        from scipy.optimize import curve_fit

        def _f(t, a, b, k):
            return a * np.exp(-b * t) + k

        a0 = max(float(np.nanmax(y_fit) - np.nanmin(y_fit)), 1e-3)
        b0 = 0.01
        c0 = max(float(np.nanmin(y_fit)), 1e-6)
        try:
            popt, _ = curve_fit(
                _f, x_fit, y_fit, p0=(a0, b0, c0), maxfev=20000,
                bounds=([0.0, 0.0, 0.0], [np.inf, 10.0, np.inf]),
            )
            a_f, b_f, d_f = popt
            tend = _f(x, *popt)
            # La asíntota debe ser ESTRICTAMENTE positiva; el umbral es
            # relativo a la media porque 0,001 mm no significa lo mismo en una
            # serie de 0,3 mm que en una de 3 mm.
            _piso_d = (1e-4 * float(np.nanmean(y_fit))
                       if np.isfinite(np.nanmean(y_fit)) else 0.0)
            if (not np.all(np.isfinite(tend)) or b_f <= 1e-4
                    or a_f <= 1e-6 or d_f <= _piso_d):
                return _recta()
            return tend
        except Exception:
            return _recta()

    if metodo in {"media_movil", "moving_average", "ma"}:
        # Igual que DPI: la ventana por omisión es el 10 % de los años con
        # dato —no del largo total— y se fuerza IMPAR, porque una ventana par
        # centrada no queda centrada y desplaza la curva medio año.
        if ventana_mm is not None and ventana_mm >= 3:
            w = int(ventana_mm)
        else:
            w = max(3, int(round(len(y_fit) * 0.10)))
        if w % 2 == 0:
            w += 1
        return (pd.Series(y).rolling(window=w, center=True, min_periods=1)
                .mean().to_numpy(dtype=float))

    if metodo in {"media", "mean", "horizontal"}:
        return np.full(n, float(np.nanmean(y)))

    return _recta()


def detrend_serie_indice(serie_mm: pd.Series, metodo: str = "spline",
                         ventana_mm: int | None = None,
                         rigidez: int | None = None) -> pd.Series:
    """Convierte una serie de anchos en índices adimensionales (media ≈ 1).

    Incluye la guarda de positividad de ARSTAN y dplR: si algún punto de la
    curva baja del 5% de la media de la serie, se descarta la curva entera y
    se usa la media. Es preferible una serie sin detrending consistente a una
    mitad dividida por su tendencia local y mitad por la media global.
    """
    s = pd.to_numeric(serie_mm, errors="coerce").astype(float).dropna()
    if s.empty:
        return s.copy()
    if (metodo or "").lower() in {"raw", "none", "ninguno"}:
        return s.copy()

    tendencia = _fit_trend(s.to_numpy(dtype=float), metodo,
                           ventana_mm=ventana_mm, rigidez=rigidez)
    tendencia = pd.Series(tendencia, index=s.index, dtype=float)

    tv = tendencia.to_numpy(dtype=float)
    media_s = float(np.nanmean(s.to_numpy(dtype=float)))
    piso = 0.05 * media_s if np.isfinite(media_s) and media_s > 0 else 0.0
    if not np.all(np.isfinite(tv)) or np.any(tv <= piso):
        tendencia = pd.Series(np.full(len(tendencia), media_s),
                              index=tendencia.index)

    return (s / tendencia).replace([np.inf, -np.inf], np.nan).dropna()


# =============================================================================
# MODELO AUTORREGRESIVO (cronología residual)
# =============================================================================

def _ajustar_ar_yule_walker(x: np.ndarray, p: int):
    """Ajusta un AR(p) por Yule-Walker (recursión de Levinson-Durbin)."""
    n = len(x)
    if p <= 0:
        return np.array([]), float(np.var(x))
    r = np.array([np.dot(x[k:], x[:n - k]) / n if k else np.dot(x, x) / n
                  for k in range(p + 1)])
    if r[0] <= 0:
        return np.zeros(p), 0.0
    phi = np.zeros(p)
    v = r[0]
    for k in range(1, p + 1):
        acum = r[k] - np.dot(phi[:k - 1], r[1:k][::-1]) if k > 1 else r[1]
        if v <= 0:
            break
        kappa = acum / v
        nuevo = phi[:k - 1] - kappa * phi[:k - 1][::-1] if k > 1 else np.array([])
        phi[:k - 1] = nuevo
        phi[k - 1] = kappa
        v *= (1.0 - kappa * kappa)
        if v <= 0:
            v = 1e-12
            break
    return phi[:p], float(v)


def _seleccionar_orden_ar(x: np.ndarray, max_orden: int = ORDEN_AR_MAXIMO) -> int:
    """Elige el orden del AR por BIC, que es lo que mejor reproduce COFECHA."""
    n = len(x)
    max_orden = int(max(0, min(max_orden, n // 10, 10)))
    if n < 20 or max_orden < 1:
        return min(1, max_orden)
    mejor_orden, mejor_pun = 1, np.inf
    for p in range(1, max_orden + 1):
        _phi, v = _ajustar_ar_yule_walker(x, p)
        if not np.isfinite(v) or v <= 0:
            continue
        pun = n * np.log(v) + p * np.log(n)      # BIC
        if pun < mejor_pun - 1e-9:
            mejor_pun, mejor_orden = pun, p
    return mejor_orden


def _ajustar_ar_burg(x: np.ndarray, p: int):
    """Coeficientes autorregresivos por el método de Burg.

    Es el estimador de ARSTAN, y es el que usa DPI. Verificado despejando los
    coeficientes de ARSTAN desde los residuos por serie de una corrida real:
    el error medio de Burg es 0,00106, frente a 0,00456 de Yule-Walker y
    0,00273 de mínimos cuadrados.

    Burg minimiza la suma de los errores de predicción hacia adelante y hacia
    atrás, en vez de resolver las ecuaciones de Yule-Walker sobre las
    autocorrelaciones muestrales. Con series cortas la diferencia se nota,
    porque Yule-Walker subestima la persistencia.
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n <= p or p < 1:
        return np.zeros(max(p, 0)), float(np.var(x)) if n else 0.0
    f = x.copy()
    b = x.copy()
    a = []
    v = float(np.dot(x, x) / n)
    for m in range(p):
        num = 2.0 * float(np.dot(f[m + 1:], b[m:-1]))
        den = float(np.dot(f[m + 1:], f[m + 1:]) + np.dot(b[m:-1], b[m:-1]))
        k = num / den if den > 0 else 0.0
        a = [ai - k * aj for ai, aj in zip(a, a[::-1])] + [k] if a else [k]
        ff = f[m + 1:] - k * b[m:-1]
        bb = b[m:-1] - k * f[m + 1:]
        f = np.concatenate([f[:m + 1], ff])
        b = np.concatenate([b[:m + 1], bb])
        v *= (1.0 - k * k)
    return np.asarray(a, dtype=float), max(v, 1e-12)


def orden_ar_agrupado(indices: dict, pmax: int = 10) -> tuple:
    """Orden autorregresivo AGRUPADO, al modo de ARSTAN.

    ARSTAN no elige un orden por serie: calcula las autocorrelaciones de toda
    la colección juntas, ajusta Yule-Walker sobre ellas, elige el orden por el
    PRIMER MÍNIMO del AIC y aplica ese mismo orden a todas las series.

    El primer mínimo, y no el mínimo global, es deliberado: los dos criterios
    pueden diferir y ARSTAN pide revisar la traza del AIC.

    Devuelve (orden, autocorrelaciones_agrupadas).
    """
    num = np.zeros(pmax)
    den = np.zeros(pmax)
    ntot = 0
    for v in indices.values():
        x = pd.to_numeric(v, errors="coerce").dropna().to_numpy(dtype=float)
        if len(x) < 20:
            continue
        x = x - x.mean()
        n = len(x)
        ntot += n
        c0 = float(np.sum(x * x))
        if c0 <= 0:
            continue
        for k in range(1, pmax + 1):
            if n - k < 5:
                continue
            num[k - 1] += n * (float(np.sum(x[:-k] * x[k:])) / c0)
            den[k - 1] += n
    if ntot == 0:
        return 1, np.zeros(pmax)
    rho = num / np.maximum(den, 1e-12)

    aic = []
    for p in range(0, pmax + 1):
        if p == 0:
            var = 1.0
        else:
            R = np.array([[1.0 if i == j else rho[abs(i - j) - 1]
                           for j in range(p)] for i in range(p)])
            r = rho[:p]
            try:
                phi = np.linalg.solve(R, r)
            except Exception:
                aic.append(np.inf)
                continue
            var = 1.0 - float(np.dot(phi, r))
        aic.append(ntot * np.log(max(var, 1e-12)) + 2 * p)
    for p in range(1, len(aic) - 1):
        if aic[p] <= aic[p - 1] and aic[p] <= aic[p + 1]:
            return p, rho
    return max(int(np.argmin(aic)), 1), rho


def residualizar_indice(indice: pd.Series, max_orden: int | None = None,
                        orden_fijo: int | None = None,
                        devolver_orden: bool = False):
    """Quita la autocorrelación del índice con un modelo AR."""
    s = pd.to_numeric(indice, errors="coerce").astype(float).dropna()
    if len(s) < 4:
        return (s.copy(), 0) if devolver_orden else s.copy()
    c = s - s.mean()
    x = c.to_numpy(dtype=float)
    if np.std(x) == 0:
        return (s.copy(), 0) if devolver_orden else s.copy()

    if max_orden is None:
        max_orden = ORDEN_AR_MAXIMO
    p = int(orden_fijo) if orden_fijo else _seleccionar_orden_ar(x, max_orden)

    if p <= 0:
        resid_v = x.copy()
    else:
        # Burg, no Yule-Walker: es el estimador de ARSTAN. Ver _ajustar_ar_burg.
        phi, _ = _ajustar_ar_burg(x, p)
        # RETROPRONÓSTICO de los p valores anteriores al inicio.
        #
        # ARSTAN no deja los primeros p años sin modelar: estima los valores
        # previos con el mismo modelo, reflejando la serie, y así calcula un
        # residuo para TODOS los años. Sin esto el primer año se queda con el
        # índice crudo y —peor— ese valor entra en la media de recentrado y
        # desplaza la serie ENTERA unas tres milésimas.
        prev = np.empty(p, dtype=float)
        for i in range(p):
            j = min(i, len(x) - 1)
            prev[p - 1 - i] = float(np.dot(phi[:1], [x[j]])) if p == 1 else x[j]
        ext = np.concatenate([prev, x])
        resid_v = x.copy()
        for t in range(len(x)):
            hist = ext[t:t + p][::-1]
            resid_v[t] = x[t] - float(np.dot(phi, hist))

    resid = pd.Series(resid_v, index=s.index)
    # Se devuelve al nivel de la serie original, como hace dplR en ar.func
    resid = resid - resid.mean() + float(s.mean())
    return (resid, p) if devolver_orden else resid


# =============================================================================
# API PRINCIPAL
# =============================================================================

def normalizar_serie(serie_mm: pd.Series,
                     tipo: str = "residual",
                     metodo: str = "spline",
                     rigidez: int | None = None,
                     ventana_mm: int | None = None,
                     orden_ar: int | None = None) -> pd.Series:
    """Estandariza UNA serie de anchos según el tipo de cronología pedido.

    raw       devuelve los anchos tal cual
    standard  índices tras quitar la tendencia
    residual  índices sin tendencia y sin autocorrelación
    """
    tipo = (tipo or "raw").lower()
    if tipo == "raw":
        return pd.to_numeric(serie_mm, errors="coerce").astype(float).dropna()

    idx = detrend_serie_indice(serie_mm, metodo,
                               ventana_mm=ventana_mm, rigidez=rigidez)
    if tipo == "residual":
        return residualizar_indice(idx, orden_fijo=orden_ar)
    return idx


def construir_cronologia(series: dict[str, pd.Series],
                         tipo: str = "residual",
                         metodo: str = "spline",
                         agregacion: str = "biweight",
                         rigidez: int | None = None,
                         ventana_mm: int | None = None) -> tuple[pd.Series, dict]:
    """Arma la cronología a partir de varias series, como el botón Crono de DPI.

    Devuelve (cronología, información). La información trae el número de
    series, la profundidad muestral por año y los parámetros usados, para
    poder mostrarlos en pantalla.
    """
    if not series:
        raise ValueError("No hay series para construir la cronología.")

    # Orden AR agrupado, al modo de ARSTAN: un solo orden para toda la
    # colección, elegido sobre las autocorrelaciones del conjunto. No es la
    # mediana de los órdenes por serie, que da otra cosa.
    #
    # El pre-ajuste va sin `rigidez` a propósito: es lo que hace DPI, y la
    # igualdad entre los dos programas se mide sobre su comportamiento, no
    # sobre el que uno supondría.
    orden_pool = None
    if (tipo or "").lower() == "residual":
        try:
            prev = {}
            for nombre, s in series.items():
                prev[nombre] = detrend_serie_indice(s, metodo,
                                                    ventana_mm=ventana_mm)
            if len(prev) >= 3:
                orden_pool, _rho = orden_ar_agrupado(prev)
        except Exception:
            orden_pool = None

    columnas = []
    for nombre, s in series.items():
        try:
            col = normalizar_serie(s, tipo=tipo, metodo=metodo,
                                   rigidez=rigidez, ventana_mm=ventana_mm,
                                   orden_ar=orden_pool)
            if len(col) > 0:
                col.name = nombre
                columnas.append(col)
        except Exception:
            continue

    if not columnas:
        raise ValueError("Ninguna serie pudo estandarizarse.")

    df = pd.concat(columnas, axis=1).sort_index()

    agg = (agregacion or "biweight").lower()
    if agg in {"biweight", "robusta", "robust"}:
        valores = df.apply(lambda fila: biweight_mean(fila.dropna().values), axis=1)
    elif agg in {"median", "mediana"}:
        valores = df.median(axis=1, skipna=True)
    else:
        valores = df.mean(axis=1, skipna=True)

    profundidad = df.notna().sum(axis=1)
    crono = pd.Series(valores).dropna().sort_index()

    info = {
        "n_series":    len(columnas),
        "tipo":        tipo,
        "metodo":      metodo,
        "agregacion":  agg,
        "rigidez":     int(rigidez or RIGIDEZ_SPLINE_DEFECTO),
        "orden_ar":    orden_pool,
        "profundidad": profundidad.reindex(crono.index).fillna(0).astype(int),
        "anio_min":    int(crono.index.min()) if len(crono) else None,
        "anio_max":    int(crono.index.max()) if len(crono) else None,
    }
    return crono, info


def describir(info: dict) -> str:
    """Resumen corto para mostrar junto al nombre de la cronología."""
    if not info:
        return ""
    tipo = {"raw": "sin estandarizar", "standard": "estándar",
            "residual": "residual"}.get(info.get("tipo", ""), info.get("tipo", ""))
    partes = [f"cronología {tipo} de {info.get('n_series', 0)} series"]
    if info.get("tipo") != "raw":
        partes.append(f"{info.get('metodo', 'spline')} {info.get('rigidez', 32)} años")
    if info.get("orden_ar"):
        partes.append(f"AR({info['orden_ar']})")
    prof = info.get("profundidad")
    if prof is not None and len(prof):
        partes.append(f"profundidad {int(prof.min())}–{int(prof.max())}")
    return " · ".join(partes)
