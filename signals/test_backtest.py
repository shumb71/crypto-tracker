"""Pruebas del backtest: sin datos reales. Ejecuta: python3 signals/test_backtest.py"""
import math
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import backtest as B  # noqa: E402


def velas(n, seed, tf_ms=14_400_000):
    rng, p, out = random.Random(seed), 100.0, {k: [] for k in "tohlcv"}
    for i in range(n):
        o = p
        p *= math.exp(0.0006 * math.sin(i / 90) + rng.gauss(0, 0.012))
        hi, lo = max(o, p) * (1 + abs(rng.gauss(0, 0.004))), min(o, p) * (1 - abs(rng.gauss(0, 0.004)))
        for k, x in zip("tohlcv", (i * tf_ms, o, hi, lo, p, 1000 * (1 + abs(rng.gauss(0, 0.5))))):
            out[k].append(x)
    return out


v = velas(900, 1)
filas = B.futuros(v, B.simular(v))
assert len(filas) == 900 - 129 and filas[0]["i"] == 129 and filas[-1]["i"] == 899

# --- no mira el futuro: cambiar las velas posteriores no altera lo que decía en una vela
v2 = {k: list(x) for k, x in v.items()}
for k in "ohlc":
    for i in range(600, 900):
        v2[k][i] *= 3
f2 = B.simular(v2)
for a, b in zip(filas, f2):
    if a["i"] < 600:
        assert {k: a[k] for k in B.CAMPOS} == {k: b[k] for k in B.CAMPOS}, a["i"]
assert any({k: a[k] for k in B.CAMPOS} != {k: b[k] for k in B.CAMPOS} for a, b in zip(filas, f2) if a["i"] >= 600)

# --- el rendimiento futuro es el del cierre k velas después, y falta al final
f = filas[10]
assert abs(f["r5"] - 100 * (v["c"][f["i"] + 5] / v["c"][f["i"]] - 1)) < 1e-9
assert filas[-1]["r5"] is None and filas[-6]["r5"] is not None and filas[-5]["r5"] is None
assert f["c"] == v["c"][f["i"]] and f["t"] == v["t"][f["i"]]

# --- inicios: solo la primera vela de cada racha
assert B.inicios([0, 1, 1, 0, -1, -1, 1, 0]) == [0, 1, 0, 0, -1, 0, 1, 0]

# --- el contraste distingue una señal que adivina de una al azar
rng = random.Random(3)
serie = [{"r5": rng.gauss(0, 2)} for _ in range(3000)]
for j, x in enumerate(serie):
    x["adivina"] = (1 if x["r5"] > 0 else -1) if j % 25 == 0 else 0
    x["azar"] = rng.choice((1, -1)) if j % 25 == 7 else 0
r_ok = B.evaluar([serie], lambda x: x["adivina"], 5, random.Random(1), 300)
r_no = B.evaluar([serie], lambda x: x["azar"], 5, random.Random(1), 300)
assert r_ok["acierto"] == 100 and r_ok["p"] < 0.01 and r_ok["ventaja"] > 1, r_ok
assert 0.02 < r_no["p"] < 0.98 and abs(r_no["ventaja"]) < 0.6, r_no
# una señal siempre «compra» en un mercado que sube no tiene ventaja: el azar gana lo mismo
sube = [{"r5": 1 + rng.gauss(0, 1), "s": 1 if j % 30 == 0 else 0} for j in range(3000)]
r_dr = B.evaluar([sube], lambda x: x["s"], 5, random.Random(1), 300)
assert r_dr["media"] > 0.7 and abs(r_dr["ventaja"]) < 0.3 and r_dr["p"] > 0.02, r_dr
# tramos: dentro + fuera = todo
n_in = B.evaluar([serie], lambda x: x["adivina"], 5, random.Random(1), 50, "in")["n"]
n_out = B.evaluar([serie], lambda x: x["adivina"], 5, random.Random(1), 50, "out")["n"]
assert n_in + n_out == r_ok["n"] and n_in == 72

# --- análisis completo, global e informe con dos monedas y las 4 temporalidades
cfg = {"timeframes": {"1h": .1, "4h": .2, "1d": .35, "1w": .35}, "umbral_fuerte": .5, "min_timeframes_de_acuerdo": 3}
MS = B.run.MS
por_serie, vv = {}, {}
for s, sem in (("AAA", 5), ("BBB", 9)):
    for tf, n in (("1h", 2600), ("4h", 650), ("1d", 400), ("1w", 200)):
        x = velas(n, sem + len(tf) + n, MS[tf])
        fin = 2600 * MS["1h"]
        x["t"] = [fin - (n - i) * MS[tf] for i in range(n)]   # todas acaban a la vez
        paso = 4 if tf == "1h" else 1
        desde = next(i for i in range(130, 140) if (x["t"][i - 1] + MS["1h"]) % MS["4h"] == 0) if tf == "1h" else 130
        por_serie[(s, tf)], vv[(s, tf)] = B.futuros(x, B.simular(x, paso, desde)), x
assert all((f["t"] + MS["1h"]) % MS["4h"] == 0 for f in por_serie[("AAA", "1h")])
res = {"por_tf": B.analizar({k: f for k, f in por_serie.items() if k[1] != "1h"}, n_azar=40)}
assert list(res["por_tf"]) == ["4h", "1d", "1w"] and set(res["por_tf"]["4h"]["senales"]) == {s[0] for s in B.SENALES}
g = {s: B.global_fuerte({tf: por_serie[(s, tf)] for tf in B.TFS}, cfg, vv[(s, "4h")]) for s in ("AAA", "BBB")}
ult = g["AAA"][-1]
assert ult["n_tf"] == 4 and len(g["AAA"]) == len(por_serie[("AAA", "4h")])
# la nota global de la última vela coincide con combinar() sobre lo último de cada temporalidad
esp = B.engine.combinar({tf: {"score": por_serie[("AAA", tf)][-1]["score"]} for tf in B.TFS}, cfg["timeframes"], .5, 3)
assert ult["score"] == esp["score"]
# y en una vela intermedia solo usa temporalidades ya CERRADAS en ese momento
med = g["AAA"][300]
cierre = med["t"] + MS["4h"]
for tf in ("1d", "1w"):
    usadas = [f for f in por_serie[("AAA", tf)] if f["t"] + MS[tf] <= cierre]
    assert usadas, tf
res["global"] = B.analizar_global(g, n_azar=40)
txt = B.informe(res, {"generado": "x", "monedas": ["AAA", "BBB"]})
assert "Temporalidad 1s" in txt and "Señal fuerte global" in txt and "undefined" not in txt and "None" not in txt

# --- ida y vuelta de ficheros
with tempfile.TemporaryDirectory() as d:
    filas_v = [[v["t"][i], v["o"][i], v["h"][i], v["l"][i], v["c"][i], v["v"][i]] for i in range(900)]
    B.guardar_velas(Path(d) / "x.csv.gz", filas_v)
    assert B.leer_velas(Path(d) / "x.csv.gz")["c"] == v["c"]
    B.guardar_filas(Path(d) / "f.csv.gz", filas)
print("BACKTEST OK")
