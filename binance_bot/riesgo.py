"""Reglas de gestión del riesgo: stop loss, take profit y límite de pérdida diaria."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Posicion:
    cantidad: float      # cantidad del activo base (ej. BTC)
    precio_entrada: float

    def stop_loss(self, pct: float) -> float:
        return self.precio_entrada * (1 - pct / 100)

    def take_profit(self, pct: float) -> float:
        return self.precio_entrada * (1 + pct / 100)


@dataclass
class ControlRiesgo:
    stop_loss_pct: float
    take_profit_pct: float
    perdida_maxima_diaria: float
    _dia: date = field(default_factory=date.today)
    _resultado_dia: float = 0.0

    def _reiniciar_si_nuevo_dia(self, hoy: Optional[date] = None) -> None:
        hoy = hoy or date.today()
        if hoy != self._dia:
            self._dia, self._resultado_dia = hoy, 0.0

    def registrar_resultado(self, pnl: float, hoy: Optional[date] = None) -> None:
        self._reiniciar_si_nuevo_dia(hoy)
        self._resultado_dia += pnl

    def puede_abrir(self, hoy: Optional[date] = None) -> bool:
        self._reiniciar_si_nuevo_dia(hoy)
        return self._resultado_dia > -self.perdida_maxima_diaria

    @property
    def resultado_dia(self) -> float:
        return self._resultado_dia

    def motivo_salida(self, pos: Posicion, precio: float) -> Optional[str]:
        """Devuelve 'STOP_LOSS' o 'TAKE_PROFIT' si hay que cerrar la posición."""
        if precio <= pos.stop_loss(self.stop_loss_pct):
            return "STOP_LOSS"
        if precio >= pos.take_profit(self.take_profit_pct):
            return "TAKE_PROFIT"
        return None
