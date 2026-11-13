"""Bucle principal: atiende comandos de Telegram y revisa el mercado periódicamente."""

import logging
import time
from html import escape

from .config import Config
from .market import MarketClient, MarketError
from .messages import HELP, format_analysis, format_summary
from .signals import Analysis, analyze
from .state import State
from .telegram_api import Telegram

log = logging.getLogger(__name__)

COMMANDS = [
    ("analizar", "Analizar una moneda, ej: /analizar BTCUSDT"),
    ("resumen", "Estado de todas las monedas vigiladas"),
    ("lista", "Ver monedas vigiladas"),
    ("agregar", "Vigilar una moneda, ej: /agregar SOLUSDT"),
    ("quitar", "Dejar de vigilar una moneda"),
    ("pausar", "Pausar alertas automáticas"),
    ("reanudar", "Reanudar alertas automáticas"),
    ("config", "Ver configuración"),
    ("ayuda", "Ayuda"),
]


def normalize_symbol(raw: str) -> str:
    s = raw.strip().upper().replace("/", "").replace("-", "")
    # Permite escribir solo "BTC" -> "BTCUSDT"
    if len(s) <= 5 or not s.endswith(("USDT", "USDC", "FDUSD", "BTC", "ETH", "EUR", "TRY", "BRL")):
        s += "USDT"
    return s


class Bot:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.tg = Telegram(cfg.bot_token)
        self.market = MarketClient(cfg.market_api_url)
        self.state = State(cfg.state_file, cfg.symbols)
        self.next_check = 0.0

    # ---------- Análisis ----------
    def analyze_symbol(self, symbol: str) -> Analysis:
        candles = self.market.get_candles(symbol, self.cfg.interval, limit=300)
        return analyze(candles, self.cfg.signal_threshold)

    def scan_market(self) -> None:
        if self.state.paused or not self.cfg.chat_id:
            return
        log.info("Revisando %d monedas...", len(self.state.symbols))
        for symbol in list(self.state.symbols):
            try:
                a = self.analyze_symbol(symbol)
            except (MarketError, ValueError) as e:
                log.warning("%s: %s", symbol, e)
                continue
            log.info("%s precio=%s score=%+.1f señal=%s", symbol, a.price, a.score, a.signal)
            if self.state.should_notify(symbol, a.signal, self.cfg.cooldown_hours):
                self.tg.send(self.cfg.chat_id, format_analysis(a))

    # ---------- Comandos ----------
    def handle(self, msg: dict) -> None:
        chat_id = str(msg["chat"]["id"])
        text = (msg.get("text") or "").strip()
        if not text.startswith("/"):
            return
        parts = text.split()
        cmd = parts[0][1:].split("@")[0].lower()
        args = parts[1:]

        if not self.cfg.chat_id:
            self.tg.send(chat_id, f"Tu chat id es <code>{chat_id}</code>.\nPonlo en <b>TELEGRAM_CHAT_ID</b> "
                                  "en el archivo .env y reinicia el bot.")
            return
        if chat_id != self.cfg.chat_id:
            log.warning("Ignorando mensaje de chat no autorizado %s", chat_id)
            return

        reply = lambda t: self.tg.send(chat_id, t)  # noqa: E731

        if cmd in ("start", "ayuda", "help"):
            reply(HELP)
        elif cmd == "analizar":
            if not args:
                return reply("Uso: /analizar BTCUSDT")
            symbol = normalize_symbol(args[0])
            try:
                reply(format_analysis(self.analyze_symbol(symbol)))
            except (MarketError, ValueError) as e:
                reply(f"⚠️ {escape(str(e))}")
        elif cmd == "resumen":
            analyses, errors = [], []
            for s in self.state.symbols:
                try:
                    analyses.append(self.analyze_symbol(s))
                except (MarketError, ValueError) as e:
                    errors.append(f"{s}: {e}")
            reply(format_summary(analyses, errors))
        elif cmd == "lista":
            syms = ", ".join(self.state.symbols) or "(ninguna)"
            reply(f"👀 Monedas vigiladas: <b>{escape(syms)}</b>")
        elif cmd == "agregar":
            if not args:
                return reply("Uso: /agregar SOLUSDT")
            symbol = normalize_symbol(args[0])
            if not self.market.symbol_exists(symbol):
                return reply(f"⚠️ No encuentro el par {escape(symbol)} en el mercado.")
            ok = self.state.add_symbol(symbol)
            reply(f"✅ Ahora vigilo {symbol}" if ok else f"Ya vigilaba {symbol}")
        elif cmd == "quitar":
            if not args:
                return reply("Uso: /quitar SOLUSDT")
            symbol = normalize_symbol(args[0])
            ok = self.state.remove_symbol(symbol)
            reply(f"🗑 Dejé de vigilar {symbol}" if ok else f"No estaba vigilando {symbol}")
        elif cmd == "pausar":
            self.state.set_paused(True)
            reply("⏸ Alertas automáticas pausadas. Usa /reanudar para volver a activarlas.")
        elif cmd == "reanudar":
            self.state.set_paused(False)
            self.next_check = 0
            reply("▶️ Alertas automáticas reanudadas.")
        elif cmd == "config":
            reply(
                "⚙️ <b>Configuración</b>\n"
                f"Velas: {self.cfg.interval}\n"
                f"Revisión cada: {self.cfg.check_every_minutes} min\n"
                f"Umbral de señal: ±{self.cfg.signal_threshold}\n"
                f"Cooldown: {self.cfg.cooldown_hours} h\n"
                f"Alertas: {'pausadas' if self.state.paused else 'activas'}"
            )
        else:
            reply("No conozco ese comando. Usa /ayuda")

    # ---------- Bucle ----------
    def run(self) -> None:
        self.tg.set_commands(COMMANDS)
        if self.cfg.chat_id:
            self.tg.send(self.cfg.chat_id, "🤖 Bot de señales iniciado. Usa /ayuda para ver los comandos.")
        else:
            log.warning("TELEGRAM_CHAT_ID vacío: escribe /start al bot para obtener tu chat id.")
        while True:
            try:
                if time.time() >= self.next_check:
                    self.scan_market()
                    self.next_check = time.time() + self.cfg.check_every_minutes * 60
                wait = int(max(1, min(20, self.next_check - time.time())))
                for update in self.tg.get_updates(timeout=wait):
                    if "message" in update:
                        try:
                            self.handle(update["message"])
                        except Exception:
                            log.exception("Error manejando comando")
            except KeyboardInterrupt:
                log.info("Saliendo...")
                return
            except Exception:
                log.exception("Error en el bucle principal; reintentando en 10 s")
                time.sleep(10)
