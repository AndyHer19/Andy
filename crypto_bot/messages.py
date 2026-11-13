"""Formato de los mensajes de Telegram (HTML)."""

from html import escape

from .signals import BUY, SELL, Analysis

DISCLAIMER = "<i>⚠️ Señal automática basada en indicadores técnicos. No es consejo financiero: la decisión es tuya.</i>"


def fmt_price(p: float) -> str:
    if p >= 1000:
        return f"{p:,.2f}"
    if p >= 1:
        return f"{p:,.4f}"
    return f"{p:.8f}".rstrip("0")


def _header(a: Analysis) -> str:
    if a.signal == BUY:
        return f"🟢 <b>POSIBLE COMPRA</b> ({a.strength}) — <b>{escape(a.symbol)}</b>"
    if a.signal == SELL:
        return f"🔴 <b>POSIBLE VENTA</b> ({a.strength}) — <b>{escape(a.symbol)}</b>"
    return f"⚪ <b>NEUTRAL</b> — <b>{escape(a.symbol)}</b>"


def format_analysis(a: Analysis, disclaimer: bool = True) -> str:
    lines = [_header(a), ""]
    price_line = f"💰 Precio: <b>{fmt_price(a.price)}</b>"
    if a.change_24h_pct is not None:
        price_line += f" ({a.change_24h_pct:+.2f}% 24h)"
    lines.append(price_line)
    lines.append(f"⏱ Velas: {escape(a.interval)} · Puntuación: <b>{a.score:+.1f}</b>")
    if a.rsi is not None:
        lines.append(f"📈 RSI(14): {a.rsi:.1f}")
    if a.ema50 is not None:
        ema_line = f"📉 EMA50: {fmt_price(a.ema50)}"
        if a.ema200 is not None:
            ema_line += f" · EMA200: {fmt_price(a.ema200)}"
        lines.append(ema_line)
    if a.reasons:
        lines += ["", "<b>Motivos:</b>"] + [f"• {escape(r)}" for r in a.reasons]
    lv = a.levels()
    if lv:
        stop, target = lv
        lines += ["", "<b>Niveles orientativos (ATR):</b>",
                  f"🛑 Stop: {fmt_price(stop)}", f"🎯 Objetivo: {fmt_price(target)}"]
    if disclaimer:
        lines += ["", DISCLAIMER]
    return "\n".join(lines)


def format_summary(analyses: list[Analysis], errors: list[str]) -> str:
    icon = {BUY: "🟢", SELL: "🔴"}
    lines = ["📊 <b>Resumen del mercado</b>", ""]
    for a in sorted(analyses, key=lambda x: x.score, reverse=True):
        rsi = f"RSI {a.rsi:.0f}" if a.rsi is not None else ""
        lines.append(f"{icon.get(a.signal, '⚪')} <b>{escape(a.symbol)}</b> {fmt_price(a.price)} · "
                     f"score {a.score:+.1f} · {rsi}")
    for e in errors:
        lines.append(f"⚠️ {escape(e)}")
    lines += ["", DISCLAIMER]
    return "\n".join(lines)


HELP = """🤖 <b>Bot de señales cripto</b>

Vigilo el mercado y te aviso cuando varios indicadores (RSI, MACD, EMAs, Bollinger, volumen) coinciden en una posible <b>compra</b> o <b>venta</b>.

<b>Comandos:</b>
/analizar BTCUSDT — análisis al momento de una moneda
/resumen — estado de todas tus monedas
/lista — monedas vigiladas
/agregar SOLUSDT — vigilar una moneda
/quitar SOLUSDT — dejar de vigilarla
/pausar — pausar alertas automáticas
/reanudar — reanudar alertas
/config — ver configuración

""" + DISCLAIMER
