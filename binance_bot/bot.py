"""Bucle principal del bot de trading para Binance.

Uso:  python -m binance_bot.bot
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional

from .config import Config, cargar_config
from .estrategia import COMPRAR, VENDER, calcular_senal
from .exchange import BrokerBinance, BrokerPaper, crear_exchange
from .riesgo import ControlRiesgo, Posicion

log = logging.getLogger("bot")


class Bot:
    def __init__(self, cfg: Config, broker):
        self.cfg = cfg
        self.broker = broker
        self.riesgo = ControlRiesgo(cfg.stop_loss_pct, cfg.take_profit_pct,
                                    cfg.perdida_maxima_diaria)
        self.archivo_estado = Path(f"estado_{cfg.modo}.json")
        self.posicion: Optional[Posicion] = None
        self.coste_entrada = 0.0
        self._cargar_estado()

    # ---------- persistencia (para no perder la posición si el bot se reinicia) ----------
    def _cargar_estado(self) -> None:
        if self.cfg.modo == "paper" or not self.archivo_estado.exists():
            return
        datos = json.loads(self.archivo_estado.read_text())
        if datos.get("par") == self.cfg.par and datos.get("cantidad"):
            self.posicion = Posicion(datos["cantidad"], datos["precio_entrada"])
            self.coste_entrada = datos.get("coste", 0.0)
            log.info("Posición recuperada: %.8f a %.2f", self.posicion.cantidad,
                     self.posicion.precio_entrada)

    def _guardar_estado(self) -> None:
        if self.cfg.modo == "paper":
            return
        datos = {"par": self.cfg.par}
        if self.posicion:
            datos.update(cantidad=self.posicion.cantidad,
                         precio_entrada=self.posicion.precio_entrada, coste=self.coste_entrada)
        self.archivo_estado.write_text(json.dumps(datos, indent=2))

    # ---------- operaciones ----------
    def abrir(self, precio: float) -> None:
        if not self.riesgo.puede_abrir():
            log.warning("Límite de pérdida diaria alcanzado (%.2f). No se abren operaciones hoy.",
                        self.riesgo.resultado_dia)
            return
        if self.broker.saldo_quote() < self.cfg.cantidad_usdt:
            log.warning("Saldo insuficiente para comprar %.2f %s", self.cfg.cantidad_usdt,
                        self.broker.quote)
            return
        r = self.broker.comprar(self.cfg.cantidad_usdt, precio)
        self.posicion = Posicion(r["cantidad"], r["precio"])
        self.coste_entrada = r["coste"]
        self._guardar_estado()
        log.info("🟢 COMPRA %.8f %s a %.2f (coste %.2f %s) | SL %.2f | TP %.2f",
                 r["cantidad"], self.broker.base, r["precio"], r["coste"], self.broker.quote,
                 self.posicion.stop_loss(self.cfg.stop_loss_pct),
                 self.posicion.take_profit(self.cfg.take_profit_pct))

    def cerrar(self, precio: float, motivo: str) -> None:
        r = self.broker.vender(self.posicion.cantidad, precio)
        pnl = r["ingreso"] - self.coste_entrada
        self.riesgo.registrar_resultado(pnl)
        log.info("🔴 VENTA %.8f %s a %.2f por %s | resultado %+.2f %s | hoy %+.2f",
                 r["cantidad"], self.broker.base, r["precio"], motivo, pnl,
                 self.broker.quote, self.riesgo.resultado_dia)
        self.posicion, self.coste_entrada = None, 0.0
        self._guardar_estado()

    def paso(self) -> None:
        """Una revisión del mercado: comprueba salidas y luego señales."""
        velas = self.broker.velas(self.cfg.temporalidad, limite=self.cfg.media_lenta + 5)
        cierres = [v[4] for v in velas[:-1]]  # ignora la vela aún abierta
        precio = self.broker.precio()

        if self.posicion:
            motivo = self.riesgo.motivo_salida(self.posicion, precio)
            if motivo:
                self.cerrar(precio, motivo)
                return

        senal = calcular_senal(cierres, self.cfg.media_rapida, self.cfg.media_lenta)
        log.debug("Precio %.2f | señal %s | posición %s", precio, senal, bool(self.posicion))
        if senal == COMPRAR and not self.posicion:
            self.abrir(precio)
        elif senal == VENDER and self.posicion:
            self.cerrar(precio, "SEÑAL_VENTA")

    def ejecutar(self) -> None:
        log.info("Bot iniciado | modo=%s | par=%s | %s | SMA %d/%d",
                 self.cfg.modo.upper(), self.cfg.par, self.cfg.temporalidad,
                 self.cfg.media_rapida, self.cfg.media_lenta)
        while True:
            try:
                self.paso()
            except KeyboardInterrupt:
                raise
            except Exception as e:  # errores de red, etc.: registrar y seguir
                log.error("Error en la iteración: %s", e)
            time.sleep(self.cfg.intervalo)


def construir_bot(cfg: Config) -> Bot:
    ex = crear_exchange(cfg.modo, cfg.api_key, cfg.api_secret)
    if cfg.modo == "paper":
        broker = BrokerPaper(ex, cfg.par, cfg.saldo_paper)
    else:
        broker = BrokerBinance(ex, cfg.par)
    return Bot(cfg, broker)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("bot.log", encoding="utf-8")],
    )
    cfg = cargar_config()
    if cfg.modo == "live":
        log.warning("⚠️  MODO LIVE: se operará con DINERO REAL.")
    try:
        construir_bot(cfg).ejecutar()
    except KeyboardInterrupt:
        log.info("Bot detenido por el usuario.")


if __name__ == "__main__":
    main()
