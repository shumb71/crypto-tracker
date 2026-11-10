"""Motor de señales: indicadores y puntuación de confluencia.

Sin dependencias externas. Todo trabaja sobre velas YA CERRADAS.
La puntuación va de -1 (todo bajista) a +1 (todo alcista). No es una
probabilidad: mide cuántas señales independientes apuntan al mismo lado.
"""
from statistics import mean, pstdev

# Peso de cada bloque dentro de una temporalidad (suman 1)
PESOS = {"tendencia": 0.35, "estructura": 0.15, "momento": 0.25,
         "divergencia": 0.15, "volumen": 0.10}


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def sign(x):
    return (x > 0) - (x < 0)


def ema(vals, n):
    """EMA con semilla SMA. Devuelve lista con None hasta tener n datos."""
    out = [None] * len(vals)
    if len(vals) < n:
        return out
    k = 2 / (n + 1)
    prev = mean(vals[:n])
    out[n - 1] = prev
    for i in range(n, len(vals)):
        prev = vals[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(closes, n=14):
    """RSI de Wilder."""
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    diffs = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    up = mean(max(d, 0) for d in diffs[:n])
    dn = mean(max(-d, 0) for d in diffs[:n])
    out[n] = 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)
    for i in range(n, len(diffs)):
        up = (up * (n - 1) + max(diffs[i], 0)) / n
        dn = (dn * (n - 1) + max(-diffs[i], 0)) / n
        out[i + 1] = 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)
    return out


def macd(closes, fast=12, slow=26, sig=9):
    ef, es = ema(closes, fast), ema(closes, slow)
    line = [a - b if a is not None and b is not None else None for a, b in zip(ef, es)]
    start = next((i for i, v in enumerate(line) if v is not None), len(line))
    s = [None] * start + ema(line[start:], sig)
    hist = [a - b if a is not None and b is not None else None for a, b in zip(line, s)]
    return line, s, hist


def atr(h, l, c, n=14):
    if len(c) <= n:
        return None
    tr = [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, len(c))]
    a = mean(tr[:n])
    for x in tr[n:]:
        a = (a * (n - 1) + x) / n
    return a


def pivots(vals, k=5, kind="low"):
    """Índices de mínimos/máximos locales confirmados con k velas a cada lado."""
    out = []
    for i in range(k, len(vals) - k):
        w = vals[i - k:i + k + 1]
        if (kind == "low" and vals[i] == min(w)) or (kind == "high" and vals[i] == max(w)):
            if not out or i - out[-1] > k:
                out.append(i)
    return out


def divergencia(candles, rsi_vals, k=5, max_sep=60, reciente=20):
    """Divergencia regular precio/RSI entre los dos últimos pivotes.

    Alcista: el precio hace un mínimo más bajo y el RSI uno más alto.
    Bajista: el precio hace un máximo más alto y el RSI uno más bajo.
    Solo cuenta si el segundo pivote está entre las últimas `reciente` velas.
    """
    n = len(candles["c"])
    found = []
    for kind, serie, tipo in (("low", candles["l"], "alcista"), ("high", candles["h"], "bajista")):
        p = pivots(serie, k, kind)
        if len(p) < 2:
            continue
        a, b = p[-2], p[-1]
        if n - 1 - b > reciente or not (k <= b - a <= max_sep):
            continue
        ra, rb = rsi_vals[a], rsi_vals[b]
        if ra is None or rb is None:
            continue
        if tipo == "alcista" and serie[b] < serie[a] and rb > ra + 1 and ra < 50:
            found.append({"tipo": tipo, "t": candles["t"][b]})
        if tipo == "bajista" and serie[b] > serie[a] and rb < ra - 1 and ra > 50:
            found.append({"tipo": tipo, "t": candles["t"][b]})
    if not found:
        return None
    return max(found, key=lambda d: d["t"])  # la más reciente


def estructura(candles, k=5):
    """+1 máximos y mínimos crecientes, -1 decrecientes, 0 mixto."""
    ph, pl = pivots(candles["h"], k, "high"), pivots(candles["l"], k, "low")
    if len(ph) < 2 or len(pl) < 2:
        return 0.0
    hh = candles["h"][ph[-1]] > candles["h"][ph[-2]]
    hl = candles["l"][pl[-1]] > candles["l"][pl[-2]]
    if hh and hl:
        return 1.0
    if not hh and not hl:
        return -1.0
    return 0.0


