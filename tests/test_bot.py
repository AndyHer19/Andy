from datetime import date

import pytest

from binance_bot.backtest import backtest
from binance_bot.bot import Bot
from binance_bot.config import Config
from binance_bot.estrategia import COMPRAR, VENDER, calcular_senal, media_movil
from binance_bot.exchange import BrokerPaper
from binance_bot.riesgo import ControlRiesgo, Posicion


def test_media_movil():
    assert media_movil([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]


def test_senal_compra_y_venta():
    bajada_y_subida = [10] * 5 + [9, 8, 7, 6] + [12]
    assert calcular_senal(bajada_y_subida, 2, 4) == COMPRAR
    subida_y_bajada = [10] * 5 + [11, 12, 13, 14] + [8]
    assert calcular_senal(subida_y_bajada, 2, 4) == VENDER
    assert calcular_senal([10] * 10, 2, 4) is None


def test_riesgo_sl_tp_y_limite_diario():
    r = ControlRiesgo(2, 4, 50)
    pos = Posicion(1, 100)
    assert r.motivo_salida(pos, 97.9) == "STOP_LOSS"
    assert r.motivo_salida(pos, 104.1) == "TAKE_PROFIT"
    assert r.motivo_salida(pos, 101) is None
    hoy = date(2026, 1, 1)
    r.registrar_resultado(-60, hoy)
    assert not r.puede_abrir(hoy)
    assert r.puede_abrir(date(2026, 1, 2))  # se reinicia al día siguiente


def test_config_protege_modo_live():
    with pytest.raises(ValueError):
        Config(modo="live", api_key="k", api_secret="s").validar()
    Config(modo="live", api_key="k", api_secret="s",
           confirmar_live="SI_ENTIENDO_EL_RIESGO").validar()
    with pytest.raises(ValueError):
        Config(modo="testnet").validar()


class ExchangeFalso:
    def __init__(self, cierres):
        self.cierres, self.precio = cierres, cierres[-1]

    def fetch_ohlcv(self, par, tf, limit=100):
        return [[i, c, c, c, c, 1] for i, c in enumerate(self.cierres)] + [[0, 0, 0, 0, 0, 0]]

    def fetch_ticker(self, par):
        return {"last": self.precio}


def test_bot_compra_y_cierra_por_take_profit():
    cfg = Config(media_rapida=2, media_lenta=4, cantidad_usdt=100,
                 take_profit_pct=4, stop_loss_pct=2)
    ex = ExchangeFalso([10] * 5 + [9, 8, 7, 6] + [12])
    bot = Bot(cfg, BrokerPaper(ex, "BTC/USDT", 1000))
    bot.paso()
    assert bot.posicion is not None and bot.broker.saldo_quote() == 900
    ex.precio = 13  # +8 % -> take profit
    bot.paso()
    assert bot.posicion is None
    assert bot.broker.saldo_quote() > 1000


def test_backtest_sintetico():
    precios = [100] * 30 + [100 - i for i in range(10)] + [90 + i * 2 for i in range(20)]
    velas = [[i, p, p * 1.001, p * 0.999, p, 1] for i, p in enumerate(precios)]
    r = backtest(velas, 3, 8, 20, 2, 4)
    assert r["operaciones"] >= 1
    assert r["resultado"] > 0
