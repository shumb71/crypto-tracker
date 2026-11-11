"""Backtest del motor de señales: ¿qué hizo el precio después de cada señal?

Recorre el histórico vela a vela. En cada vela cerrada le da al motor EXACTAMENTE lo que
habría visto en directo (las 499 velas cerradas anteriores, nada del futuro), apunta qué
señales daba y mide el recorrido del precio en las velas siguientes.

Uso:
  python signals/backtest.py --descargar --datos datos      # baja el histórico de Binance
  python signals/backtest.py --datos datos --out out        # simula y escribe resultados

Salida (en --out): filas_<SYM>_<tf>.csv.gz (una fila por vela), backtest.json e informe.md.
Solo biblioteca estándar. No es una garantía de nada: mide el pasado.
"""
import argparse
import csv
import gzip
import json
import random
import sys
import time
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).parent))
import engine  # noqa: E402
import estrategia  # noqa: E402
import run  # noqa: E402

VENTANA = 499                # velas cerradas que ve el bot en directo (pide 500 y descarta la abierta)
HORIZONTES = (5, 10, 20)     # velas hacia delante
TFS = ("1h", "4h", "1d", "1w")
CORTE = 0.6                  # primer 60 % del histórico = "muestra"; último 40 % = "fuera de muestra"
N_AZAR = 1000                # desplazamientos al azar para el contraste
BASES = ("https://data-api.binance.vision", "https://api.binance.com")


# ----------------------------------------------------------------- datos

def descargar(symbol, tf, ahora_ms, desde_ms=0):
    """Todas las velas cerradas de Binance para symbol/tf, paginando de 1000 en 1000."""
    filas, inicio, err = [], desde_ms, None
    while True:
        rows = None
        for base in BASES:
            try:
                rows = run.http_json(f"{base}/api/v3/klines?symbol={symbol}&interval={tf}"
                                     f"&limit=1000&startTime={inicio}", timeout=30)
                break
            except Exception as e:  # prueba la otra base
                err = e
        if rows is None:
            raise RuntimeError(f"No se pudo descargar {symbol} {tf}: {err}")
        if not rows:
            break
        filas += [[int(r[0]), *map(float, r[1:6])] for r in rows]
        inicio = int(rows[-1][0]) + run.MS[tf]
        if len(rows) < 1000:
            break
        time.sleep(0.15)
    return [r for r in filas if r[0] + run.MS[tf] <= ahora_ms]


def guardar_velas(ruta, filas):
    with gzip.open(ruta, "wt", newline="") as f:
        csv.writer(f).writerows(filas)


def leer_velas(ruta):
    with gzip.open(ruta, "rt", newline="") as f:
        rows = [[int(r[0]), *map(float, r[1:])] for r in csv.reader(f)]
    rows.sort(key=lambda r: r[0])
    return dict(zip("tohlcv", (list(x) for x in zip(*rows))))


# ----------------------------------------------------------------- simulación

CAMPOS = ["t", "c", "atr_pct", "score", "estado", "dir", "n_sen", "s_div", "s_doble", "s_comp", "s_adx",
          "div", "div_rsi", "div_sq", "rup", "rup_conf", "rup_vela", "rup_vol", "rup_cruce",
          "adx", "adx_pend", "ent", "e_precio", "e_sq", "e_adx", "e_poc", "zonas", "z_media", "z_topado",
          "z_cuchillo", "sal", "x_alta", "x_div", "x_vol", "pos"]


