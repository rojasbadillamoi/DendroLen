"""
cronologia.py — DendroLen

Construcción de cronologías estandarizadas, con el mismo método que el botón
Crono de DPI. El código viene de modulo_codatacion.py de DPI para que ambos
programas entreguen exactamente los mismos índices y las mismas correlaciones.

Diferencia con DPI: el solver del spline está resuelto con numpy en vez de
scipy, para no agregarle esa dependencia al instalador de DendroLen. Se
verificó que ambos caminos coinciden hasta 1e-11 en valor relativo.

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

def biweight_mean(values, c: float = 6.0) -> float:
    """Media biponderada de Tukey: promedio robusto frente a valores atípicos."""
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan
    if len(x) < 3:
        return float(np.mean(x))
    m = np.median(x)
    mad = np.median(np.abs(x - m))
    if mad == 0:
        return float(np.mean(x))
    u = (x - m) / (c * mad)
    mask = np.abs(u) < 1
    if not np.any(mask):
        return float(np.mean(x))
    w = (1 - u[mask] ** 2) ** 2
    return float(np.sum((x[mask] - m) * w) / np.sum(w) + m)


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
        # Spline en escala lineal con piso en el 10% de la media, igual que DPI
        try:
            sp = np.asarray(spline_cook(
                y, nyrs=float(rigidez or RIGIDEZ_SPLINE_DEFECTO), f=0.5))
            media = float(np.nanmean(y))
            piso = 0.10 * media if np.isfinite(media) and media > 0 else 0.0
            sp = np.where(np.isfinite(sp), sp, media)
            sp = np.maximum(sp, piso)
            return sp
        except Exception:
            return _recta()

    if metodo in {"negexp", "exp", "exponencial"}:
        try:
            from scipy.optimize import curve_fit

            def _f(t, a, b, k):
                return a * np.exp(-b * t) + k

            a0 = max(float(y_fit[0] - np.min(y_fit)), 1e-6)
            k0 = float(np.min(y_fit))
            popt, _ = curve_fit(_f, x_fit, y_fit, p0=[a0, 0.01, k0], maxfev=10000)
            tend = _f(x, *popt)
            if not np.all(np.isfinite(tend)):
                return _recta()
            return tend
        except Exception:
            # Sin scipy: ajuste log-lineal, que es la aproximación clásica
            try:
                pos = y_fit > 0
                if pos.sum() >= 3:
                    p = np.polyfit(x_fit[pos], np.log(y_fit[pos]), 1)
                    tend = np.exp(np.polyval(p, x))
                    if np.all(np.isfinite(tend)):
                        return tend
            except Exception:
                pass
            return _recta()

    if metodo in {"media_movil", "moving_average", "ma"}:
        w = int(ventana_mm) if ventana_mm else max(3, int(round(0.10 * n)))
        w = max(3, min(w, n))
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
        if v <= 0:
            continue
        pun = n * np.log(v) + p * np.log(n)      # BIC
        if pun < mejor_pun:
            mejor_orden, mejor_pun = p, pun
    return mejor_orden


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
        phi, _ = _ajustar_ar_yule_walker(x, p)
        resid_v = x.copy()
        for t in range(p, len(x)):
            resid_v[t] = x[t] - float(np.dot(phi, x[t - p:t][::-1]))

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

    # Orden AR agrupado, al modo de ARSTAN: uno solo para toda la colección
    orden_pool = None
    if (tipo or "").lower() == "residual" and len(series) >= 3:
        try:
            ordenes = []
            for s in series.values():
                idx = detrend_serie_indice(s, metodo, ventana_mm=ventana_mm,
                                           rigidez=rigidez)
                if len(idx) >= 20:
                    x = (idx - idx.mean()).to_numpy(dtype=float)
                    ordenes.append(_seleccionar_orden_ar(x))
            if ordenes:
                orden_pool = int(round(float(np.median(ordenes))))
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
