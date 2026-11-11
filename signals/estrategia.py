"""Capa didáctica y de estrategia (guía TradingLatino, solo compras).

Toma lo que ya calcula engine.analizar_tf y añade, para cada temporalidad:
  porques              por qué la nota es la que es (5 bloques, con sus números)
  tendencia_explicada  estado de la tendencia y las 4 señales de agotamiento, explicadas
  escenarios           qué confirmaría o anularía la lectura actual, con niveles concretos
  estrategia           comprobaciones de la guía: entrada, zonas no operables, salida y checklist
  guia                 para qué sirve cada temporalidad según la matriz de la guía

Solo AÑADE información al resultado: no cambia puntuaciones ni avisos.
Los umbrales (en ATR o en % del rango) están elegidos por criterio, no ajustados con datos reales.
"""
from statistics import mean

import engine

VENTANA_RANGO = 50      # velas para medir "parte baja / media / alta" del rango
VENTANA_POC = 100       # velas para el perfil de volumen aproximado
MIN_VELAS = 130         # mismas que exige engine.tendencia_estado

GUIA_TF = {
    "1h": ("8 a 12 horas", "Operativa intradía y ajuste de la entrada",
           "Buscar entradas rápidas al terminar las correcciones"),
    "4h": ("24 a 48 horas", "Trading táctico (futuros con stop loss)",
           "Esperar el retroceso a la EMA 55 con valle rojo"),
    "1d": ("10 a 12 días", "Trading de posición (spot o futuros)",
           "Respetar la tendencia; apartarse si no hay patrón"),
    "1w": ("3 a 6 meses", "Inversión de medio plazo en spot",
           "Buscar zonas de soporte para compras escalonadas"),
}


# ----------------------------------------------------------------- formato

def eu(x, dec=1):
    """Número con formato español: 1.234,5"""
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pr(x):
    """Precio con los decimales que toquen según su tamaño."""
    return eu(x, 0 if x >= 10_000 else 1 if x >= 100 else 2 if x >= 1 else 5)


def sg(x):
    """Valor de un oscilador con 3 cifras significativas."""
    return f"{x:.3g}".replace(".", ",")


def cap(s):
    """Pone la primera letra en mayúscula sin tocar el resto (capitalize() pasaría EMA a ema)."""
    return s[:1].upper() + s[1:]


ESTADOS = {"sana": "sana", "agotandose": "agotándose", "lateral": "lateral", "ruptura": "ruptura confirmada",
           "ruptura_dudosa": "posible ruptura", "sin_tendencia": "sin tendencia", "sin_datos": "sin datos"}


def lado(d):
    return "alcista" if d > 0 else "bajista"


# ----------------------------------------------------------------- cálculos

def series(candles):
    h, l, c = candles["h"], candles["l"], candles["c"]
    return {"e10": engine.ema(c, 10), "e55": engine.ema(c, 55),
            "e200": engine.ema(c, 200), "adx": engine.adx(h, l, c), "sq": engine.squeeze_hist(h, l, c),
            "atr": engine.atr_serie(h, l, c), "rsi": engine.rsi(c), "macd": engine.macd(c)[2]}


def color_squeeze(h0, h1):
    """Color del histograma según tu guía: depende del signo y de si sube o baja."""
    if h0 is None or h1 is None:
        return None
    if h0 >= 0:
        return "verde oscuro (acelera al alza)" if h0 > h1 else "verde claro (pierde tracción)"
    return "rojo oscuro (acelera a la baja)" if h0 < h1 else "rojo claro (pierde fuerza)"


def posicion_rango(candles, ventana=VENTANA_RANGO):
    """Dónde está el precio dentro del rango de las últimas `ventana` velas (0 = suelo, 1 = techo)."""
    lo, hi = min(candles["l"][-ventana:]), max(candles["h"][-ventana:])
    if hi <= lo:
        return 0.5, lo, hi, "media"
    pos = (candles["c"][-1] - lo) / (hi - lo)
    return pos, lo, hi, "baja" if pos <= 1 / 3 else "alta" if pos >= 2 / 3 else "media"