def fila(a, st):
    """Lo que el bot decía en una vela, aplanado en números."""
    t = a["tendencia"]
    div, rup, sen = t["divergencia"], t["ruptura"], t["senales"]
    f = {"t": a["t"], "c": a["cierre"], "atr_pct": a["atr_pct"], "score": a["score"],
         "estado": t["estado"], "dir": t["dir"], "n_sen": t["n_senales"],
         "s_div": int(sen["divergencia"]), "s_doble": int(sen["doble"]),
         "s_comp": int(sen["compresion"]), "s_adx": int(sen["adx"]),
         "div": 0 if not div else (1 if div["tipo"] == "alcista" else -1),
         "div_rsi": int(bool(div and div["rsi"])), "div_sq": int(bool(div and div["squeeze"])),
         "rup": rup["dir"] if rup else 0, "rup_conf": int(bool(rup and rup["confirmada"])),
         "rup_vela": rup["vela_atr"] if rup else "", "rup_vol": rup["vol_x"] if rup else "",
         "rup_cruce": int(rup["cruce"]) if rup else "", "adx": t["adx"]}
    for k in CAMPOS[CAMPOS.index("adx_pend"):]:
        f[k] = ""
    if st:
        en = {i["id"]: i["ok"] for i in st["entrada_long"]["items"]}
        zn = {i["id"]: i["activa"] for i in st["zonas_no_operables"]["items"]}
        sa = {i["id"]: i["ok"] for i in st["salida"]["items"]}
        f.update(adx_pend=st["zona"]["adx_pendiente"], ent=st["entrada_long"]["cumple"],
                 e_precio=int(en["precio"]), e_sq=int(en["squeeze"]), e_adx=int(en["adx"]), e_poc=int(en["poc"]),
                 zonas=st["zonas_no_operables"]["activas"], z_media=int(zn["media"]),
                 z_topado=int(zn["topado"]), z_cuchillo=int(zn["cuchillo"]),
                 sal=st["salida"]["cumple"], x_alta=int(bool(sa["alta"])), x_div=int(bool(sa["divergencia"])),
                 x_vol=int(bool(sa["volatilidad"])), pos=st["zona"]["pos"])
    return f


def simular(velas, paso=1, desde=130, progreso=None):
    """Una fila por vela (cada `paso` velas), sin mirar nunca más allá de la vela evaluada."""
    n, out = len(velas["c"]), []
    for i in range(desde - 1, n, paso):
        w = {k: velas[k][max(0, i - VENTANA + 1):i + 1] for k in "tohlcv"}
        a = engine.analizar_tf(w)
        if not a:
            continue
        st = estrategia.estrategia(a, w, estrategia.series(w)) if len(w["c"]) >= estrategia.MIN_VELAS else None
        f = fila(a, st)
        f["i"] = i
        out.append(f)
        if progreso and len(out) % 2000 == 0:
            progreso(len(out))
    return out


def futuros(velas, filas, horizontes=HORIZONTES):
    """Añade a cada fila el % de cambio del cierre a k velas vista (None si aún no existe)."""
    c, n = velas["c"], len(velas["c"])
    for f in filas:
        i = f["i"]
        for k in horizontes:
            f[f"r{k}"] = 100 * (c[i + k] / c[i] - 1) if i + k < n else None
    return filas


