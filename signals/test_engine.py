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
cd_ = engine.combinar_div(r_, s_)
assert (cd_["tipo"], cd_["rsi"], cd_["squeeze"], cd_["t"]) == ("bajista", True, True, 5)
assert cd_["det"]["rsi"] is r_ and cd_["det"]["squeeze"] is s_
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

# =========================== Explicaciones y estrategia ===========================
import estrategia as ES

# --- formato y utilidades
assert ES.eu(1234.5) == "1.234,5" and ES.pr(73216.01) == "73.216" and ES.pr(2024.22) == "2.024,2"
assert ES.pr(0.43219) == "0,43219" and ES.cap("EMA 50 sube") == "EMA 50 sube" and ES.cap("ema") == "Ema"
assert ES.color_squeeze(-2, -1) is not None
assert ES.color_squeeze(2, 1).startswith("verde oscuro") and ES.color_squeeze(1, 2).startswith("verde claro")
assert ES.color_squeeze(-1, -2).startswith("rojo claro") and ES.color_squeeze(-2, -1).startswith("rojo oscuro")
assert ES.color_squeeze(None, 1) is None

# --- POC aproximado: cae donde se concentra el volumen
v_poc = dict(t=list(range(100)), o=[105.0] * 100, c=[105.0] * 100, h=[110.0] * 100, l=[100.0] * 100, v=[100.0] * 100)
for i in range(40, 45):
    v_poc["h"][i], v_poc["l"][i], v_poc["v"][i] = 105.0, 104.0, 5000.0
assert 104.0 <= ES.poc_aproximado(v_poc) <= 105.0
assert ES.poc_aproximado(dict(h=[5.0] * 100, l=[5.0] * 100, v=[1.0] * 100)) is None   # sin recorrido, no hay perfil

# --- posición en el rango
pos, lo_, hi_, nom = ES.posicion_rango(velas_de([100 + i for i in range(80)]))
assert nom == "alta" and pos > 0.9
pos, lo_, hi_, nom = ES.posicion_rango(velas_de([200 - i for i in range(80)]))
assert nom == "baja" and pos < 0.1

# --- completar(): estructura, coherencia con la nota y JSON válido
def completo(cd, tf="4h"):
    a = engine.analizar_tf(cd)
    return ES.completar(a, cd, tf), ES.series(cd)

cd = techo(11, 1.000)
a, S = completo(cd)
json.dumps(a)
assert {"porques", "tendencia_explicada", "escenarios", "estrategia", "guia"} <= set(a)
assert len(a["porques"]["bloques"]) == 5
assert abs(sum(b["aporta"] for b in a["porques"]["bloques"]) - a["score"]) < 0.02      # los porqués suman la nota
textos = " ".join(b["texto"] for b in a["porques"]["bloques"])
assert "ema 50" not in textos and "squeeze" not in textos                                # sin minúsculas indebidas
assert "Squeeze" in textos and "máximo" in textos                                        # explica la divergencia con números
te = a["tendencia_explicada"]
assert te["estado"] == a["tendencia"]["estado"] == "agotandose" and te["resumen"]
assert {x["id"]: x["ok"] for x in te["senales"]} == a["tendencia"]["senales"]           # misma verdad que el motor
assert all(x["texto"] and x["regla"] and x["donde"] for x in te["senales"])
assert a["guia"]["horizonte"] == "24 a 48 horas" and completo(cd, "1w")[0]["guia"]["horizonte"] == "3 a 6 meses"

# --- el ADX explica por qué no cuenta cuando cae pero el precio ya se alejó del extremo
adx_txt = next(x["texto"] for x in te["senales"] if x["id"] == "adx")
dt = engine.adx_detalle(S["adx"], cd["h"], cd["l"], cd["c"], 1, S["atr"][-1])
assert dt["ok"] == a["tendencia"]["senales"]["adx"] == engine.adx_cede(S["adx"], cd["h"], cd["l"], cd["c"], 1, S["atr"][-1])
if dt["cae"] and not dt["cerca"]:
    assert "ya está a" in adx_txt

# --- entrada, zonas, salida y checklist: coherentes con los indicadores en bruto
def comprobar_estrategia(cd, tf="4h"):
    a, S = completo(cd, tf)
    st = a["estrategia"]
    e = {i["id"]: i["ok"] for i in st["entrada_long"]["items"]}
    assert e["adx"] == (S["adx"][-1] < S["adx"][-3])
    assert e["squeeze"] == (S["sq"][-1] < 0 and S["sq"][-1] > S["sq"][-2])
    z = {i["id"]: i["activa"] for i in st["zonas_no_operables"]["items"]}
    pos, _, _, nombre = ES.posicion_rango(cd)
    assert z["media"] == (a["tendencia"]["estado"] == "lateral" and nombre == "media")
    assert z["cuchillo"] == (cd["c"][-1] < cd["c"][-6] and S["adx"][-1] - S["adx"][-3] > 0)
    assert st["zonas_no_operables"]["activas"] == sum(z.values())
    ch = {i["id"]: i for i in st["checklist"]["items"]}
    assert (ch["estructura"]["ok"], ch["monitor"]["ok"], ch["adx"]["ok"]) == (e["precio"], e["squeeze"], e["adx"])
    assert ch["zona"]["ok"] == (st["zonas_no_operables"]["activas"] == 0)
    assert ch["riesgo"]["manual"] and ch["capital"]["manual"] and ch["riesgo"]["ok"] is None
    assert st["entrada_long"]["cumple"] == sum(1 for v_ in e.values() if v_) and st["entrada_long"]["total"] == 4
    assert all(i["texto"] for g in ("entrada_long", "salida") for i in st[g]["items"])
    return a, st, e, z