def poc_aproximado(candles, ventana=VENTANA_POC, bins=48):
    """Punto de control (POC) aproximado: el precio con más volumen, repartiendo el volumen de cada
    vela de forma uniforme entre los precios que recorre. No es el de TradingView."""
    h, l, v = candles["h"][-ventana:], candles["l"][-ventana:], candles["v"][-ventana:]
    lo, hi = min(l), max(h)
    if hi <= lo:
        return None
    paso = (hi - lo) / bins
    vol = [0.0] * bins
    for hh, ll, vv in zip(h, l, v):
        a, b = min(bins - 1, int((ll - lo) / paso)), min(bins - 1, int((hh - lo) / paso))
        for k in range(a, b + 1):
            vol[k] += vv / (b - a + 1)
    return lo + (max(range(bins), key=vol.__getitem__) + 0.5) * paso


def item(id_, titulo, ok, texto, regla=None, donde=None, **extra):
    d = {"id": id_, "titulo": titulo, "ok": ok, "texto": texto}
    if regla:
        d["regla"] = regla
    if donde:
        d["donde"] = donde
    d.update(extra)
    return d


# ----------------------------------------------------------------- por qué esta nota

def texto_div(div):
    """Describe una divergencia con los números de cada indicador que la ve."""
    partes = []
    for fuente, nombre in (("squeeze", "Squeeze"), ("rsi", "RSI")):
        d = (div.get("det") or {}).get(fuente)
        if not d:
            continue
        (pa, pb), (ia, ib) = d["p"], d["i"]
        if div["tipo"] == "bajista":
            partes.append(f"el precio hizo un máximo de {pr(pb)} (el anterior, {pr(pa)}) pero el {nombre} "
                          f"marcó {sg(ib)} frente a {sg(ia)}: menos fuerza compradora")
        else:
            partes.append(f"el precio hizo un mínimo de {pr(pb)} (el anterior, {pr(pa)}) pero el {nombre} "
                          f"marcó {sg(ib)} frente a {sg(ia)}: menos presión vendedora")
    return "; ".join(partes)


