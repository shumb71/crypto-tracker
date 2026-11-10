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
# (una divergencia suelta en una bajada de ruido puede restar algo de puntuación)
assert a["score"] > 0.4 and b["score"] < -0.3 and abs(p["score"]) < 0.45
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
        s = serie(400, drift, seed={"1h": 1, "4h": 2, "1d": 3, "1w": 4}[tf])
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



# =========================== Estado de la tendencia ===========================
def velas_de(closes, rango=0.0015, vols=None):
    t = [i * 14_400_000 for i in range(len(closes))]
    o = [closes[0]] + closes[:-1]
    return dict(t=t, o=o, h=[max(x, y) * (1 + rango) for x, y in zip(o, closes)],
                l=[min(x, y) * (1 - rango) for x, y in zip(o, closes)], c=closes, v=vols or [1000.0] * len(closes))


def ruido(p, n, drift=0.0, vol=0.002):
    out = []
    for _ in range(n):
        p *= math.exp(drift + random.gauss(0, vol)); out.append(p)
    return out


def tramo(p, n, paso, r=0.0004):
    out = []
    for _ in range(n):
        p = p * (1 + paso) + random.gauss(0, r * p); out.append(p)
    return out


def hacia(p, n, objetivo):
    return tramo(p, n, (objetivo / p) ** (1 / n) - 1)


# --- Squeeze Momentum y ADX
assert abs(engine.linreg_fin([1, 3, 5, 7, 9]) - 9) < 1e-9           # recta perfecta: el valor final es el real
assert all(abs(x) < 1e-9 for x in engine.squeeze_hist([5.0] * 60, [5.0] * 60, [5.0] * 60) if x is not None)
sq_up = engine.squeeze_hist(sube["h"], sube["l"], sube["c"])
assert sq_up[-1] > 0 and engine.squeeze_hist(baja["h"], baja["l"], baja["c"])[-1] < 0   # signo = dirección
limpia = serie(300, 0.004, seed=1, vol=0.004)               # subida limpia: ADX muy alto
ax_up = engine.adx(limpia["h"], limpia["l"], limpia["c"])
assert ax_up[:27].count(None) == 27 and ax_up[27] is not None and ax_up[-1] > 40
ax_pl = [x for x in engine.adx(plano["h"], plano["l"], plano["c"]) if x is not None]
assert max(ax_pl) <= 100 and min(ax_pl) >= 0

# --- Doble techo + divergencia -> agotamiento (2 de 4 señales)
def techo(seed, rel_B):
    random.seed(seed)
    c = ruido(100, 100, 0.003, 0.002)
    c += tramo(c[-1], 30, 0.006)
    A = max(c)
    c += tramo(c[-1], 14, -0.007)
    c += hacia(c[-1], 26, A * rel_B)
    c += tramo(c[-1], 8, -0.004)
    return velas_de(c)

for seed in (11, 12):
    cd = techo(seed, 1.000)
    t = engine.tendencia_estado(cd, engine.divergencia(cd, engine.rsi(cd["c"])))
    print("doble techo", seed, t["estado"], t["senales"])
    assert t["dir"] == 1 and t["senales"]["doble"] and t["senales"]["divergencia"]
    assert t["estado"] == "agotandose" and t["n_senales"] >= 2
    # una tendencia bajista no se "agota" por un doble techo
cd = techo(11, 0.992)          # segundo máximo algo más bajo: doble techo sin divergencia = 1 señal
t = engine.tendencia_estado(cd, engine.divergencia(cd, engine.rsi(cd["c"])))
assert t["senales"]["doble"] and not t["senales"]["divergencia"] and t["estado"] == "sana"
cd = techo(11, 1.003)          # segundo máximo más alto que el primero: ya no es doble techo
t = engine.tendencia_estado(cd, engine.divergencia(cd, engine.rsi(cd["c"])))
assert not t["senales"]["doble"]

# --- Combinación de divergencias: una sola señal, más fiable si coinciden; si se contradicen, ninguna
r_, s_ = {"tipo": "bajista", "t": 5}, {"tipo": "bajista", "t": 7}
assert engine.combinar_div(r_, s_) == {"tipo": "bajista", "rsi": True, "squeeze": True, "t": 5}
assert engine.combinar_div(None, s_)["squeeze"] and not engine.combinar_div(None, s_)["rsi"]
assert engine.combinar_div(r_, {"tipo": "alcista", "t": 7}) is None

# --- Lateral y ruptura (lateral determinista con un seno, para no depender del azar del ADX)
def lateral_y_ruptura(n_lat, salto, vol_r, d=1, tras=3):
    c = [100 * (1 + 0.006 * math.sin(2 * math.pi * i / 14)) for i in range(n_lat)]
    base = c[-1]
    c.append(base * (1 + d * salto))
    for _ in range(tras):
        c.append(c[-1] * (1 + d * 0.003))
    cd = velas_de(c, vols=[1000.0] * n_lat + [vol_r] + [1300.0] * tras)
    cd["h"][n_lat] = max(cd["c"][n_lat], base) * 1.001
    cd["l"][n_lat] = min(cd["c"][n_lat], base) * 0.999
    return cd, engine.tendencia_estado(cd, engine.divergencia(cd, engine.rsi(cd["c"])))

