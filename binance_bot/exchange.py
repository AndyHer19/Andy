"""Conexión con Binance mediante ccxt.

- BrokerPaper: precios reales, órdenes simuladas en local (comisión 0,1 %).
- BrokerBinance: órdenes reales en testnet o en la cuenta real.
"""
import ccxt

COMISION = 0.001  # 0,1 % comisión estándar de Binance spot


def crear_exchange(modo: str, api_key: str = "", api_secret: str = ""):
    ex = ccxt.binance({
        "apiKey": api_key or None,
        "secret": api_secret or None,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    if modo == "testnet":
        ex.set_sandbox_mode(True)
    return ex


class BrokerBase:
    def __init__(self, exchange, par: str):
        self.ex = exchange
        self.par = par
        self.base, self.quote = par.split("/")

    def velas(self, temporalidad: str, limite: int = 100) -> list:
        """Lista de [timestamp, apertura, máximo, mínimo, cierre, volumen]."""
        return self.ex.fetch_ohlcv(self.par, temporalidad, limit=limite)

    def precio(self) -> float:
        return float(self.ex.fetch_ticker(self.par)["last"])

    def comprar(self, usdt: float, precio: float) -> dict:
        raise NotImplementedError

    def vender(self, cantidad: float, precio: float) -> dict:
        raise NotImplementedError

    def saldo_quote(self) -> float:
        raise NotImplementedError


class BrokerPaper(BrokerBase):
    """Simula órdenes con un saldo ficticio. No necesita claves de API."""

    def __init__(self, exchange, par: str, saldo_inicial: float):
        super().__init__(exchange, par)
        self.saldo = {self.quote: saldo_inicial, self.base: 0.0}

    def saldo_quote(self) -> float:
        return self.saldo[self.quote]

    def comprar(self, usdt: float, precio: float) -> dict:
        if usdt > self.saldo[self.quote]:
            raise ValueError("Saldo simulado insuficiente")
        cantidad = usdt / precio * (1 - COMISION)
        self.saldo[self.quote] -= usdt
        self.saldo[self.base] += cantidad
        return {"cantidad": cantidad, "precio": precio, "coste": usdt}

    def vender(self, cantidad: float, precio: float) -> dict:
        cantidad = min(cantidad, self.saldo[self.base])
        ingreso = cantidad * precio * (1 - COMISION)
        self.saldo[self.base] -= cantidad
        self.saldo[self.quote] += ingreso
        return {"cantidad": cantidad, "precio": precio, "ingreso": ingreso}


class BrokerBinance(BrokerBase):
    """Envía órdenes de mercado reales (testnet o live)."""

    def __init__(self, exchange, par: str):
        super().__init__(exchange, par)
        self.ex.load_markets()
        self.mercado = self.ex.market(par)

    def saldo_quote(self) -> float:
        return float(self.ex.fetch_balance()["free"].get(self.quote, 0.0))

    def _saldo_base(self) -> float:
        return float(self.ex.fetch_balance()["free"].get(self.base, 0.0))

    def _comprobar_minimo(self, cantidad: float, precio: float) -> None:
        limites = self.mercado.get("limits", {})
        min_cant = (limites.get("amount") or {}).get("min") or 0
        min_coste = (limites.get("cost") or {}).get("min") or 0
        if cantidad < min_cant or cantidad * precio < min_coste:
            raise ValueError(
                f"Orden demasiado pequeña: mínimo {min_cant} {self.base} / {min_coste} {self.quote}"
            )

    def comprar(self, usdt: float, precio: float) -> dict:
        cantidad = float(self.ex.amount_to_precision(self.par, usdt / precio))
        self._comprobar_minimo(cantidad, precio)
        orden = self.ex.create_market_buy_order(self.par, cantidad)
        llenado = float(orden.get("filled") or cantidad)
        # La comisión se cobra en el activo comprado: descontarla para no vender de más.
        comision = sum(float(f.get("cost") or 0) for f in orden.get("fees") or []
                       if f.get("currency") == self.base)
        return {
            "cantidad": llenado - comision,
            "precio": float(orden.get("average") or precio),
            "coste": float(orden.get("cost") or llenado * precio),
            "id": orden.get("id"),
        }

    def vender(self, cantidad: float, precio: float) -> dict:
        cantidad = min(cantidad, self._saldo_base())
        cantidad = float(self.ex.amount_to_precision(self.par, cantidad))
        self._comprobar_minimo(cantidad, precio)
        orden = self.ex.create_market_sell_order(self.par, cantidad)
        comision = sum(float(f.get("cost") or 0) for f in orden.get("fees") or []
                       if f.get("currency") == self.quote)
        return {
            "cantidad": float(orden.get("filled") or cantidad),
            "precio": float(orden.get("average") or precio),
            "ingreso": float(orden.get("cost") or cantidad * precio) - comision,
            "id": orden.get("id"),
        }
