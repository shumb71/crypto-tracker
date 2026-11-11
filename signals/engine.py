"""Motor de señales: indicadores y puntuación de confluencia.

Sin dependencias externas. Todo trabaja sobre velas YA CERRADAS.
La puntuación va de -1 (todo bajista) a +1 (todo alcista). No es una
probabilidad: mide cuántas señales independientes apuntan al mismo lado.
"""
from statistics import mean, pstdev

# Peso de cada bloque dentro de una temporalidad (suman 1)
PESOS = {"tendencia": 0.35, "estructura": 0.15, "momento": 0.25,
         "divergencia": 0.15, "volumen": 0.10}


def _r(x):
    """Redondeo corto (8 cifras significativas) para guardar números en el JSON."""
    return float(f"{x:.8g}")


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
        det = {"p": [_r(serie[a]), _r(serie[b])], "i": [_r(ra), _r(rb)]}
        if tipo == "alcista" and serie[b] < serie[a] and rb > ra + 1 and ra < 50:
            found.append({"tipo": tipo, "t": candles["t"][b], **det})
        if tipo == "bajista" and serie[b] > serie[a] and rb < ra - 1 and ra > 50:
            found.append({"tipo": tipo, "t": candles["t"][b], **det})
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


# ---------------------------------------------------------------------------
# Estado de la tendencia: agotamiento, lateral y ruptura (EMA 10/55, ADX, Squeeze)
# ---------------------------------------------------------------------------
# Umbrales medidos en ATR para que valgan igual en BTC que en una altcoin.
# Están elegidos por criterio, no ajustados con datos reales: el backtest dirá si hay que moverlos.

def sma(vals, n):
    out = [None] * len(vals)
    if len(vals) < n:
        return out
    s = sum(vals[:n])
    out[n - 1] = s / n
    for i in range(n, len(vals)):
        s += vals[i] - vals[i - n]
        out[i] = s / n
    return out


def linreg_fin(y):
    """Valor final de la recta de mínimos cuadrados ajustada a y (como linreg(x, n, 0) de Pine)."""
    n = len(y)
    xm, ym = (n - 1) / 2, sum(y) / n
    sxx = sum((i - xm) ** 2 for i in range(n))
    sxy = sum((i - xm) * (y[i] - ym) for i in range(n))
    return ym + (sxy / sxx) * (n - 1 - xm)


def squeeze_hist(h, l, c, n=20):
    """Histograma del Squeeze Momentum (LazyBear): regresión lineal de
    cierre - media(media(máx, mín), SMA) sobre n velas."""
    out = [None] * len(c)
    if len(c) < 2 * n - 1:
        return out
    sm = sma(c, n)
    raw = [None] * len(c)
    for i in range(n - 1, len(c)):
        hh, ll = max(h[i - n + 1:i + 1]), min(l[i - n + 1:i + 1])
        raw[i] = c[i] - ((hh + ll) / 2 + sm[i]) / 2
    for i in range(2 * n - 2, len(c)):
        out[i] = linreg_fin(raw[i - n + 1:i + 1])
    return out


def adx(h, l, c, n=14):
    """ADX de Wilder, alineado con las velas (None al principio)."""
    m = len(c)
    out = [None] * m
    if m < 2 * n + 1:
        return out
    pdm, mdm, tr = [], [], []
    for i in range(1, m):
        up, dn = h[i] - h[i - 1], l[i - 1] - l[i]
        pdm.append(up if up > dn and up > 0 else 0.0)
        mdm.append(dn if dn > up and dn > 0 else 0.0)
        tr.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
    sp, sm_, st = sum(pdm[:n]), sum(mdm[:n]), sum(tr[:n])

    def dx():
        if st == 0:
            return 0.0
        pdi, mdi = 100 * sp / st, 100 * sm_ / st
        return 0.0 if pdi + mdi == 0 else 100 * abs(pdi - mdi) / (pdi + mdi)

    dxs = [dx()]
    for j in range(n, len(tr)):
        sp, sm_, st = sp - sp / n + pdm[j], sm_ - sm_ / n + mdm[j], st - st / n + tr[j]
        dxs.append(dx())
    a = mean(dxs[:n])
    out[2 * n - 1] = a
    for k in range(n, len(dxs)):
        a = (a * (n - 1) + dxs[k]) / n
        out[n + k] = a
    return out