def porques(a, candles, S):
    c, h, l, v = candles["c"], candles["h"], candles["l"], candles["v"]
    comp = a["componentes"]
    bloques = []

    def bloque(id_, titulo, texto, donde):
        peso = engine.PESOS[id_]
        bloques.append({"id": id_, "titulo": titulo, "valor": comp[id_], "peso": peso,
                        "aporta": round(comp[id_] * peso, 3), "texto": texto, "donde": donde})

    # Tendencia de fondo: EMA 55 / EMA 200
    e55, e200 = S["e55"], S["e200"]
    t = [f"el precio ({pr(c[-1])}) está {'por encima' if c[-1] > e55[-1] else 'por debajo'} de la EMA 55 ({pr(e55[-1])})"]
    t.append(f"la EMA 55 está {'por encima' if e55[-1] > e200[-1] else 'por debajo'} de la EMA 200 ({pr(e200[-1])})"
             if e200[-1] is not None else "aún no hay velas para calcular la EMA 200")
    if e55[-6] is not None:
        t.append("la EMA 55 " + ("sube" if e55[-1] > e55[-6] else "baja"))
    v_ = comp["tendencia"]
    concl = ("mandan los compradores" if v_ >= 0.5 else "mandan los vendedores" if v_ <= -0.5
             else "las señales van mezcladas")
    bloque("tendencia", "Tendencia de fondo", f"{cap(t[0])}; " + "; ".join(t[1:]) + f". Conclusión: {concl}.",
           "Pon las EMA 55 y 200 en el gráfico (la 55 es la misma de tu guía). La EMA 10 junto a la 55 se usa aparte, "
           "para ver si la tendencia se agota: mira «Estado de la tendencia».")

    # Estructura de máximos y mínimos
    ph, pl = engine.pivots(h, 5, "high"), engine.pivots(l, 5, "low")
    if len(ph) >= 2 and len(pl) >= 2:
        hh, hl = h[ph[-1]] > h[ph[-2]], l[pl[-1]] > l[pl[-2]]
        txt = (f"El último máximo ({pr(h[ph[-1]])}) es {'más alto' if hh else 'más bajo'} que el anterior "
               f"({pr(h[ph[-2]])}) y el último mínimo ({pr(l[pl[-1]])}) es {'más alto' if hl else 'más bajo'} que el "
               f"anterior ({pr(l[pl[-2]])}). ")
        txt += ("Máximos y mínimos crecientes: estructura alcista." if hh and hl else
                "Máximos y mínimos decrecientes: estructura bajista." if not hh and not hl else
                "Estructura mixta: no confirma ninguna dirección.")
    else:
        txt = "Todavía no hay suficientes giros claros para medir la estructura."
    bloque("estructura", "Estructura (máximos y mínimos)", txt,
           "Marca a ojo los dos últimos máximos y los dos últimos mínimos: ¿van subiendo o bajando?")

    # Momento: RSI y MACD
    r, m0, m1 = S["rsi"][-1], S["macd"][-1], S["macd"][-2]
    zona = ("sobrecompra: puede estar cansado" if r >= 70 else "por encima de 50: manda el impulso comprador" if r >= 50
            else "por debajo de 50: manda el impulso vendedor" if r > 30 else "sobreventa: puede estar cansado a la baja")
    bloque("momento", "Momento (RSI y MACD)",
           f"El RSI está en {eu(r)} ({zona}). El histograma del MACD es {'positivo' if m0 > 0 else 'negativo'} y "
           f"{'sube' if m0 > m1 else 'baja'} ({sg(m1)} → {sg(m0)}).",
           "Panel del RSI (línea frente a la de 50) y panel del MACD (barras del histograma).")

    # Divergencias
    div = a["divergencia"]
    if div:
        fuente = "RSI y Squeeze" if div["rsi"] and div["squeeze"] else "RSI" if div["rsi"] else "Squeeze"
        txt = (f"Hay divergencia {div['tipo']} ({fuente}): {texto_div(div)}. "
               + ("Coinciden los dos indicadores, así que es más fiable. " if div["rsi"] and div["squeeze"] else "")
               + ("Es una señal de que la subida pierde fuerza." if div["tipo"] == "bajista"
                  else "Es una señal de que la bajada pierde fuerza."))
    else:
        txt = "No hay divergencia reciente (últimas ~20 velas) entre el precio y el RSI o el Squeeze."
    bloque("divergencia", "Divergencias", txt,
           "Compara las dos últimas crestas (o valles) del Squeeze con los dos últimos máximos (o mínimos) del precio.")

    # Volumen
    vm = mean(v[-23:-3]) if len(v) >= 23 else 0
    if vm > 0:
        ratio = mean(v[-3:]) / vm
        mov = "alcista" if c[-1] > c[-4] else "bajista"
        txt = (f"El volumen de las 3 últimas velas es {eu(ratio)}× la media de las 20 anteriores. "
               + (f"Con volumen alto el movimiento {mov} reciente es más fiable." if ratio > 1.15
                  else "Volumen normal o bajo: no refuerza ni resta."))
    else:
        txt = "No hay volumen suficiente para valorar."
    bloque("volumen", "Volumen", txt, "Barras de volumen bajo el gráfico: las 3 últimas frente a las 20 anteriores.")

    top = max(bloques, key=lambda b: abs(b["aporta"]))
    resumen = (f"Nota {eu(a['nota'])}/10. El bloque que más pesa ahora es «{top['titulo']}» "
               f"({'suma' if top['aporta'] > 0 else 'resta'} {eu(abs(top['aporta']), 2)}). "
               "Cada bloque va de −1 (todo bajista) a +1 (todo alcista) y se multiplica por su peso.")
    return {"resumen": resumen, "bloques": bloques}


# ----------------------------------------------------------------- estado de la tendencia