def guardar_filas(ruta, filas, horizontes=HORIZONTES):
    cols = CAMPOS + [f"r{k}" for k in horizontes]
    with gzip.open(ruta, "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for f in filas:
            w.writerow(["" if f.get(k) is None else f.get(k) for k in cols])


# ----------------------------------------------------------------- señales a evaluar
# Cada señal: (id, título, función fila -> sentido esperado del precio: +1 sube, -1 baja, 0 no hay señal)

def _tend(f):
    return f["estado"] in ("sana", "agotandose") and f["dir"] != 0


def _n(f, k):
    return f.get(k) not in ("", None)


SENALES = [
    ("agot", "Tendencia «agotándose» (≥2 de 4 señales)", lambda f: -f["dir"] if f["estado"] == "agotandose" else 0),
    ("agot3", "Agotamiento con ≥3 de 4 señales", lambda f: -f["dir"] if f["estado"] == "agotandose" and f["n_sen"] >= 3 else 0),
    ("agot1", "Al menos 1 señal de agotamiento", lambda f: -f["dir"] if _tend(f) and f["n_sen"] >= 1 else 0),
    ("s_div", "Agotamiento: divergencia", lambda f: -f["dir"] if _tend(f) and f["s_div"] else 0),
    ("s_doble", "Agotamiento: doble techo/suelo", lambda f: -f["dir"] if _tend(f) and f["s_doble"] else 0),
    ("s_comp", "Agotamiento: medias 10/55 juntándose", lambda f: -f["dir"] if _tend(f) and f["s_comp"] else 0),
    ("s_adx", "Agotamiento: ADX cede", lambda f: -f["dir"] if _tend(f) and f["s_adx"] else 0),
    ("div", "Divergencia (RSI o Squeeze)", lambda f: f["div"]),
    ("div_rsi", "Divergencia solo en RSI", lambda f: f["div"] if f["div_rsi"] and not f["div_sq"] else 0),
    ("div_sq", "Divergencia solo en Squeeze", lambda f: f["div"] if f["div_sq"] and not f["div_rsi"] else 0),
    ("div_2", "Divergencia en RSI y Squeeze a la vez", lambda f: f["div"] if f["div_sq"] and f["div_rsi"] else 0),
    ("div_adx", "Divergencia + ADX con pendiente negativa (aviso reforzado)",
     lambda f: f["div"] if f["div"] and _n(f, "adx_pend") and f["adx_pend"] < 0 else 0),
    ("div_sin_adx", "Divergencia con ADX subiendo", lambda f: f["div"] if f["div"] and _n(f, "adx_pend") and f["adx_pend"] >= 0 else 0),
    ("rup", "Ruptura de lateral confirmada", lambda f: f["rup"] if f["rup_conf"] else 0),
    ("rup_dud", "Posible ruptura (sin confirmar)", lambda f: f["rup"] if f["rup"] and not f["rup_conf"] else 0),
    ("ent4", "Entrada long: 4 de 4 condiciones", lambda f: 1 if f.get("ent") == 4 else 0),
    ("ent4_limpia", "Entrada long 4/4 y ninguna zona no operable", lambda f: 1 if f.get("ent") == 4 and f.get("zonas") == 0 else 0),
    ("ent3", "Entrada long: ≥3 de 4 condiciones", lambda f: 1 if _n(f, "ent") and f["ent"] >= 3 else 0),
    ("e_precio", "Entrada: precio en la EMA 55 / parte baja", lambda f: 1 if f.get("e_precio") == 1 else 0),
    ("e_sq", "Entrada: Squeeze en valle rojo girando", lambda f: 1 if f.get("e_sq") == 1 else 0),
    ("e_adx", "Entrada: ADX con pendiente negativa", lambda f: 1 if f.get("e_adx") == 1 else 0),
    ("e_poc", "Entrada: cerca del POC aproximado", lambda f: 1 if f.get("e_poc") == 1 else 0),
    ("z_media", "Zona no operable: mitad del lateral (comprando)", lambda f: 1 if f.get("z_media") == 1 else 0),
    ("z_topado", "Zona no operable: topado / sobreextendido (comprando)", lambda f: 1 if f.get("z_topado") == 1 else 0),
    ("z_cuchillo", "Zona no operable: caída con ADX subiendo (comprando)", lambda f: 1 if f.get("z_cuchillo") == 1 else 0),
    ("sal2", "Salida: ≥2 de 3 condiciones", lambda f: -1 if _n(f, "sal") and f["sal"] >= 2 else 0),
    ("x_alta", "Salida: parte alta del rango", lambda f: -1 if f.get("x_alta") == 1 else 0),
    ("x_div", "Salida: divergencia bajista en Squeeze", lambda f: -1 if f.get("x_div") == 1 else 0),
    ("x_vol", "Salida: pérdida de volatilidad tras impulso", lambda f: -1 if f.get("x_vol") == 1 else 0),
    ("nota_alta", "Nota de la temporalidad ≥ 7,5 (score ≥ 0,5)", lambda f: 1 if f["score"] >= 0.5 else 0),
    ("nota_baja", "Nota de la temporalidad ≤ 2,5 (score ≤ −0,5)", lambda f: -1 if f["score"] <= -0.5 else 0),
]


def sentidos(filas, fn):
    return [fn(f) for f in filas]


def inicios(sent):
    """Solo cuenta la vela en la que la señal APARECE (o cambia de sentido), no cada vela que dura."""
    return [s if s != 0 and (j == 0 or sent[j - 1] != s) else 0 for j, s in enumerate(sent)]


def _resumen(vals):
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "media": round(mean(vals), 3), "mediana": round(median(vals), 3),
            "acierto": round(100 * sum(1 for v in vals if v > 0) / len(vals), 1)}


