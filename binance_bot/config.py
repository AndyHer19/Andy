"""Carga y valida la configuración desde variables de entorno / archivo .env."""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv es opcional
    pass

MODOS_VALIDOS = ("paper", "testnet", "live")
FRASE_CONFIRMACION = "SI_ENTIENDO_EL_RIESGO"


@dataclass
class Config:
    modo: str = "paper"
    api_key: str = ""
    api_secret: str = ""
    par: str = "BTC/USDT"
    temporalidad: str = "15m"
    media_rapida: int = 9
    media_lenta: int = 21
    cantidad_usdt: float = 20.0
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0
    perdida_maxima_diaria: float = 50.0
    saldo_paper: float = 1000.0
    intervalo: int = 60
    confirmar_live: str = ""

    def validar(self) -> None:
        if self.modo not in MODOS_VALIDOS:
            raise ValueError(f"MODO debe ser uno de {MODOS_VALIDOS}, no '{self.modo}'")
        if self.media_rapida >= self.media_lenta:
            raise ValueError("MEDIA_RAPIDA debe ser menor que MEDIA_LENTA")
        if self.cantidad_usdt <= 0:
            raise ValueError("CANTIDAD_POR_OPERACION_USDT debe ser mayor que 0")
        if not (0 < self.stop_loss_pct < 100) or not (0 < self.take_profit_pct < 1000):
            raise ValueError("STOP_LOSS_PCT / TAKE_PROFIT_PCT fuera de rango")
        if self.modo in ("testnet", "live") and not (self.api_key and self.api_secret):
            raise ValueError(f"El modo '{self.modo}' necesita BINANCE_API_KEY y BINANCE_API_SECRET")
        if self.modo == "live" and self.confirmar_live != FRASE_CONFIRMACION:
            raise ValueError(
                f"Para operar con dinero real pon CONFIRMAR_LIVE={FRASE_CONFIRMACION} en tu .env"
            )


def cargar_config() -> Config:
    e = os.getenv
    cfg = Config(
        modo=e("MODO", "paper").strip().lower(),
        api_key=e("BINANCE_API_KEY", "").strip(),
        api_secret=e("BINANCE_API_SECRET", "").strip(),
        par=e("PAR", "BTC/USDT").strip().upper(),
        temporalidad=e("TEMPORALIDAD", "15m").strip(),
        media_rapida=int(e("MEDIA_RAPIDA", "9")),
        media_lenta=int(e("MEDIA_LENTA", "21")),
        cantidad_usdt=float(e("CANTIDAD_POR_OPERACION_USDT", "20")),
        stop_loss_pct=float(e("STOP_LOSS_PCT", "2")),
        take_profit_pct=float(e("TAKE_PROFIT_PCT", "4")),
        perdida_maxima_diaria=float(e("PERDIDA_MAXIMA_DIARIA_USDT", "50")),
        saldo_paper=float(e("SALDO_PAPER_USDT", "1000")),
        intervalo=int(e("INTERVALO_SEGUNDOS", "60")),
        confirmar_live=e("CONFIRMAR_LIVE", "").strip(),
    )
    cfg.validar()
    return cfg