def explicar_tendencia(a, candles, S):
    t = a["tendencia"]
    c, h, l = candles["c"], candles["h"], candles["l"]
    if t["estado"] == "sin_datos":
        return {"estado": "sin_datos", "resumen": f"Aún no hay velas suficientes (hacen falta {MIN_VELAS}) "
                "para valorar el estado de la tendencia.", "senales": []}
    atr_v, e10, e55, adxs = S["atr"][-1], S["e10"], S["e55"], S["adx"]
    d, pico = t["dir"], engine.tendencia_previa(e10, e55, atr_v)[1]
    sep = abs(e10[-1] - e55[-1]) / atr_v
    ancho = (max(h[-20:]) - min(l[-20:])) / atr_v
    e, n, minimo = t["estado"], t["n_senales"], t["min"]
    sen = []
    if d:
        L = lado(d)
        div = t["divergencia"]
        if t["senales"]["divergencia"]:
            tx = f"{cap(texto_div(div))}."
            if div["rsi"] and div["squeeze"]:
                tx += " Coinciden RSI y Squeeze: cuenta como una sola señal, pero más fiable."
        elif div:
            tx = f"Hay una divergencia {div['tipo']}, pero va contra la tendencia {L} que se evalúa: no cuenta."
        else:
            tx = "No hay divergencia reciente entre el precio y el Squeeze o el RSI."
        sen.append(item("divergencia", "Divergencia en el monitor", t["senales"]["divergencia"], tx, "Guía §5.2",
                        "Ventana del Squeeze: compara las dos últimas crestas verdes (o valles rojos) con los máximos (o mínimos) del precio."))
        dob = t["doble"]
        tx = (f"Dos {'máximos' if d > 0 else 'mínimos'} casi iguales ({pr(dob['p'][0])} y {pr(dob['p'][1])}): el segundo "
              f"no logró superar al primero. Es un doble {'techo' if d > 0 else 'suelo'}."
              if dob else f"No hay doble {'techo' if d > 0 else 'suelo'}: el precio no se ha quedado repitiendo el último extremo.")
        sen.append(item("doble", "Doble techo / doble suelo", t["senales"]["doble"], tx, "Guía §5.1 (el precio deja de hacer extremos nuevos)",
                        "Busca dos picos (o dos suelos) casi a la misma altura sin que el segundo supere al primero."))
        tx = (f"La separación entre la EMA 10 y la EMA 55 es de {eu(sep)} ATR (en lo más fuerte de la tendencia llegó a "
              f"{eu(pico)}) y el precio está a {eu(abs(c[-1] - e55[-1]) / atr_v)} ATR de la EMA 55. "
              + ("Las medias se juntan y el precio se pega a la 55: la tendencia se aplana." if t["senales"]["compresion"]
                 else "Siguen separadas: la tendencia mantiene su abanico."))
        sen.append(item("compresion", "Medias 10 y 55 juntándose", t["senales"]["compresion"], tx, "Guía §5.1",
                        "Línea azul (EMA 10) y línea café (EMA 55): ¿se están acercando y el precio oscila pegado a la café?"))
        a0, a3 = adxs[-1], adxs[-4]
        dt = engine.adx_detalle(adxs, h, l, c, d, atr_v)
        pk = dt["pico"] if dt["pico"] is not None else a0
        tx = f"El ADX está en {eu(a0)} (hace 3 velas, {eu(a3)}; su pico reciente, {eu(pk)}). "
        if dt["ok"]:
            tx += "Gira a la baja mientras el precio intenta seguir: el movimiento pierde respaldo."
        elif dt["cae"] and not dt["cerca"]:
            tx += (f"Está cayendo, pero el precio ya está a {eu(dt['dist'])} ATR de su extremo: no está «intentando seguir» "
                   "la tendencia, así que de momento no cuenta como señal.")
        elif dt["pico"] is not None and dt["pico"] < 25:
            tx += "Nunca llegó a 25 en las últimas 40 velas: no hubo fuerza que perder."
        else:
            tx += "Todavía no muestra pérdida clara de fuerza."
        sen.append(item("adx", "ADX perdiendo fuerza", t["senales"]["adx"], tx, "Guía §5.2 y §2.3",
                        "Línea blanca del ADX: ¿apunta hacia abajo mientras el precio sigue empujando?"))

    if e == "sana":
        res = f"La tendencia {lado(d)} sigue sana: solo {n} de 4 señales de agotamiento (hacen falta {minimo})."
    elif e == "agotandose":
        res = f"La tendencia {lado(d)} se está agotando: se cumplen {n} de 4 señales (hacen falta {minimo})."
    elif e == "lateral":
        res = (f"El precio está en un lateral: ADX {eu(adxs[-1])} (bajo 25), EMA 10 y 55 a {eu(sep)} ATR una de otra y un "
               f"rango de {eu(ancho)} ATR en 20 velas. Según la guía (§5.3), las tendencias suelen pasar por un lateral antes de girar.")
    elif e in ("ruptura", "ruptura_dudosa"):
        r = t["ruptura"]
        falta = [x for x, ok in (("fuerza de la vela", r["vela_atr"] >= 1.5), ("volumen", r["vol_x"] >= 1.3),
                                 ("cruce de medias", r["cruce"])) if not ok]
        res = (f"El precio salió del lateral {'al alza' if r['dir'] > 0 else 'a la baja'}: vela de {eu(r['vela_atr'])}× ATR "
               f"(mínimo 1,5), volumen de {eu(r['vol_x'])}× la media (mínimo 1,3) y "
               f"{'con' if r['cruce'] else 'sin'} cruce de las EMA 10/55. ")
        res += ("Cumple las tres condiciones: ruptura confirmada, que es lo que la guía pide para dar por cambiada la tendencia."
                if e == "ruptura" else f"Falta: {', '.join(falta)}. La guía exige las tres a la vez, así que aún no se da por confirmada.")
    elif e == "sin_tendencia":
        res = (f"No hay una tendencia clara que agotar (separación máxima de las EMA 10/55 en el último tramo: {eu(pico)} ATR; "
               "hace falta al menos 3, con ADX por encima de 25).")
    else:
        res = ""
    return {"estado": e, "dir": d, "n_senales": n, "min": minimo, "resumen": res, "senales": sen}