def evaluar(series, fn, k, rng, n_azar=N_AZAR, tramo=None):
    """Rendimiento «a favor de la señal» k velas después de cada inicio, juntando varias series.

    series: lista de listas de filas (p. ej. BTC y ETH de una temporalidad).
    tramo: None = todo; 'in' = primer 60 %; 'out' = último 40 % (por tiempo, en cada serie).
    Contraste: se desplaza la posición de las señales al azar dentro de cada serie (misma
    cantidad, mismos sentidos, mismas rachas) y se mira cuántas veces el azar lo hace igual o mejor.
    """
    datos = []  # por serie: (inicios, rendimientos, índices válidos)
    for filas in series:
        ini = inicios(sentidos(filas, fn))
        r = [f.get(f"r{k}") for f in filas]
        m = len(filas)
        lo, hi = (0, m) if tramo is None else (0, int(CORTE * m)) if tramo == "in" else (int(CORTE * m), m)
        datos.append((ini, r, lo, hi))
    obs = [s * r[j] for ini, r, lo, hi in datos for j, s in enumerate(ini)
           if s and lo <= j < hi and r[j] is not None]
    res = _resumen(obs)
    if res["n"] < 5:
        return res
    # Lo que haría «cualquier vela» con esos mismos sentidos: desplazamientos circulares al azar
    medias = []
    for _ in range(n_azar):
        vals = []
        for ini, r, lo, hi in datos:
            ancho = hi - lo
            if ancho < 50:
                continue
            d = rng.randrange(1, ancho)
            for j in range(lo, hi):
                s = ini[j]
                if s:
                    x = r[lo + (j - lo + d) % ancho]
                    if x is not None:
                        vals.append(s * x)
        if vals:
            medias.append(mean(vals))
    if medias:
        res["azar"] = round(mean(medias), 3)
        res["ventaja"] = round(res["media"] - res["azar"], 3)
        res["p"] = round((1 + sum(1 for x in medias if x >= res["media"])) / (1 + len(medias)), 4)
    return res


