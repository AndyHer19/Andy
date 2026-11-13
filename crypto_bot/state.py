"""Estado persistente: lista de monedas y última señal enviada por moneda."""

import json
import time
from pathlib import Path

from .signals import NEUTRAL


class State:
    def __init__(self, path: str, default_symbols: list[str]):
        self.path = Path(path)
        self.data: dict = {"symbols": list(default_symbols), "last": {}, "paused": False}
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    @property
    def symbols(self) -> list[str]:
        return self.data["symbols"]

    @property
    def paused(self) -> bool:
        return bool(self.data.get("paused"))

    def set_paused(self, value: bool) -> None:
        self.data["paused"] = value
        self.save()

    def add_symbol(self, s: str) -> bool:
        if s in self.symbols:
            return False
        self.symbols.append(s)
        self.save()
        return True

    def remove_symbol(self, s: str) -> bool:
        if s not in self.symbols:
            return False
        self.symbols.remove(s)
        self.data["last"].pop(s, None)
        self.save()
        return True

    def should_notify(self, symbol: str, signal: str, cooldown_hours: float, now: float | None = None) -> bool:
        """Avisa solo cuando la señal cambia, o si se repite pasado el cooldown.

        Volver a NEUTRAL no se notifica, pero "rearma" la moneda para la siguiente señal.
        """
        now = time.time() if now is None else now
        last = self.data["last"].get(symbol)
        if signal == NEUTRAL:
            if last and last.get("signal") != NEUTRAL:
                self.data["last"][symbol] = {"signal": NEUTRAL, "ts": now}
                self.save()
            return False
        if last and last.get("signal") == signal and now - last.get("ts", 0) < cooldown_hours * 3600:
            return False
        self.data["last"][symbol] = {"signal": signal, "ts": now}
        self.save()
        return True