# ----------------------------------------------------------------- escenarios

def escenarios(a, candles, S):
    t = a["tendencia"]
    e = t["estado"]
    if e == "sin_datos":
        return []
    c, h, l = candles["c"], candles["h"], candles["l"]
    atr_v, e55 = S["atr"][-1], S["e55"][-1]
    d = t["dir"]
    ph, pl = engine.pivots(h, 5, "high"), engine.pivots(l, 5, "low")
    ult_max = h[ph[-1]] if ph else max(h[-20:])
    ult_min = l[pl[-1]] if pl else min(l[-20:])
    caja_h, caja_l = max(h[-20:]), min(l[-20:])
    out = []

    def esc(tipo, cuando, entonces):
        out.append({"tipo": tipo, "cuando": cuando, "entonces": entonces})

    if e == "sana":
        esc("vigila", f"El precio aguanta {'sobre' if d > 0 else 'bajo'} la EMA 55 ({pr(e55)}) y el ADX no gira a la baja",
            "La tendencia sigue sana; no hay motivo para dudar de ella.")
        esc("debilita", f"Aparece una divergencia en el Squeeze o el ADX empieza a caer ({eu(S['adx'][-1])} ahora)",
            "Sería la primera señal de agotamiento; con una segunda, el panel y el bot lo marcan como «agotándose».")
    elif e == "agotandose":
        niv = pr(e55)
        esc("confirma", f"El precio cierra {'por debajo' if d > 0 else 'por encima'} de la EMA 55 ({niv}), la EMA 10 cruza "
            f"{'por debajo' if d > 0 else 'por encima'} de la 55 y entra volumen",
            "Se confirmaría el giro. Lo habitual (guía §5.3) es que antes pase por un lateral.")
        esc("anula", f"El precio supera el último {'máximo' if d > 0 else 'mínimo'} ({pr(ult_max if d > 0 else ult_min)}) "
            f"con el Squeeze marcando {'una cresta mayor' if d > 0 else 'un valle más profundo'} y el ADX volviendo a subir",
            "Se anularía el agotamiento: la tendencia retoma fuerza.")
    elif e == "lateral":
        esc("confirma", f"Cierre por encima de {pr(caja_h)} con una vela de al menos {pr(1.5 * atr_v)} de recorrido (1,5 ATR), "
            "volumen de 1,3× la media o más y la EMA 10 cruzando sobre la 55",
            "Ruptura alcista confirmada: la guía da por cambiada la tendencia.")
        esc("confirma", f"Cierre por debajo de {pr(caja_l)} con las mismas tres condiciones",
            "Ruptura bajista confirmada.")
        esc("vigila", "Mientras no rompa", "El centro del lateral es zona no operable según la guía: ni compra ni venta con ventaja.")
    elif e in ("ruptura", "ruptura_dudosa"):
        r = t["ruptura"]
        falta = [x for x, ok in (("una vela más fuerte", r["vela_atr"] >= 1.5), ("más volumen", r["vol_x"] >= 1.3),
                                 ("el cruce de medias", r["cruce"])) if not ok]
        if e == "ruptura_dudosa":
            esc("confirma", f"Llega {', '.join(falta)}", "La ruptura pasaría a confirmada.")
        esc("anula", f"El precio vuelve dentro del lateral ({pr(caja_l)} – {pr(caja_h)})", "Sería una falsa ruptura.")
    else:  # sin_tendencia
        esc("vigila", "Se forma una tendencia: EMA 10 y 55 separadas al menos 3 ATR y ADX por encima de 25",
            "Entonces tendría sentido vigilar su agotamiento.")
    return out