random.seed(21); fuerte = velas_de(ruido(100, 200, 0.004, 0.003))
a, st, e, z = comprobar_estrategia(fuerte)
assert z["topado"] and not e["precio"]                       # tras un subidón: topado y lejos de la EMA 55
assert {i["id"]: i["ok"] for i in st["salida"]["items"]}["alta"]
random.seed(22); comprobar_estrategia(velas_de(ruido(100, 200, -0.004, 0.003)))
for n_lat in range(140, 160, 3):
    c_ = [100 * (1 + 0.006 * math.sin(2 * math.pi * i / 14)) for i in range(n_lat)]
    comprobar_estrategia(velas_de(c_))
# alguna fase del lateral deja el precio en el centro (zona activa) y otra no
fases = []
for n_lat in range(140, 154):
    c_ = [100 * (1 + 0.006 * math.sin(2 * math.pi * i / 14)) for i in range(n_lat)]
    fases.append(comprobar_estrategia(velas_de(c_))[3]["media"])
assert any(fases) and not all(fases), fases

# el divergencia bajista de la salida exige el Squeeze (la del RSI sola no vale)
a11, st11, *_ = comprobar_estrategia(techo(11, 1.000))
a12, st12, *_ = comprobar_estrategia(techo(12, 1.000))
s11 = next(i for i in st11["salida"]["items"] if i["id"] == "divergencia")
s12 = next(i for i in st12["salida"]["items"] if i["id"] == "divergencia")
assert s11["ok"] and not s12["ok"] and "solo la ve el RSI" in s12["texto"]

# --- escenarios con niveles concretos
cd_l, t_l = lateral_y_ruptura(150, 0.0, 1000, tras=0)[0], None
c_lat = velas_de([100 * (1 + 0.006 * math.sin(2 * math.pi * i / 14)) for i in range(150)])
a_l, S_l = completo(c_lat)
assert a_l["tendencia"]["estado"] == "lateral"
esc = a_l["escenarios"]
assert any(x["tipo"] == "confirma" and ES.pr(max(c_lat["h"][-20:])) in x["cuando"] for x in esc)
assert any(x["tipo"] == "confirma" and ES.pr(min(c_lat["l"][-20:])) in x["cuando"] for x in esc)
assert a11["tendencia"]["estado"] == "agotandose" and {x["tipo"] for x in a11["escenarios"]} == {"confirma", "anula"}
a_sana = completo(velas_de(ruido(100, 195, 0.004, 0.003)))[0]
assert a_sana["tendencia"]["estado"] == "sana" and {x["tipo"] for x in a_sana["escenarios"]} == {"vigila", "debilita"}
cd_r, t_r = lateral_y_ruptura(148, 0.03, 1000)             # ruptura sin volumen
a_r = completo(cd_r)[0]
assert a_r["tendencia"]["estado"] == "ruptura_dudosa" and "Falta: volumen" in a_r["tendencia_explicada"]["resumen"]
assert any("más volumen" in x["cuando"] for x in a_r["escenarios"])
cd_r2, _ = lateral_y_ruptura(148, 0.03, 2800)
assert "ruptura confirmada" in completo(cd_r2)[0]["tendencia_explicada"]["resumen"]

# --- pocas velas: los porqués funcionan y lo demás se declara sin datos
a_c, _ = completo(velas_de(ruido(100, 100, 0.003, 0.002)))
assert a_c["estrategia"] is None and a_c["escenarios"] == [] and a_c["tendencia_explicada"]["estado"] == "sin_datos"
assert len(a_c["porques"]["bloques"]) == 5

# --- integrado en run.calcular: todo llega a signals.json y es serializable
run.FUENTES = [("falsa", falsa(0.004))]
sen, _ = run.calcular(cfg, ahora)
for tf_, a_ in sen["BTCUSDT"]["tf"].items():
    assert {"porques", "tendencia_explicada", "escenarios", "estrategia", "guia"} <= set(a_), tf_
assert sen["BTCUSDT"]["tf"]["1w"]["guia"]["horizonte"] == "3 a 6 meses"
tam = len(json.dumps(sen, ensure_ascii=False))
print("tamaño de signals.json de prueba (2 monedas):", tam, "bytes")
assert tam < 250_000

print("\nTODO OK")