def compresion(closes, n=20, ventana=120):
    """True si el ancho de Bollinger está en el 20 % más bajo de la ventana."""
    if len(closes) < n + 30:
        return False
    anchos = []
    for i in range(max(n, len(closes) - ventana), len(closes) + 1):
        w = closes[i - n:i]
        m = mean(w)
        anchos.append(4 * pstdev(w) / m if m else 0)
    actual = anchos[-1]
    return sum(1 for a in anchos if a <= actual) / len(anchos) <= 0.20


def analizar_tf(candles):
    """Analiza una temporalidad. Devuelve None si no hay velas suficientes."""
    c, h, l, v = candles["c"], candles["h"], candles["l"], candles["v"]
    if len(c) < 60:
        return None
    e50, e200 = ema(c, 50), ema(c, 200)
    r = rsi(c)
    line, s, hist = macd(c)

    # Tendencia: precio vs EMA50, EMA50 vs EMA200, pendiente de la EMA50
    t = [sign(c[-1] - e50[-1])]
    if e200[-1] is not None:
        t.append(sign(e50[-1] - e200[-1]))
    if e50[-6] is not None:
        t.append(sign(e50[-1] - e50[-6]))
    tendencia = mean(t)

    # Momento: RSI centrado en 50 + MACD (cruce y dirección del histograma)
    m_rsi = clamp((r[-1] - 50) / 20)
    m_macd = 0.0
    if hist[-1] is not None and hist[-2] is not None:
        m_macd = 0.6 * sign(hist[-1]) + 0.4 * sign(hist[-1] - hist[-2])
    momento = (m_rsi + m_macd) / 2

    div = divergencia(candles, r)
    d = 0.0 if not div else (1.0 if div["tipo"] == "alcista" else -1.0)

    # Volumen: solo suma si el movimiento reciente va con volumen por encima de la media
    vol = 0.0
    vm = mean(v[-23:-3]) if len(v) >= 23 else 0
    if vm > 0:
        ratio = mean(v[-3:]) / vm
        vol = sign(c[-1] - c[-4]) * clamp(ratio - 1, 0, 1)

    est = estructura(candles)
    comp = {"tendencia": tendencia, "estructura": est, "momento": momento,
            "divergencia": d, "volumen": vol}
    score = sum(PESOS[k] * comp[k] for k in PESOS)
    a = atr(h, l, c)
    return {
        "score": round(score, 3),
        "nota": nota(score),
        "componentes": {k: round(x, 2) for k, x in comp.items()},
        "rsi": round(r[-1], 1),
        "ema50": e50[-1], "ema200": e200[-1],
        "atr_pct": round(100 * a / c[-1], 2) if a else None,
        "divergencia": div,
        "compresion": compresion(c),
        "cierre": c[-1], "t": candles["t"][-1],
    }


def nota(score):
    """Pasa de [-1, +1] a una nota de 0 a 10 (5 = neutral)."""
    return round(5 + 5 * clamp(score), 1)


def etiqueta(score, umbral_fuerte=0.5):
    if score >= umbral_fuerte:
        return "ALCISTA FUERTE"
    if score >= 0.2:
        return "alcista"
    if score <= -umbral_fuerte:
        return "BAJISTA FUERTE"
    if score <= -0.2:
        return "bajista"
    return "neutral"


def combinar(por_tf, pesos_tf, umbral_fuerte=0.5, min_acuerdo=3):
    """Mezcla las temporalidades disponibles según su peso."""
    disp = {tf: a for tf, a in por_tf.items() if a}
    if not disp:
        return None
    total = sum(pesos_tf[tf] for tf in disp)
    score = sum(pesos_tf[tf] * a["score"] for tf, a in disp.items()) / total
    lado = sign(score)
    acuerdo = sum(1 for a in disp.values() if sign(a["score"]) == lado and abs(a["score"]) >= 0.15)
    fuerte = abs(score) >= umbral_fuerte and acuerdo >= min(min_acuerdo, len(disp))
    return {"score": round(score, 3), "nota": nota(score),
            "etiqueta": etiqueta(score, umbral_fuerte) if fuerte or abs(score) < umbral_fuerte
            else ("alcista" if lado > 0 else "bajista"),
            "fuerte": fuerte, "lado": lado, "acuerdo": acuerdo}