# ----------------------------------------------------------------- tu estrategia (guía)

def estrategia(a, candles, S):
    t = a["tendencia"]
    c, h, l = candles["c"], candles["h"], candles["l"]
    atr_v, e55, adxs, sq = S["atr"][-1], S["e55"][-1], S["adx"], S["sq"]
    pos, lo, hi, nombre = posicion_rango(candles)
    dist55 = (c[-1] - e55) / atr_v
    poc = poc_aproximado(candles)
    dist_poc = (c[-1] - poc) / atr_v if poc else None
    a0, a2 = adxs[-1], adxs[-3]
    pend = a0 - a2
    h0, h1 = sq[-1], sq[-2]
    estado = t["estado"]
    rango_txt = f"{pr(lo)} – {pr(hi)}"

    # --- Entrada en long (tabla de la guía §3)
    c1_lat = estado == "lateral" and nombre == "baja"
    c1 = -0.5 <= dist55 <= 1.5 or c1_lat
    c2 = h0 < 0 and h0 > h1
    c3 = pend < 0
    c4 = dist_poc is not None and -0.5 <= dist_poc <= 1.5
    entrada = [
        item("precio", "Precio en la EMA 55 o en la parte baja del lateral", c1,
             f"El precio está a {eu(abs(dist55))} ATR {'por encima' if dist55 >= 0 else 'por debajo'} de la EMA 55 ({pr(e55)}) "
             f"y en el {eu(100 * pos, 0)} % del rango de las últimas {VENTANA_RANGO} velas ({rango_txt}). "
             + ("Está testeando la media (entre −0,5 y +1,5 ATR)." if -0.5 <= dist55 <= 1.5 else "Está lejos de la media.")
             + (" Además está en la parte baja de un lateral." if c1_lat else ""),
             "Guía §3 · Acción del precio", "Línea café (EMA 55): ¿el precio la está tocando o viene de retroceder hasta ella?"),
        item("squeeze", "Squeeze: valle rojo que se gira al alza", c2,
             f"El histograma del Squeeze pasa de {sg(h1)} a {sg(h0)}: {color_squeeze(h0, h1)}. "
             + ("Es un valle que pierde fuerza." if c2 else "No es un valle que se gire al alza."),
             "Guía §2.2 y §3", "Ventana del Squeeze en modo área: busca el cambio de rojo oscuro a rojo claro (rosa)."),
        item("adx", "ADX con pendiente negativa", c3,
             f"El ADX está en {eu(a0)} (hace 2 velas, {eu(a2)}): pendiente {'negativa' if c3 else 'positiva'}. "
             + ("La caída no lleva fuerza." if c3 else "El movimiento actual sí lleva fuerza."),
             "Guía §2.3 y §3", "Línea blanca del ADX: ¿apunta hacia abajo?"),
        item("poc", "Cerca del POC (aproximado)", c4,
             (f"El POC aproximado de las últimas {VENTANA_POC} velas está en {pr(poc)}; el precio está a {eu(abs(dist_poc))} ATR "
              f"{'por encima' if dist_poc >= 0 else 'por debajo'}. "
              + ("Apoyado sobre el POC, que actúa de soporte." if c4 else
                 "Por debajo del POC (haría de resistencia)." if dist_poc < -0.5 else "Lejos del POC.")
              + " Es una aproximación calculada con las velas, no el POC de tu TradingView.") if poc
             else "No hay datos para calcular el POC.",
             "Guía §2.4 y §3", "Perfil de volumen con el POC extendido a la derecha: ¿el precio está justo sobre esa línea?"),
    ]

    # --- Zonas no operables (§3.3)
    z1 = estado == "lateral" and nombre == "media"
    topado = pos >= 0.85 or dist55 >= 3.0
    caida = c[-1] < c[-6]
    z3 = caida and pend > 0
    zonas = [
        item("media", "Parte media de un lateral", None, None),
        item("topado", "Topado arriba o sobreextendido sobre la EMA 55", None, None),
        item("cuchillo", "Caída con ADX con pendiente positiva", None, None),
    ]
    zonas[0].update(activa=z1, texto=(f"Hay lateral y el precio está en el {eu(100 * pos, 0)} % del rango: zona media, sin ventaja estadística."
                                      if z1 else "No hay lateral con el precio en el centro del rango." if estado != "lateral"
                                      else f"Hay lateral pero el precio está en la parte {nombre} del rango."),
                    regla="Guía §3.3", donde="Dibuja la caja del lateral y mira si el precio está en el tercio central.")
    zonas[1].update(activa=topado, texto=(f"El precio está en el {eu(100 * pos, 0)} % del rango y a {eu(dist55)} ATR de la EMA 55: "
                                          + ("está topado arriba o muy separado de la media; comprar aquí es ir tarde." if topado
                                             else "ni pegado al techo ni muy separado de la media.")),
                    regla="Guía §3.3", donde="Distancia entre el precio y la línea café; ¿está tocando la resistencia?")
    zonas[2].update(activa=z3, texto=(f"{'El precio cae (cierra por debajo del de hace 5 velas)' if caida else 'El precio no está cayendo'} "
                                      f"y el ADX {'sube' if pend > 0 else 'baja'} ({eu(a2)} → {eu(a0)}). "
                                      + ("Caída con fuerza confirmada: intentar comprar es «atrapar un cuchillo»." if z3 else "No es una caída con fuerza.")),
                    regla="Guía §3.3", donde="Línea blanca del ADX mientras el precio cae: si sube, no compres.")
    for z in zonas:
        z.pop("ok", None)
    activas = sum(1 for z in zonas if z["activa"])

    # --- Salida / toma de beneficios (§3.2)
    div = t["divergencia"]
    s1 = pos >= 0.8
    s2 = bool(div) and div["tipo"] == "bajista" and div["squeeze"]
    atr_prev = S["atr"][-21]
    ratio_atr = atr_v / atr_prev if atr_prev else 1.0
    s3 = t["dir"] == 1 and pend < 0 and (t["senales"]["compresion"] or ratio_atr <= 0.75)
    salida = [
        item("alta", "Parte alta del rango o resistencia", s1,
             f"El precio está en el {eu(100 * pos, 0)} % del rango de las últimas {VENTANA_RANGO} velas ({rango_txt}). "
             + ("Está arriba: la guía sugiere cerrar o tomar beneficios." if s1 else "No está en la parte alta."),
             "Guía §3.2", "Techo del lateral o resistencia previa: ¿el precio llega a ella?"),
        item("divergencia", "Divergencia bajista en el monitor", s2,
             (f"Hay divergencia bajista en el Squeeze: {texto_div(div)}." if s2 else
              "Hay divergencia bajista, pero solo la ve el RSI; la guía habla del Squeeze." if div and div["tipo"] == "bajista"
              else "No hay divergencia bajista en el Squeeze."),
             "Guía §3.2 y §5.2", "Crestas verdes del Squeeze: ¿la última es más baja que la anterior con el precio igual o más alto?"),
        item("volatilidad", "Pérdida de volatilidad tras un impulso", s3,
             f"El rango de las velas (ATR) es {eu(100 * ratio_atr, 0)} % del de hace 20 velas y el ADX {'baja' if pend < 0 else 'sube'} "
             f"({eu(a2)} → {eu(a0)}). "
             + ("Tras una subida, el precio se aplana y el ADX pierde fuerza: la guía sugiere tomar ganancias." if s3
                else "No se da la combinación de aplanamiento y ADX cediendo tras una subida."),
             "Guía §3.2 y §5.1", "Velas cada vez más pequeñas y línea blanca del ADX girando hacia abajo."),
        item("breakeven", "Stop loss a breakeven", None,
             "Esto no se puede medir: es una acción tuya. Cuando la operación en long entra en positivo tras un rebote, "
             "sube el stop ligeramente por encima del precio de entrada.",
             "Guía §3.2", None, manual=True),
    ]

    # --- Checklist pre-operativa (§6.1)
    checklist = [
        item("estructura", "1. Estructura: cerca de la EMA 55 o en la parte baja del rango", c1,
             f"Estado de la tendencia: {ESTADOS[estado]}. " + entrada[0]["texto"], "Guía §6.1", entrada[0].get("donde")),
        item("monitor", "2. Monitor: valle rojo que pierde fuerza", c2, entrada[1]["texto"], "Guía §6.1", entrada[1].get("donde")),
        item("adx", "3. ADX con pendiente negativa", c3, entrada[2]["texto"], "Guía §6.1", entrada[2].get("donde")),
        item("zona", "4. No estás en zona no operable", activas == 0,
             "Ninguna de las 3 zonas de exclusión está activa." if activas == 0
             else f"Hay {activas} zona(s) no operable(s) activa(s): " + "; ".join(z["titulo"].lower() for z in zonas if z["activa"]) + ".",
             "Guía §6.1"),
        item("riesgo", "5. Riesgo en derivados", None,
             "Margen aislado, apalancamiento moderado (máximo 5x–10x) y stop loss puesto desde el origen. Esto lo marcas tú.",
             "Guía §4.2 y §6.1", None, manual=True),
        item("capital", "6. Asignación de capital", None,
             "Primera entrada con un 2 %–4 % de la liquidez y reserva para promediar solo en soportes de más jerarquía. Esto lo marcas tú.",
             "Guía §4.3 y §6.1", None, manual=True),
    ]
    return {
        "zona": {"pos": round(pos, 3), "nombre": nombre, "rango": [_r(lo), _r(hi)], "ventana": VENTANA_RANGO,
                 "dist_ema55_atr": round(dist55, 2), "poc": _r(poc) if poc else None,
                 "dist_poc_atr": round(dist_poc, 2) if dist_poc is not None else None,
                 "squeeze_color": color_squeeze(h0, h1), "adx_pendiente": round(pend, 2)},
        "entrada_long": {"cumple": sum(1 for i in entrada if i["ok"]), "total": len(entrada), "items": entrada},
        "zonas_no_operables": {"activas": activas, "total": len(zonas), "items": zonas},
        "salida": {"cumple": sum(1 for i in salida if i["ok"]), "total": 3, "items": salida},
        "checklist": {"auto_ok": sum(1 for i in checklist if i["ok"]), "auto_total": 4, "items": checklist},
    }


def _r(x):
    return engine._r(x)


# ----------------------------------------------------------------- punto de entrada

def completar(a, candles, tf):
    """Añade a `a` (resultado de engine.analizar_tf) las claves didácticas y de estrategia."""
    if not a:
        return a
    S = series(candles)
    a["guia"] = dict(zip(("horizonte", "uso", "accion_caidas"), GUIA_TF.get(tf, ("", "", ""))))
    a["porques"] = porques(a, candles, S)
    a["tendencia_explicada"] = explicar_tendencia(a, candles, S)
    a["escenarios"] = escenarios(a, candles, S)
    a["estrategia"] = estrategia(a, candles, S) if len(candles["c"]) >= MIN_VELAS else None
    return a