# lateral puro, sin ruptura
cd = velas_de([100 * (1 + 0.006 * math.sin(2 * math.pi * i / 14)) for i in range(150)])
t = engine.tendencia_estado(cd, None)
assert t["estado"] == "lateral" and t["ruptura"] is None, t["estado"]

cd, t = lateral_y_ruptura(148, 0.03, 2800)                      # fuerza + volumen + cruce
assert t["estado"] == "ruptura" and t["ruptura"]["dir"] == 1 and t["ruptura"]["confirmada"]
cd, t = lateral_y_ruptura(148, 0.03, 1000)                      # sin volumen: no se confirma
assert t["estado"] == "ruptura_dudosa" and not t["ruptura"]["confirmada"] and t["ruptura"]["vol_x"] < 1.3
assert engine.tendencia_estado(cd, None)["ruptura"]["cruce"]
# a la baja: probamos varias fases del lateral y exigimos que alguna confirme y ninguna dé "alcista"
estados = [lateral_y_ruptura(n, 0.03, 2800, d=-1)[1] for n in range(140, 154)]
assert any(e["estado"] == "ruptura" and e["ruptura"]["dir"] == -1 for e in estados)
assert not any(e["ruptura"] and e["ruptura"]["dir"] == 1 for e in estados)

# --- Pocas velas: no se inventa nada
corto = velas_de(ruido(100, 100, 0.003, 0.002))
t = engine.tendencia_estado(corto, None)
assert t["estado"] == "sin_datos" and t["n_senales"] == 0

# --- Avisos de agotamiento y de ruptura: solo en 4h/1d, sin repetir, sin ráfaga al activarse
cfg = json.loads((Path(__file__).parent / "config.json").read_text())
assert cfg["avisar_agotamiento_en"] == ["4h", "1d"] and cfg["avisar_rupturas_en"] == ["4h", "1d"]
run.FUENTES = [("falsa", falsa(0.004))]
sen, _ = run.calcular(cfg, ahora)

def forzar(sen, tf, **cambios):
    s_ = json.loads(json.dumps(sen))
    s_["BTCUSDT"]["tf"][tf]["tendencia"].update(cambios)
    return s_

agot = dict(estado="agotandose", dir=1, n_senales=3,
            senales=dict(divergencia=True, doble=True, compresion=False, adx=True),
            divergencia=dict(tipo="bajista", rsi=True, squeeze=True, t=1))
est = {"simbolos": {}}                                    # estado antiguo, sin la clave nueva
m = run.alertas(cfg, forzar(sen, "4h", **agot), est)
assert not any("agotando" in x for x in m)                # primera vez: se arma en silencio
m = run.alertas(cfg, forzar(sen, "4h", **agot), est)
assert not any("agotando" in x for x in m)                # sigue sin repetirse
est["agotamiento"]["BTCUSDT|4h"] = 0                      # simula que antes estaba sano
m = run.alertas(cfg, forzar(sen, "4h", **agot), est)
avisos = [x for x in m if "agotando" in x]
assert len(avisos) == 1 and "3/4" in avisos[0] and "doble techo" in avisos[0] and "RSI + Squeeze" in avisos[0]
m = run.alertas(cfg, forzar(sen, "4h", **agot), est)
assert not any("agotando" in x for x in m)                # no repite
m = run.alertas(cfg, forzar(sen, "1h", **agot), est)
assert not any("agotando" in x for x in m)                # 1h no avisa
sana = dict(estado="sana", n_senales=0)
run.alertas(cfg, forzar(sen, "4h", **sana), est)           # se rearma al desaparecer
assert est["agotamiento"]["BTCUSDT|4h"] == 0
m = run.alertas(cfg, forzar(sen, "4h", **agot), est)
assert any("agotando" in x for x in m)

rup = dict(estado="ruptura", ruptura=dict(dir=-1, t=ahora - 86_400_000, vela_atr=2.1, vol_x=1.8, cruce=True, confirmada=True))
m = run.alertas(cfg, forzar(sen, "1d", **rup), est)
r_av = [x for x in m if "ruptura confirmada" in x]
assert len(r_av) == 1 and "a la baja" in r_av[0] and "2,1× ATR" in r_av[0]
assert not any("ruptura confirmada" in x for x in run.alertas(cfg, forzar(sen, "1d", **rup), est))
rup["ruptura"]["confirmada"] = False
assert not any("ruptura confirmada" in x for x in run.alertas(cfg, forzar(sen, "1h", **rup), est))

# --- El resumen enseña el estado de cada temporalidad
txt = run.resumen(forzar(sen, "4h", **agot), __import__("datetime").datetime.now(__import__("datetime").timezone.utc))
assert "Tendencia:" in txt and "agotándose ▲ 3/4" in txt, txt
print(txt.split("\n\n")[1])
print("\nTODO OK")