def atr_serie(h, l, c, n=14):
    out = [None] * len(c)
    if len(c) <= n:
        return out
    tr = [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, len(c))]
    a = mean(tr[:n])
    out[n] = a
    for j in range(n, len(tr)):
        a = (a * (n - 1) + tr[j]) / n
        out[j + 1] = a
    return out


def divergencia_squeeze(candles, hist, atr_v, k=5, max_sep=60, reciente=20):
    """Divergencia entre el precio y el histograma del Squeeze Momentum.

    Bajista: el precio marca un máximo igual o mayor, pero la cresta del monitor es menor.
    Alcista: el precio marca un mínimo igual o menor, pero el valle del monitor es menos profundo.
    """
    n = len(candles["c"])
    found = []
    for kind, serie, tipo in (("high", candles["h"], "bajista"), ("low", candles["l"], "alcista")):
        p = pivots(serie, k, kind)
        if len(p) < 2:
            continue
        a, b = p[-2], p[-1]
        if n - 1 - b > reciente or not (k <= b - a <= max_sep):
            continue
        va = [x for x in hist[a - 2:a + 3] if x is not None]
        vb = [x for x in hist[b - 2:b + 3] if x is not None]
        if not va or not vb:
            continue
        if tipo == "bajista":
            pa, pb = max(va), max(vb)
            if serie[b] >= serie[a] - 0.25 * atr_v and pa > 0 and 0 < pb < 0.85 * pa:
                found.append({"tipo": tipo, "t": candles["t"][b],
                              "p": [_r(serie[a]), _r(serie[b])], "i": [_r(pa), _r(pb)]})
        else:
            pa, pb = min(va), min(vb)
            if serie[b] <= serie[a] + 0.25 * atr_v and pa < 0 and 0 > pb > 0.85 * pa:
                found.append({"tipo": tipo, "t": candles["t"][b],
                              "p": [_r(serie[a]), _r(serie[b])], "i": [_r(pa), _r(pb)]})
    return max(found, key=lambda d: d["t"]) if found else None


def combinar_div(div_rsi, div_sq):
    """Una sola divergencia: si coinciden RSI y Squeeze cuenta como una, más fiable."""
    if div_rsi and div_sq and div_rsi["tipo"] != div_sq["tipo"]:
        return None  # se contradicen
    base = div_rsi or div_sq
    if not base:
        return None
    return {"tipo": base["tipo"], "rsi": bool(div_rsi), "squeeze": bool(div_sq), "t": base["t"],
            "det": {"rsi": div_rsi, "squeeze": div_sq}}


def tendencia_previa(e10, e55, atr_v, ventana=80, umbral=1.5, pico_min=3.0):
    """(dirección, pico): la última tendencia clara de las últimas `ventana` velas y su
    separación máxima entre EMA 10 y EMA 55, medida en ATR. (0, 0) si no hubo una
    tendencia de verdad (separación máxima menor que `pico_min` ATR)."""
    n = len(e55)
    sep = [(e10[i] - e55[i]) / atr_v for i in range(max(0, n - ventana), n)
           if e10[i] is not None and e55[i] is not None]
    for s in reversed(sep):
        if abs(s) >= umbral:
            d = sign(s)
            pico = max(d * x for x in sep)
            return (d, pico) if pico >= pico_min else (0, 0.0)
    return 0, 0.0


def dobles(candles, e10, e55, atr_v, k=5):
    """Doble techo (+1) o doble suelo (-1): el último extremo no logra superar al anterior
    (margen 0,25 ATR) y queda a menos de 1,5 ATR de él, tras una tendencia en esa dirección."""
    h, l, c, n = candles["h"], candles["l"], candles["c"], len(candles["c"])
    res = {}
    for kind, serie, d in (("high", h, 1), ("low", l, -1)):
        p = pivots(serie, k, kind)
        if len(p) < 2:
            continue
        a, b = p[-2], p[-1]
        if not (k + 1 <= b - a <= 60) or n - 1 - b > 30 or e10[a] is None or e55[a] is None:
            continue
        if sign(e10[a] - e55[a]) != d or sign(c[a] - e55[a]) != d:
            continue
        dif = d * (serie[b] - serie[a])
        if dif > 0.25 * atr_v or dif < -1.5 * atr_v:
            continue
        ext = max(serie[a:]) if d == 1 else min(serie[a:])
        if d * (ext - serie[a]) > 0.25 * atr_v:
            continue  # ya lo ha superado: deja de ser un doble techo/suelo
        res[d] = {"tipo": "doble_techo" if d == 1 else "doble_suelo", "t": candles["t"][b],
                  "p": [_r(serie[a]), _r(serie[b])]}
    return res