def analizar(por_serie, horizontes=HORIZONTES, semilla=7, n_azar=N_AZAR):
    """por_serie: {(symbol, tf): filas}. Devuelve {tf: {señal: {k: {todo, in, out, por_moneda}}}}."""
    rng = random.Random(semilla)
    res = {}
    for tf in sorted({tf for _, tf in por_serie}, key=TFS.index):
        grupo = {s: f for (s, t), f in por_serie.items() if t == tf}
        res[tf] = {"velas": {s: len(f) for s, f in grupo.items()}, "senales": {}}
        for sid, _, fn in SENALES:
            r = {}
            for k in horizontes:
                r[str(k)] = {
                    "todo": evaluar(list(grupo.values()), fn, k, rng, n_azar),
                    "in": evaluar(list(grupo.values()), fn, k, rng, n_azar, "in"),
                    "out": evaluar(list(grupo.values()), fn, k, rng, n_azar, "out"),
                    "por_moneda": {s: evaluar([f], fn, k, rng, max(200, n_azar // 4)) for s, f in grupo.items()},
                }
            res[tf]["senales"][sid] = r
    return res


# ----------------------------------------------------------------- señal fuerte global (las 4 temporalidades)

def global_fuerte(por_tf_filas, cfg, velas_4h, horizontes=(6, 18, 42)):
    """Reconstruye la nota global en cada cierre de 4h con lo último CERRADO de cada temporalidad."""
    idx = {tf: sorted((f["t"] + run.MS[tf], f["score"]) for f in filas) for tf, filas in por_tf_filas.items()}
    pos = {tf: 0 for tf in idx}
    c, n, out = velas_4h["c"], len(velas_4h["c"]), []
    for f in por_tf_filas["4h"]:
        cierre = f["t"] + run.MS["4h"]
        por_tf = {}
        for tf, lista in idx.items():
            while pos[tf] + 1 < len(lista) and lista[pos[tf] + 1][0] <= cierre:
                pos[tf] += 1
            if lista and lista[pos[tf]][0] <= cierre:
                por_tf[tf] = {"score": lista[pos[tf]][1]}
        g = engine.combinar(por_tf, cfg["timeframes"], cfg["umbral_fuerte"], cfg["min_timeframes_de_acuerdo"])
        fila_g = {"t": f["t"], "i": f["i"], "score": g["score"], "fuerte": g["lado"] if g["fuerte"] else 0,
                  "n_tf": len(por_tf)}
        for k in horizontes:
            fila_g[f"r{k}"] = 100 * (c[f["i"] + k] / c[f["i"]] - 1) if f["i"] + k < n else None
        out.append(fila_g)
    return out


SENALES_GLOBAL = [
    ("fuerte", "Señal fuerte global (la que avisa por Telegram)", lambda f: f["fuerte"] if f["n_tf"] == 4 else 0),
    ("fuerte_alc", "Señal fuerte ALCISTA", lambda f: 1 if f["fuerte"] == 1 and f["n_tf"] == 4 else 0),
    ("fuerte_baj", "Señal fuerte BAJISTA", lambda f: -1 if f["fuerte"] == -1 and f["n_tf"] == 4 else 0),
    ("g_alc", "Nota global ≥ 6 (score ≥ 0,2)", lambda f: 1 if f["score"] >= 0.2 and f["n_tf"] == 4 else 0),
    ("g_baj", "Nota global ≤ 4 (score ≤ −0,2)", lambda f: -1 if f["score"] <= -0.2 and f["n_tf"] == 4 else 0),
]


def analizar_global(por_moneda, horizontes=(6, 18, 42), semilla=11, n_azar=N_AZAR):
    rng = random.Random(semilla)
    res = {}
    for sid, _, fn in SENALES_GLOBAL:
        res[sid] = {str(k): {"todo": evaluar(list(por_moneda.values()), fn, k, rng, n_azar),
                             "in": evaluar(list(por_moneda.values()), fn, k, rng, n_azar, "in"),
                             "out": evaluar(list(por_moneda.values()), fn, k, rng, n_azar, "out"),
                             "por_moneda": {s: evaluar([f], fn, k, rng, max(200, n_azar // 4))
                                            for s, f in por_moneda.items()}}
                    for k in horizontes}
    return res


# ----------------------------------------------------------------- informe

def _pct(x):
    return "—" if x is None else f"{x:+.2f} %".replace(".", ",")


def _celda(r):
    if not r or r.get("n", 0) < 5:
        return f"n={r.get('n', 0) if r else 0}"
    p = r.get("p")
    if p is None:
        return f"media {_pct(r['media'])} (n={r['n']}, sin contraste)"
    marca = " ✅" if p <= 0.05 and r["ventaja"] > 0 else " ❌" if p >= 0.95 else ""
    return (f"{_pct(r['ventaja'])} (n={r['n']}, acierta {str(r['acierto']).replace('.', ',')} %, "
            f"p={str(p).replace('.', ',')}){marca}")


def tabla(titulos, bloque, horizontes, unidad):
    out = ["| Señal | " + " | ".join(f"a {k} {unidad}" for k in horizontes) + " | fuera de muestra (horizonte medio) |",
           "|---|" + "---|" * (len(horizontes) + 1)]
    medio = str(horizontes[len(horizontes) // 2])
    for sid, tit in titulos:
        r = bloque.get(sid)
        if not r:
            continue
        out.append(f"| {tit} | " + " | ".join(_celda(r[str(k)]["todo"]) for k in horizontes)
                   + f" | {_celda(r[medio]['out'])} |")
    return "\n".join(out)


def informe(res, meta):
    tit = [(s, t) for s, t, _ in SENALES]
    p = ["# Backtest de las señales", "",
         f"Generado: {meta['generado']} · Monedas: {', '.join(meta['monedas'])} · Datos: Binance (velas cerradas).", "",
         "**Cómo leerlo.** Cada celda es la *ventaja* de la señal: lo que se movió el precio a favor de la señal, "
         "menos lo que se habría movido eligiendo velas al azar con el mismo sentido. `n` = veces que apareció la señal, "
         "`acierta` = % de veces que el precio fue en el sentido esperado, `p` = probabilidad de que el azar lo iguale "
         "(✅ si p ≤ 0,05 a favor; ❌ si la señal va claramente al revés). «Fuera de muestra» = solo el último 40 % del histórico.", "",
         "En las señales de agotamiento y salida el sentido esperado es CONTRA la tendencia; en las «zonas no operables» "
         "se mide qué pasa si compras ahí (lo esperable es ventaja negativa).", ""]
    for tf, b in res["por_tf"].items():
        velas = ", ".join(f"{s}: {n}" for s, n in b["velas"].items())
        p += [f"## Temporalidad {run.NOMBRE_TF[tf]}", "", f"Velas evaluadas — {velas}", "",
              tabla(tit, b["senales"], HORIZONTES, "velas"), ""]
    if res.get("global"):
        p += ["## Señal fuerte global (4 temporalidades juntas, medida en velas de 4h)", "",
              tabla([(s, t) for s, t, _ in SENALES_GLOBAL], res["global"], (6, 18, 42), "velas de 4h"), ""]
    p += ["---", "Medir el pasado no garantiza el futuro. Con tantas señales y horizontes, alguna saldrá «significativa» "
          "por pura casualidad: fíate solo de lo que se repite en las dos monedas y fuera de muestra."]
    return "\n".join(p)


# ----------------------------------------------------------------- programa

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", default="datos")
    ap.add_argument("--out", default="out_backtest")
    ap.add_argument("--descargar", action="store_true")
    ap.add_argument("--tfs", default="1h,4h,1d,1w")
    ap.add_argument("--n-azar", type=int, default=N_AZAR)
    args = ap.parse_args()
    cfg = json.loads((Path(__file__).parent / "config.json").read_text())
    datos, out = Path(args.datos), Path(args.out)
    tfs = [t for t in args.tfs.split(",") if t]
    ahora_ms = int(time.time() * 1000)

    if args.descargar:
        datos.mkdir(parents=True, exist_ok=True)
        for sym in cfg["symbols"]:
            for tf in tfs:
                filas = descargar(sym, tf, ahora_ms)
                guardar_velas(datos / f"{sym}_{tf}.csv.gz", filas)
                print(f"{sym} {tf}: {len(filas)} velas", flush=True)
        return

    out.mkdir(parents=True, exist_ok=True)
    por_serie, velas = {}, {}
    for sym in cfg["symbols"]:
        for tf in tfs:
            ruta = datos / f"{sym}_{tf}.csv.gz"
            if not ruta.exists():
                continue
            v = leer_velas(ruta)
            # En 1h solo hace falta la nota en cada cierre de 4h (para la señal global): 1 de cada 4 velas
            paso = 4 if tf == "1h" else 1
            desde = 130
            if tf == "1h":  # alinea con los cierres de 4h
                desde = next(i for i in range(130, 140) if (v["t"][i - 1] + run.MS["1h"]) % run.MS["4h"] == 0)
            t0 = time.time()
            filas = futuros(v, simular(v, paso, desde, lambda k: print(f"  {sym} {tf}: {k} velas…", flush=True)))
            por_serie[(sym, tf)], velas[(sym, tf)] = filas, v
            guardar_filas(out / f"filas_{sym}_{tf}.csv.gz", filas)
            print(f"{sym} {tf}: {len(filas)} filas en {time.time() - t0:.0f} s", flush=True)

    res = {"por_tf": analizar({k: f for k, f in por_serie.items() if k[1] != "1h"}, n_azar=args.n_azar)}
    if all((s, tf) in por_serie for s in cfg["symbols"] for tf in TFS):
        res["global"] = analizar_global(
            {s: global_fuerte({tf: por_serie[(s, tf)] for tf in TFS}, cfg, velas[(s, "4h")]) for s in cfg["symbols"]},
            n_azar=args.n_azar)
    meta = {"generado": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "monedas": cfg["symbols"],
            "ventana": VENTANA, "horizontes": HORIZONTES, "corte": CORTE}
    (out / "backtest.json").write_text(json.dumps({"meta": meta, **res}, ensure_ascii=False, indent=1))
    (out / "informe.md").write_text(informe(res, meta))
    print(informe(res, meta))


if __name__ == "__main__":
    main()
