"""Descarga de velas (OHLCV) desde la API pública de Binance. No requiere cuenta."""

import time
from dataclasses import dataclass

import requests


@dataclass
class Candles:
    symbol: str
    interval: str
    open_times: list[int]
    opens: list[float]
    highs: list[float]
    lows: list[float]
    closes: list[float]
    volumes: list[float]


class MarketError(Exception):
    pass


class MarketClient:
    def __init__(self, base_url: str = "https://data-api.binance.vision", timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def get_candles(self, symbol: str, interval: str, limit: int = 300) -> Candles:
        """Devuelve solo velas CERRADAS (descarta la vela en curso)."""
        try:
            r = self.session.get(
                f"{self.base_url}/api/v3/klines",
                params={"symbol": symbol.upper(), "interval": interval, "limit": limit + 1},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise MarketError(f"Error de red al pedir {symbol}: {e}") from e
        if r.status_code == 400:
            raise MarketError(f"Par desconocido: {symbol}")
        if r.status_code != 200:
            raise MarketError(f"API respondió {r.status_code} para {symbol}: {r.text[:200]}")
        rows = r.json()
        now_ms = int(time.time() * 1000)
        rows = [row for row in rows if int(row[6]) < now_ms]  # row[6] = close time
        if not rows:
            raise MarketError(f"Sin datos para {symbol}")
        return Candles(
            symbol=symbol.upper(),
            interval=interval,
            open_times=[int(x[0]) for x in rows],
            opens=[float(x[1]) for x in rows],
            highs=[float(x[2]) for x in rows],
            lows=[float(x[3]) for x in rows],
            closes=[float(x[4]) for x in rows],
            volumes=[float(x[5]) for x in rows],
        )

    def symbol_exists(self, symbol: str) -> bool:
        try:
            r = self.session.get(
                f"{self.base_url}/api/v3/ticker/price", params={"symbol": symbol.upper()}, timeout=self.timeout
            )
            return r.status_code == 200
        except requests.RequestException:
            return False