def medias_juntas(e10, e55, c, atr_v, pico):
    """EMA 10 y 55 casi pegadas (<40 % de su separación máxima) y precio aplanado sobre la 55."""
    sep = abs(e10[-1] - e55[-1]) / atr_v
    return pico >= 2.5 and sep <= 0.4 * pico and abs(c[-1] - e55[-1]) <= 1.0 * atr_v


def adx_detalle(adxs, h, l, c, d, atr_v):
    """Desglose de la señal «ADX cediendo»: pico reciente, si cae y a cuántos ATR del extremo está el precio."""
    ult = [x for x in adxs[-40:] if x is not None]
    if len(ult) < 10 or adxs[-1] is None or adxs[-4] is None:
        return {"ok": False, "pico": None, "cae": False, "cerca": False, "dist": None}
    pico = max(ult)
    cae = pico >= 25 and adxs[-1] <= adxs[-4] - 0.5 and adxs[-1] <= pico - 3
    extremo = max(h[-20:]) if d == 1 else min(l[-20:])
    dist = d * (extremo - c[-1]) / atr_v
    cerca = dist <= 1.5
    return {"ok": bool(cae and cerca), "pico": pico, "cae": bool(cae), "cerca": bool(cerca), "dist": dist}


def adx_cede(adxs, h, l, c, d, atr_v):
    """ADX girando a la baja (-0,5 en 3 velas y 3 puntos bajo su pico, con pico de al menos 25)
    mientras el precio sigue a menos de 1,5 ATR del extremo de la tendencia."""
    return adx_detalle(adxs, h, l, c, d, atr_v)["ok"]


def es_lateral(adxs, e10, e55, h, l, atr_v):
    """ADX por debajo de 25, medias pegadas y rango de las últimas 20 velas de menos de 7 ATR."""
    if adxs[-1] is None:
        return False
    return (adxs[-1] < 25 and abs(e10[-1] - e55[-1]) / atr_v < 1.5
            and (max(h[-20:]) - min(l[-20:])) / atr_v <= 7)


def ruptura_en(candles, e10, e55, adxs, atrs, i, ancho=20):
    """¿La vela i rompe un lateral? Mide fuerza (vela ≥ 1,5 ATR), volumen (≥ 1,3× media)
    y cruce de EMA 10/55 a favor, hasta la última vela. Devuelve dict o None."""
    h, l, c, v, t = (candles[k] for k in "hlcvt")
    n = len(c)
    if i < ancho + 8 or atrs[i - 1] is None or adxs[i - 1] is None or e55[i - 1] is None:
        return None
    a = atrs[i - 1]
    caja_h, caja_l = max(h[i - ancho:i]), min(l[i - ancho:i])
    if (adxs[i - 1] >= 25 or abs(e10[i - 1] - e55[i - 1]) / a >= 1.5
            or (caja_h - caja_l) / a > 7):
        return None  # antes de la vela no había lateral
    d = 1 if c[i] > caja_h else -1 if c[i] < caja_l else 0
    if d == 0 or d * (c[-1] - (caja_h if d == 1 else caja_l)) <= 0:
        return None  # no rompe, o el precio ya ha vuelto dentro de la caja
    vela = (h[i] - l[i]) / a
    vm = mean(v[i - ancho:i])
    vol = v[i] / vm if vm > 0 else 0.0
    cruce = sign(e10[-1] - e55[-1]) == d and any(
        sign(e10[j] - e55[j]) == d and sign(e10[j - 1] - e55[j - 1]) != d
        for j in range(max(1, i - 7), n))
    return {"dir": d, "t": t[i], "vela_atr": round(vela, 2), "vol_x": round(vol, 2),
            "cruce": bool(cruce), "confirmada": bool(vela >= 1.5 and vol >= 1.3 and cruce)}


