"""Prueba la estrategia con datos históricos de Binance antes de arriesgar dinero.

Uso:  python -m binance_bot.backtest --par BTC/USDT --temporalidad 1h --velas 1000
"""
import argparse

from .estrategia import COMPRAR, VENDER, senal_en
from .exchange import COMISION
from .riesgo import Posicion


def backtest(velas, rapida, lenta, cantidad_usdt, sl_pct, tp_pct, saldo_inicial=1000.0) -> dict:
    """Simula la estrategia vela a vela. Las velas son [ts, open, high, low, close, vol]."""
    cierres = [v[4] for v in velas]
    saldo, pos, coste = saldo_inicial, None, 0.0
    operaciones = []

    for i in range(1, len(velas)):
        _, _, maximo, minimo, cierre, _ = velas[i]
        if pos:
            salida = None
            if minimo <= pos.stop_loss(sl_pct):        # asumimos lo peor: primero el SL
                salida = (pos.stop_loss(sl_pct), "STOP_LOSS")
            elif maximo >= pos.take_profit(tp_pct):
                salida = (pos.take_profit(tp_pct), "TAKE_PROFIT")
            elif senal_en(cierres, rapida, lenta, i) == VENDER:
                salida = (cierre, "SEÑAL_VENTA")
            if salida:
                ingreso = pos.cantidad * salida[0] * (1 - COMISION)
                saldo += ingreso
                operaciones.append({"motivo": salida[1], "pnl": ingreso - coste})
                pos = None
                continue
        if not pos and senal_en(cierres, rapida, lenta, i) == COMPRAR and saldo >= cantidad_usdt:
            saldo -= cantidad_usdt
            pos = Posicion(cantidad_usdt / cierre * (1 - COMISION), cierre)
            coste = cantidad_usdt

    if pos:  # cerrar al último precio para el informe
        ingreso = pos.cantidad * cierres[-1] * (1 - COMISION)
        saldo += ingreso
        operaciones.append({"motivo": "FIN", "pnl": ingreso - coste})

    ganadoras = [o for o in operaciones if o["pnl"] > 0]
    return {
        "saldo_final": saldo,
        "resultado": saldo - saldo_inicial,
        "operaciones": len(operaciones),
        "ganadoras": len(ganadoras),
        "tasa_acierto": (len(ganadoras) / len(operaciones) * 100) if operaciones else 0.0,
        "detalle": operaciones,
    }


def descargar_velas(par: str, temporalidad: str, total: int) -> list:
    from .exchange import crear_exchange
    ex = crear_exchange("paper")
    ms = ex.parse_timeframe(temporalidad) * 1000
    desde = ex.milliseconds() - total * ms
    velas = []
    while len(velas) < total:
        lote = ex.fetch_ohlcv(par, temporalidad, since=desde, limit=1000)
        if not lote:
            break
        velas += lote
        desde = lote[-1][0] + ms
    return velas[-total:]


def main() -> None:
    p = argparse.ArgumentParser(description="Backtest de la estrategia de cruce de medias")
    p.add_argument("--par", default="BTC/USDT")
    p.add_argument("--temporalidad", default="1h")
    p.add_argument("--velas", type=int, default=1000)
    p.add_argument("--rapida", type=int, default=9)
    p.add_argument("--lenta", type=int, default=21)
    p.add_argument("--cantidad", type=float, default=20)
    p.add_argument("--sl", type=float, default=2.0)
    p.add_argument("--tp", type=float, default=4.0)
    a = p.parse_args()

    print(f"Descargando {a.velas} velas de {a.par} ({a.temporalidad})...")
    velas = descargar_velas(a.par, a.temporalidad, a.velas)
    r = backtest(velas, a.rapida, a.lenta, a.cantidad, a.sl, a.tp)
    print(f"Operaciones:   {r['operaciones']}  (ganadoras {r['ganadoras']}, "
          f"acierto {r['tasa_acierto']:.1f} %)")
    print(f"Resultado:     {r['resultado']:+.2f} USDT")
    print(f"Saldo final:   {r['saldo_final']:.2f} USDT (inicial 1000)")
    print("Recuerda: un buen resultado pasado NO garantiza resultados futuros.")


if __name__ == "__main__":
    main()
