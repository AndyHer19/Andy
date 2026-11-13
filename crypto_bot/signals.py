"""Motor de señales: combina varios indicadores en una puntuación.

Puntuación positiva => sesgo de COMPRA, negativa => sesgo de VENTA.
Esto es una herramienta de apoyo, NO una recomendación financiera.
"""

from dataclasses import dataclass, field

from . import indicators as ind
from .market import Candles

BUY, SELL, NEUTRAL = "BUY", "SELL", "NEUTRAL"
MIN_CANDLES = 60


@dataclass
class Analysis:
    symbol: str
    interval: str
    price: float
    score: float
    signal: str
    reasons: list[str] = field(default_factory=list)
    rsi: float | None = None
    macd_hist: float | None = None
    ema50: float | None = None
    ema200: float | None = None
    bb_lower: float | None = None
    bb_upper: float | None = None
    atr: float | None = None
    change_24h_pct: float | None = None

    @property
    def strength(self) -> str:
        a = abs(self.score)
        if a >= 6:
            return "muy fuerte"
        if a >= 4.5:
            return "fuerte"
        return "moderada"

    def levels(self) -> tuple[float, float] | None:
        """Niveles orientativos (stop, objetivo) basados en ATR: 1.5x ATR de riesgo, 3x de recorrido."""
        if self.atr is None or self.signal == NEUTRAL:
            return None
        if self.signal == BUY:
            return self.price - 1.5 * self.atr, self.price + 3 * self.atr
        return self.price + 1.5 * self.atr, self.price - 3 * self.atr


INTERVAL_TO_HOURS = {"1m": 1 / 60, "3m": 0.05, "5m": 1 / 12, "15m": 0.25, "30m": 0.5, "1h": 1, "2h": 2,
                     "4h": 4, "6h": 6, "8h": 8, "12h": 12, "1d": 24, "3d": 72, "1w": 168}


def analyze(c: Candles, threshold: float = 3.0) -> Analysis:
    closes = c.closes
    if len(closes) < MIN_CANDLES:
        raise ValueError(f"Se necesitan al menos {MIN_CANDLES} velas, hay {len(closes)}")

    price = closes[-1]
    score = 0.0
    reasons: list[str] = []

    # 1) RSI: sobreventa / sobrecompra
    r = ind.rsi(closes)[-1]
    if r is not None:
        if r < 30:
            score += 2; reasons.append(f"🟢 RSI en sobreventa ({r:.1f})")
        elif r < 40:
            score += 1; reasons.append(f"🟢 RSI bajo ({r:.1f})")
        elif r > 70:
            score -= 2; reasons.append(f"🔴 RSI en sobrecompra ({r:.1f})")
        elif r > 60:
            score -= 1; reasons.append(f"🔴 RSI alto ({r:.1f})")

    # 2) MACD: cruces recientes del histograma
    _, _, hist = ind.macd(closes)
    h_now, h_prev = hist[-1], hist[-2]
    if h_now is not None and h_prev is not None:
        if h_prev <= 0 < h_now:
            score += 2; reasons.append("🟢 MACD cruzó al alza")
        elif h_prev >= 0 > h_now:
            score -= 2; reasons.append("🔴 MACD cruzó a la baja")
        elif h_now > 0 and h_now > h_prev:
            score += 0.5; reasons.append("🟢 Momentum MACD alcista creciendo")
        elif h_now < 0 and h_now < h_prev:
            score -= 0.5; reasons.append("🔴 Momentum MACD bajista creciendo")

    # 3) Tendencia con EMAs 50/200 (si no hay 200 velas, usa solo la 50)
    e50_series = ind.ema(closes, 50)
    e200_series = ind.ema(closes, 200)
    e50, e200 = e50_series[-1], e200_series[-1]
    if e50 is not None and e200 is not None:
        if price > e200 and e50 > e200:
            score += 1; reasons.append("🟢 Tendencia alcista (precio y EMA50 sobre EMA200)")
        elif price < e200 and e50 < e200:
            score -= 1; reasons.append("🔴 Tendencia bajista (precio y EMA50 bajo EMA200)")
        p50, p200 = e50_series[-2], e200_series[-2]
        if p50 is not None and p200 is not None:
            if p50 <= p200 and e50 > e200:
                score += 1.5; reasons.append("🟢 Cruce dorado (EMA50 cruza sobre EMA200)")
            elif p50 >= p200 and e50 < e200:
                score -= 1.5; reasons.append("🔴 Cruce de la muerte (EMA50 cruza bajo EMA200)")
    elif e50 is not None:
        if price > e50:
            score += 0.5; reasons.append("🟢 Precio sobre EMA50")
        else:
            score -= 0.5; reasons.append("🔴 Precio bajo EMA50")

    # 4) Bandas de Bollinger
    lower, _, upper = ind.bollinger(closes)
    bl, bu = lower[-1], upper[-1]
    if bl is not None and bu is not None:
        if price < bl:
            score += 1; reasons.append("🟢 Precio bajo la banda inferior de Bollinger")
        elif price > bu:
            score -= 1; reasons.append("🔴 Precio sobre la banda superior de Bollinger")

    # 5) Volumen: refuerza la señal si hay un pico
    vol_avg = ind.sma(c.volumes, 20)[-2]
    if vol_avg and c.volumes[-1] > 1.8 * vol_avg and score != 0:
        score *= 1.25
        reasons.append(f"📊 Volumen alto ({c.volumes[-1] / vol_avg:.1f}x la media) refuerza la señal")

    if score >= threshold:
        signal = BUY
    elif score <= -threshold:
        signal = SELL
    else:
        signal = NEUTRAL

    # Cambio aproximado en 24h
    hours = INTERVAL_TO_HOURS.get(c.interval, 0)
    change = None
    if hours and hours <= 24:
        back = int(round(24 / hours))
        if len(closes) > back:
            change = (price / closes[-1 - back] - 1) * 100

    return Analysis(
        symbol=c.symbol, interval=c.interval, price=price, score=round(score, 2), signal=signal,
        reasons=reasons, rsi=r, macd_hist=h_now, ema50=e50, ema200=e200, bb_lower=bl, bb_upper=bu,
        atr=ind.atr(c.highs, c.lows, closes)[-1], change_24h_pct=change,
    )
