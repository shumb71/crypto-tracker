"""Pruebas rápidas con datos sintéticos:  python signals/test_engine.py"""
import json, math, random, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import engine, run


def serie(n, drift, seed=1, vol=0.01, p0=100.0):
    random.seed(seed)
    t, o, h, l, c, v = [], [], [], [], [], []
    p = p0
    for i in range(n):
        op = p
        p = p * math.exp(drift + random.gauss(0, vol))
        t.append(i * 3_600_000); o.append(op); c.append(p)
        h.append(max(op, p) * 1.002); l.append(min(op, p) * 0.998); v.append(1000 + random.random() * 200)
    return dict(t=t, o=o, h=h, l=l, c=c, v=v)


# EMA de una constante es la constante; RSI de subida pura = 100, de bajada pura = 0
assert abs(engine.ema([5.0] * 60, 50)[-1] - 5.0) < 1e-9
assert engine.rsi([float(i) for i in range(1, 40)])[-1] == 100.0
assert engine.rsi([float(i) for i in range(40, 1, -1)])[-1] < 1e-9
# RSI: valor de referencia del ejemplo clásico de Wilder (≈70,46 en el primer cálculo)
w = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
assert abs(engine.rsi(w)[-1] - 70.46) < 0.1, engine.rsi(w)[-1]

sube, baja, plano = serie(500, 0.003), serie(500, -0.003), serie(500, 0.0, vol=0.004)
a, b, p = engine.analizar_tf(sube), engine.analizar_tf(baja), engine.analizar_tf(plano)
print("sube", a["score"], a["componentes"]); print("baja", b["score"], b["componentes"]); print("plano", p["score"])
assert a["score"] > 0.4 and b["score"] < -0.4 and abs(p["score"]) < 0.45
assert engine.analizar_tf(serie(40, 0.001)) is None  # pocas velas -> se ignora

# Divergencia bajista fabricada: máximo más alto con menos fuerza
c = [100 + i * 1.0 for i in range(80)] + [179 - i * 1.5 for i in range(1, 9)]
for i in range(41):
    c.append(c[-1] + (1.5 if i % 2 == 0 else -0.6))
c += [c[-1] - i * 0.8 for i in range(1, 9)]
cs = dict(t=list(range(len(c))), o=c, c=c, h=[x * 1.001 for x in c], l=[x * 0.999 for x in c], v=[1.0] * len(c))
d = engine.divergencia(cs, engine.rsi(c))
print("divergencia", d); assert d and d["tipo"] == "bajista"

pesos = {"1h": .1, "4h": .2, "1d": .35, "1w": .35}
g = engine.combinar({"1h": a, "4h": a, "1d": a, "1w": a}, pesos)
assert g["fuerte"] and g["lado"] == 1 and g["nota"] > 7.5
g2 = engine.combinar({"1h": a, "4h": b, "1d": b, "1w": a}, pesos)
assert not g2["fuerte"]
g3 = engine.combinar({"1h": a, "4h": None, "1d": a, "1w": None}, pesos)  # moneda nueva sin histórico
assert g3 and g3["fuerte"]

# Ejecución completa con una fuente falsa: alcista -> aviso; luego plano -> "desinflada"
import time
ahora = int(time.time() * 1000)
def falsa(drift):
    def f(symbol, tf):
        s = serie(400, drift, seed=hash(tf) % 50)
        t0 = (ahora // run.MS[tf]) * run.MS[tf] - 399 * run.MS[tf]
        return [[t0 + i * run.MS[tf], s["o"][i], s["h"][i], s["l"][i], s["c"][i], s["v"][i]] for i in range(400)]
    return f
cfg = json.loads((Path(__file__).parent / "config.json").read_text())
run.FUENTES = [("rota", lambda s, tf: 1 / 0), ("falsa", falsa(0.004))]
sen, fuentes = run.calcular(cfg, ahora)
assert fuentes == ["falsa"] and set(sen) == {"BTCUSDT", "ETHUSDT"}
est = {}
m1 = run.alertas(cfg, sen, est)
assert any("Señal fuerte en BTC" in m for m in m1), m1
assert not any("Señal fuerte" in m for m in run.alertas(cfg, sen, est))  # no repite
run.FUENTES = [("falsa", falsa(0.0))]
sen2, _ = run.calcular(cfg, ahora)
m3 = run.alertas(cfg, sen2, est)
print(run.resumen(sen, __import__("datetime").datetime.now(__import__("datetime").timezone.utc)))
print("---"); print(m1[0]); print("---"); print(m3[0] if m3 else "(sin aviso de salida)")
assert run.num(103250.4) == "103.250" and run.num(3412.56) == "3.412,6" and run.num(0.43219) == "0,4322"
print("\nTODO OK")
