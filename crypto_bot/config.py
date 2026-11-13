"""Carga de configuración desde variables de entorno (o un archivo .env)."""

import os
from dataclasses import dataclass, field
from pathlib import Path

VALID_INTERVALS = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"}


def load_dotenv(path: str = ".env") -> None:
    """Lector mínimo de .env (no sobrescribe variables ya definidas)."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass
class Config:
    bot_token: str
    chat_id: str | None
    symbols: list[str] = field(default_factory=list)
    interval: str = "4h"
    check_every_minutes: int = 15
    signal_threshold: float = 3.0
    cooldown_hours: float = 12.0
    market_api_url: str = "https://data-api.binance.vision"
    state_file: str = "state.json"

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise SystemExit("Falta TELEGRAM_BOT_TOKEN. Copia .env.example a .env y rellénalo.")
        interval = os.environ.get("INTERVAL", "4h").strip()
        if interval not in VALID_INTERVALS:
            raise SystemExit(f"INTERVAL inválido: {interval}. Usa uno de {sorted(VALID_INTERVALS)}")
        symbols = [s.strip().upper() for s in os.environ.get("SYMBOLS", "BTCUSDT,ETHUSDT").split(",") if s.strip()]
        return cls(
            bot_token=token,
            chat_id=os.environ.get("TELEGRAM_CHAT_ID", "").strip() or None,
            symbols=symbols,
            interval=interval,
            check_every_minutes=max(1, int(os.environ.get("CHECK_EVERY_MINUTES", "15"))),
            signal_threshold=float(os.environ.get("SIGNAL_THRESHOLD", "3")),
            cooldown_hours=float(os.environ.get("COOLDOWN_HOURS", "12")),
            market_api_url=os.environ.get("MARKET_API_URL", "https://data-api.binance.vision").rstrip("/"),
            state_file=os.environ.get("STATE_FILE", "state.json"),
        )
