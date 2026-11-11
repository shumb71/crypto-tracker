"""Prueba variantes de los umbrales de aviso sobre las filas ya simuladas por backtest.py.

Regla anti-autoengaño: la variante se ELIGE mirando solo el primer 60 % del histórico y se
JUZGA en el último 40 %, que no ha visto. Si ahí no mejora al umbral actual, no se cambia.

Uso: python signals/backtest_umbrales.py --dir out_backtest
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import backtest as B  # noqa: E402

N = 400


def medir(series, fn, k, semilla=5):
    return {t: B.evaluar(series, fn, k, random.Random(semilla), N, t) for t in ("in", "out")}


def linea(nombre, r, actual=False):
    def c(x):
        if x.get("n", 0) < 5 or "p" not in x:
            return f"n={x.get('n', 0)}"
        return f"{x['ventaja']:+.2f} % (n={x['n']}, p={x['p']})"
    return f"| {nombre}{' ← actual' if actual else ''} | {c(r['in'])} | {c(r['out'])} |"


def tabla(titulo, filas_tabla):
    return "\n".join([f"### {titulo}", "", "| Variante | Muestra (primer 60 %) | Fuera de muestra (último 40 %) |", "|---|---|---|"]
                     + filas_tabla + [""])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="out_backtest")
    args = ap.parse_args()
    d = Path(args.dir)
    cfg = json.loads((Path(__file__).parent / "config.json").read_text())
    syms = cfg["symbols"]
    F = {(s, tf): B.leer_filas(d / f"filas_{s}_{tf}.csv.gz") for s in syms for tf in B.TFS
         if (d / f"filas_{s}_{tf}.csv.gz").exists()}
    out = ["# Variantes de umbrales", "",
           "Ventaja = movimiento a favor de la señal menos lo que da el azar con el mismo sentido. "
           "Una variante solo merece la pena si gana al umbral actual TAMBIÉN fuera de muestra.", ""]

    for tf in ("4h", "1d"):
        series = [F[(s, tf)] for s in syms if (s, tf) in F]
        if not series:
            continue
        k = 10
        out.append(f"## {B.run.NOMBRE_TF[tf]} — a {k} velas vista\n")
        # Agotamiento: cuántas señales de 4 hacen falta
        out.append(tabla("Aviso de agotamiento: nº mínimo de señales", [
            linea(f"≥{m} de 4", medir(series, lambda f, m=m: -f["dir"] if f["estado"] in ("sana", "agotandose")
                                      and f["dir"] and f["n_sen"] >= m else 0, k), m == 2) for m in (1, 2, 3)]))
        # Ruptura: fuerza de la vela, volumen y cruce
        filas_t = []
        for vela in (1.0, 1.5, 2.0):
            for vol in (1.0, 1.3, 1.6, 2.0):
                for cruce in (True, False):
                    fn = (lambda f, a=vela, b=vol, c=cruce: f["rup"] if f["rup"] and f["rup_vela"] >= a
                          and f["rup_vol"] >= b and (f["rup_cruce"] or not c) else 0)
                    filas_t.append(linea(f"vela ≥ {vela} ATR, volumen ≥ {vol}×, {'con' if cruce else 'sin exigir'} cruce",
                                         medir(series, fn, k), (vela, vol, cruce) == (1.5, 1.3, True)))
        out.append(tabla("Ruptura de lateral: qué se exige para confirmarla", filas_t))
        # Nota de la temporalidad
        out.append(tabla("Nota alcista de la temporalidad: desde qué score", [
            linea(f"score ≥ {u}", medir(series, lambda f, u=u: 1 if f["score"] >= u else 0, k), u == 0.5)
            for u in (0.3, 0.4, 0.5, 0.6, 0.7)]))
        out.append(tabla("Nota bajista de la temporalidad: desde qué score", [
            linea(f"score ≤ −{u}", medir(series, lambda f, u=u: -1 if f["score"] <= -u else 0, k), u == 0.5)
            for u in (0.3, 0.4, 0.5, 0.6, 0.7)]))

    # Señal fuerte global
    if all((s, tf) in F for s in syms for tf in B.TFS):
        velas = {s: B.leer_velas(d / "datos" / f"{s}_4h.csv.gz") for s in syms}
        out.append("## Señal fuerte global — a 18 velas de 4h (3 días)\n")
        filas_t = []
        for u in (0.3, 0.4, 0.5, 0.6):
            for ac in (2, 3, 4):
                c2 = dict(cfg, umbral_fuerte=u, min_timeframes_de_acuerdo=ac)
                # las filas de 4h leídas del CSV llevan i = posición en el fichero; hace falta el índice real de la vela
                g = {}
                for s in syms:
                    pos = {t: j for j, t in enumerate(velas[s]["t"])}
                    f4 = [dict(f, i=pos[f["t"]]) for f in F[(s, "4h")]]
                    g[s] = B.global_fuerte({tf: (f4 if tf == "4h" else F[(s, tf)]) for tf in B.TFS}, c2, velas[s])
                filas_t.append(linea(f"score ≥ {u} y ≥ {ac} temporalidades de acuerdo",
                                     medir(list(g.values()), lambda f: f["fuerte"] if f["n_tf"] == 4 else 0, 18),
                                     (u, ac) == (0.5, 3)))
        out.append(tabla("Aviso de señal fuerte: umbral y acuerdo", filas_t))
    txt = "\n".join(out)
    (d / "umbrales.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
