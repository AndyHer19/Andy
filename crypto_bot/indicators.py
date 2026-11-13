"""Indicadores técnicos calculados con Python puro.

Todas las funciones reciben listas de floats ordenadas de la más antigua a la
más reciente y devuelven listas del mismo largo (con None donde aún no hay
suficientes datos).
"""

from math import sqrt

Series = list[float | None]


def sma(values: list[float], period: int) -> Series:
    out: Series = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    window = sum(values[:period])
    out[period - 1] = window / period
    for i in range(period, len(values)):
        window += values[i] - values[i - period]
        out[i] = window / period
    return out


def ema(values: list[float], period: int) -> Series:
    """EMA sembrada con la SMA de los primeros `period` valores."""
    out: Series = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    k = 2 / (period + 1)
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def _ema_of_optional(values: Series, period: int) -> Series:
    """EMA sobre una serie que empieza con None (p. ej. la línea MACD)."""
    start = next((i for i, v in enumerate(values) if v is not None), None)
    out: Series = [None] * len(values)
    if start is None:
        return out
    tail = ema([v for v in values[start:]], period)  # type: ignore[misc]
    out[start:] = tail
    return out


def rsi(closes: list[float], period: int = 14) -> Series:
    """RSI con suavizado de Wilder."""
    out: Series = [None] * len(closes)
    if len(closes) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        change = closes[i] - closes[i - 1]
        gains += max(change, 0)
        losses += max(-change, 0)
    avg_gain, avg_loss = gains / period, losses / period

    def value(g: float, l: float) -> float:
        if l == 0:
            return 100.0 if g > 0 else 50.0
        return 100 - 100 / (1 + g / l)

    out[period] = value(avg_gain, avg_loss)
    for i in range(period + 1, len(closes)):
        change = closes[i] - closes[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(change, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-change, 0)) / period
        out[i] = value(avg_gain, avg_loss)
    return out


def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[Series, Series, Series]:
    """Devuelve (línea MACD, línea de señal, histograma)."""
    ema_fast, ema_slow = ema(closes, fast), ema(closes, slow)
    line: Series = [
        (f - s) if f is not None and s is not None else None for f, s in zip(ema_fast, ema_slow)
    ]
    sig = _ema_of_optional(line, signal)
    hist: Series = [(m - s) if m is not None and s is not None else None for m, s in zip(line, sig)]
    return line, sig, hist


def bollinger(closes: list[float], period: int = 20, mult: float = 2.0) -> tuple[Series, Series, Series]:
    """Devuelve (banda inferior, media, banda superior)."""
    mid = sma(closes, period)
    lower: Series = [None] * len(closes)
    upper: Series = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        m = mid[i]
        if m is None:
            continue
        window = closes[i - period + 1 : i + 1]
        std = sqrt(sum((x - m) ** 2 for x in window) / period)
        lower[i], upper[i] = m - mult * std, m + mult * std
    return lower, mid, upper


def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> Series:
    """Average True Range (Wilder). Útil para estimar stop-loss / objetivo."""
    n = len(closes)
    out: Series = [None] * n
    if n <= period:
        return out
    trs = [highs[0] - lows[0]]
    for i in range(1, n):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    prev = sum(trs[1 : period + 1]) / period
    out[period] = prev
    for i in range(period + 1, n):
        prev = (prev * (period - 1) + trs[i]) / period
        out[i] = prev
    return out
