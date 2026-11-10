"""Ejecuta el motor: baja velas, puntúa, avisa por Telegram y guarda resultados.

Uso:  python signals/run.py --out out [--estado]
Variables de entorno (Secrets de GitHub): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
Solo usa datos públicos de mercado: no necesita claves de ningún exchange.
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
import engine  # noqa: E402

MS = {"1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000, "1w": 604_800_000}
NOMBRE_TF = {"1h": "1h", "4h": "4h", "1d": "1d", "1w": "1s"}
QUOTES = ("USDT", "USDC", "FDUSD", "EUR", "BTC", "ETH")
AVISO = "<i>Puntuación de confluencia técnica: no es una probabilidad ni un consejo de inversión.</i>"


def http_json(url, data=None, timeout=20):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "crypto-tracker-signals"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def partir(symbol):
    for q in QUOTES:
        if symbol.endswith(q) and len(symbol) > len(q):
            return symbol[:-len(q)], q
    raise ValueError(f"No sé separar el par {symbol}")


# ---------- Fuentes de velas (cada una devuelve filas [t, o, h, l, c, v]) ----------

def _binance(base_url):
    def f(symbol, tf):
        rows = http_json(f"{base_url}/api/v3/klines?symbol={symbol}&interval={tf}&limit=500")
        return [[int(r[0]), *map(float, r[1:6])] for r in rows]
    return f


def _bingx(symbol, tf):
    b, q = partir(symbol)
    d = http_json("https://open-api.bingx.com/openApi/spot/v2/market/kline"
                  f"?symbol={b}-{q}&interval={tf}&limit=500")
    rows = d["data"]
    if rows and isinstance(rows[0], dict):
        return [[int(r["time"]), float(r["open"]), float(r["high"]), float(r["low"]),
                 float(r["close"]), float(r["volume"])] for r in rows]
    return [[int(r[0]), *map(float, r[1:6])] for r in rows]


def _okx(symbol, tf):
    b, q = partir(symbol)
    bar = {"1h": "1H", "4h": "4H", "1d": "1Dutc", "1w": "1Wutc"}[tf]
    d = http_json(f"https://www.okx.com/api/v5/market/candles?instId={b}-{q}&bar={bar}&limit=300")
    return [[int(r[0]), *map(float, r[1:6])] for r in d["data"]]


FUENTES = [
    ("binance", _binance("https://data-api.binance.vision")),
    ("binance", _binance("https://api.binance.com")),
    ("bingx", _bingx),
    ("okx", _okx),
]


def velas(symbol, tf, ahora_ms):
    """Prueba cada fuente en orden y devuelve solo velas cerradas."""
    errores = []
    for nombre, f in FUENTES:
        try:
            rows = sorted(f(symbol, tf), key=lambda r: r[0])
            rows = [r for r in rows if r[0] + MS[tf] <= ahora_ms]  # descarta la vela en curso
            if len(rows) < 60:
                raise ValueError(f"solo {len(rows)} velas")
            if ahora_ms - (rows[-1][0] + MS[tf]) > 2 * MS[tf]:
                raise ValueError("datos atrasados")
            cols = list(zip(*rows))
            return nombre, dict(zip("tohlcv", (list(x) for x in cols)))
        except Exception as e:  # pasa a la siguiente fuente
            errores.append(f"{nombre}: {type(e).__name__} {e}")
    raise RuntimeError(f"Sin datos para {symbol} {tf} -> " + " | ".join(errores))


# ---------- Formato de mensajes ----------

def num(x):
    """Precio con formato español: 103.250 / 3.412,5 / 0,4321"""
    dec = 0 if x >= 10_000 else 1 if x >= 100 else 2 if x >= 1 else 4
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def bola(score):
    return "🟢" if score >= 0.2 else "🔴" if score <= -0.2 else "🟡"


def bloque(symbol, s):
    base = partir(symbol)[0]
    g = s["global"]
    out = [f"<b>{base}</b> {num(s['precio'])} $ — {bola(g['score'])} {g['etiqueta']} <b>{g['nota']}/10</b>"]
    out.append(" · ".join(f"{NOMBRE_TF[tf]} {bola(a['score'])} {a['nota']}"
                          for tf, a in s["tf"].items() if a))
    notas = [f"divergencia {a['divergencia']['tipo']} en {NOMBRE_TF[tf]}"
             for tf, a in s["tf"].items() if a and a["divergencia"]]
    notas += [f"volatilidad comprimida en {NOMBRE_TF[tf]}"
              for tf, a in s["tf"].items() if a and a["compresion"]]
    if notas:
        out.append("⚠️ " + "; ".join(notas))
    return "\n".join(out)


def resumen(senales, ahora):
    hora = ahora.astimezone(ZoneInfo("Europe/Madrid")).strftime("%d/%m %H:%M")
    partes = [f"📊 <b>Señales cripto</b> — {hora}"]
    partes += [bloque(sym, s) for sym, s in senales.items()]
    partes.append("Nota: 0 = todo bajista, 5 = neutral, 10 = todo alcista.\n" + AVISO)
    return "\n\n".join(partes)


# ---------- Telegram ----------

class Telegram:
    def __init__(self, token, chat_id):
        self.token, self.chat_id = token, str(chat_id or "")
        self.activo = bool(token and chat_id)

    def _api(self, metodo, **params):
        data = urllib.parse.urlencode(params).encode()
        return http_json(f"https://api.telegram.org/bot{self.token}/{metodo}", data=data)

    def enviar(self, texto):
        if not self.activo:
            print("[telegram desactivado] " + texto.replace("\n", " | ")[:200])
            return
        self._api("sendMessage", chat_id=self.chat_id, text=texto,
                  parse_mode="HTML", disable_web_page_preview="true")

    def comandos(self, offset):
        """Devuelve (comandos recibidos del chat autorizado, nuevo offset)."""
        if not self.activo:
            return [], offset
        r = self._api("getUpdates", offset=offset, timeout=0,
                      allowed_updates=json.dumps(["message"]))
        cmds = []
        for u in r.get("result", []):
            offset = u["update_id"] + 1
            m = u.get("message") or {}
            if str(m.get("chat", {}).get("id")) != self.chat_id:
                continue  # ignora a cualquiera que no seas tú
            texto = (m.get("text") or "").strip().lower().split("@")[0]
            if texto.startswith("/"):
                cmds.append(texto.split()[0])
        return cmds, offset


AYUDA = ("🤖 <b>Bot de señales</b>\n/estado — resumen de todas las monedas\n/ayuda — este mensaje\n\n"
         "Reviso el mercado cada 15 minutos aprox. y te aviso solo cuando hay señal fuerte "
         "o una divergencia nueva. La respuesta a un comando puede tardar unos minutos.")


# ---------- Programa principal ----------

def calcular(cfg, ahora_ms):
    senales, fuentes = {}, set()
    for sym in cfg["symbols"]:
        por_tf, precio = {}, None
        for tf in cfg["timeframes"]:
            fuente, c = velas(sym, tf, ahora_ms)
            fuentes.add(fuente)
            por_tf[tf] = engine.analizar_tf(c)
            if tf == "1h":
                precio = c["c"][-1]
        g = engine.combinar(por_tf, cfg["timeframes"], cfg["umbral_fuerte"],
                            cfg["min_timeframes_de_acuerdo"])
        if g:
            senales[sym] = {"precio": precio, "global": g, "tf": por_tf}
    return senales, sorted(fuentes)


def alertas(cfg, senales, estado):
    """Compara con el estado anterior y devuelve los avisos nuevos."""
    msgs = []
    est_sym = estado.setdefault("simbolos", {})
    vistos = estado.setdefault("divergencias", {})
    for sym, s in senales.items():
        g, base = s["global"], partir(sym)[0]
        antes = est_sym.get(sym, "normal")
        if g["fuerte"]:
            ahora = "fuerte_alcista" if g["lado"] > 0 else "fuerte_bajista"
        elif antes != "normal" and abs(g["score"]) >= cfg["umbral_salida"] \
                and (g["lado"] > 0) == (antes == "fuerte_alcista"):
            ahora = antes  # histéresis: sigue vigente hasta que afloje de verdad
        else:
            ahora = "normal"
        if ahora != antes:
            if ahora == "normal":
                msgs.append(f"⚪ <b>{base}</b>: la señal fuerte se ha desinflado.\n\n" + bloque(sym, s))
            else:
                icono = "🚀" if ahora == "fuerte_alcista" else "🔻"
                msgs.append(f"{icono} <b>Señal fuerte en {base}</b> "
                            f"({g['acuerdo']} temporalidades de acuerdo)\n\n" + bloque(sym, s))
        est_sym[sym] = ahora
        for tf in cfg["avisar_divergencias_en"]:
            a = s["tf"].get(tf)
            if a and a["divergencia"]:
                clave = f"{sym}|{tf}|{a['divergencia']['tipo']}|{a['divergencia']['t']}"
                if clave not in vistos:
                    vistos[clave] = int(time.time())
                    msgs.append(f"🔀 <b>{base}</b>: divergencia {a['divergencia']['tipo']} nueva en "
                                f"{NOMBRE_TF[tf]} (RSI {a['rsi']}).\n\n" + bloque(sym, s))
    # limpia divergencias de hace más de 60 días
    limite = time.time() - 60 * 86400
    estado["divergencias"] = {k: v for k, v in vistos.items() if v > limite}
    return msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--estado", action="store_true", help="envía el resumen completo")
    args = ap.parse_args()

    raiz = Path(__file__).parent
    cfg = json.loads((raiz / "config.json").read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    f_estado = out / "state.json"
    estado = json.loads(f_estado.read_text(encoding="utf-8")) if f_estado.exists() else {}
    primera_vez = not estado

    ahora = datetime.now(timezone.utc)
    senales, fuentes = calcular(cfg, int(ahora.timestamp() * 1000))

    tg = Telegram(os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID"))
    if not tg.activo:
        print("AVISO: faltan los secrets TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID; no se envía nada.")

    cmds, estado["tg_offset"] = tg.comandos(estado.get("tg_offset", 0))
    msgs = alertas(cfg, senales, estado)
    if primera_vez:
        msgs = []  # en el primer arranque manda solo el resumen, no una ráfaga de avisos
    for m in msgs:
        tg.enviar(m + "\n\n" + AVISO)
    if "/ayuda" in cmds or "/start" in cmds:
        tg.enviar(AYUDA)
    if args.estado or primera_vez or "/estado" in cmds or "/start" in cmds:
        tg.enviar(resumen(senales, ahora))

    (out / "signals.json").write_text(json.dumps(
        {"generado": ahora.isoformat(timespec="seconds"), "fuentes": fuentes, "senales": senales},
        ensure_ascii=False, indent=1), encoding="utf-8")
    f_estado.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {len(senales)} monedas, {len(msgs)} avisos, fuentes: {fuentes}")


if __name__ == "__main__":
    main()