def tendencia_estado(candles, div_rsi, min_agotamiento=2):
    """Estado de la tendencia en una temporalidad.

    estado: sana | agotandose | lateral | ruptura | ruptura_dudosa | sin_tendencia | sin_datos
    Las 4 señales de agotamiento: divergencia (RSI o Squeeze, cuenta como una), doble
    techo/suelo, medias 10/55 juntándose y ADX cediendo. Solo cuentan las que van en el
    sentido de la tendencia que se está agotando.
    """
    h, l, c = candles["h"], candles["l"], candles["c"]
    n = len(c)
    atrs = atr_serie(h, l, c)
    atr_v = atrs[-1]
    hist = squeeze_hist(h, l, c)
    div_sq = divergencia_squeeze(candles, hist, atr_v) if atr_v else None
    div = combinar_div(div_rsi, div_sq)
    base = {"estado": "sin_datos", "dir": 0, "n_senales": 0, "min": min_agotamiento,
            "senales": {"divergencia": False, "doble": False, "compresion": False, "adx": False},
            "divergencia": div, "doble": None, "ruptura": None,
            "adx": None, "squeeze": round(hist[-1], 4) if hist[-1] is not None else None}
    if n < 130 or not atr_v:
        return base
    e10, e55 = ema(c, 10), ema(c, 55)
    adxs = adx(h, l, c)
    d, pico = tendencia_previa(e10, e55, atr_v)
    if d and max((x for x in adxs[-60:] if x is not None), default=0) < 25:
        d = 0  # sin ADX alto no hubo tendencia que agotar
    base["adx"] = round(adxs[-1], 1) if adxs[-1] is not None else None
    base["dir"] = d

    if d:
        dob = dobles(candles, e10, e55, atr_v).get(d)
        sen = {
            "divergencia": bool(div) and (div["tipo"] == "bajista") == (d == 1),
            "doble": dob is not None,
            "compresion": medias_juntas(e10, e55, c, atr_v, pico),
            "adx": adx_cede(adxs, h, l, c, d, atr_v),
        }
        base.update(senales=sen, n_senales=sum(sen.values()), doble=dob)

    # ¿ruptura de un lateral en las últimas 4 velas? (la primera vela que sale de la caja)
    rup = None
    for i in range(n - 4, n):
        rup = ruptura_en(candles, e10, e55, adxs, atrs, i)
        if rup:
            break
    base["ruptura"] = rup

    if rup and rup["confirmada"]:
        base["estado"] = "ruptura"
    elif rup:
        base["estado"] = "ruptura_dudosa"
    elif es_lateral(adxs, e10, e55, h, l, atr_v):
        base["estado"] = "lateral"
    elif d:
        base["estado"] = "agotandose" if base["n_senales"] >= min_agotamiento else "sana"
    else:
        base["estado"] = "sin_tendencia"
    return base


def analizar_tf(candles, min_agotamiento=2):
    """Analiza una temporalidad. Devuelve None si no hay velas suficientes."""
    c, h, l, v = candles["c"], candles["h"], candles["l"], candles["v"]
    if len(c) < 60:
        return None
    e55, e200 = ema(c, 55), ema(c, 200)
    r = rsi(c)
    line, s, hist = macd(c)

    # Tendencia: precio vs EMA55, EMA55 vs EMA200, pendiente de la EMA55
    t = [sign(c[-1] - e55[-1])]
    if e200[-1] is not None:
        t.append(sign(e55[-1] - e200[-1]))
    if e55[-6] is not None:
        t.append(sign(e55[-1] - e55[-6]))
    tendencia = mean(t)

    # Momento: RSI centrado en 50 + MACD (cruce y dirección del histograma)
    m_rsi = clamp((r[-1] - 50) / 20)
    m_macd = 0.0
    if hist[-1] is not None and hist[-2] is not None:
        m_macd = 0.6 * sign(hist[-1]) + 0.4 * sign(hist[-1] - hist[-2])
    momento = (m_rsi + m_macd) / 2

    tend = tendencia_estado(candles, divergencia(candles, r), min_agotamiento)
    div = tend["divergencia"]  # RSI y/o Squeeze, ya combinadas en una sola
    # Una divergencia confirmada por RSI y Squeeze pesa más que la de un solo indicador
    d = 0.0 if not div else ((1.0 if div["rsi"] and div["squeeze"] else 0.6)
                             * (1.0 if div["tipo"] == "alcista" else -1.0))

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
        "ema55": e55[-1], "ema200": e200[-1],
        "atr_pct": round(100 * a / c[-1], 2) if a else None,
        "divergencia": div,
        "tendencia": tend,
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
