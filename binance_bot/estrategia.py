"""Estrategia de cruce de medias móviles simples (SMA).

- COMPRAR cuando la media rápida cruza POR ENCIMA de la lenta.
- VENDER  cuando la media rápida cruza POR DEBAJO de la lenta.
"""
from typing import Optional, Sequence

COMPRAR = "COMPRAR"
VENDER = "VENDER"


def media_movil(valores: Sequence[float], periodo: int) -> list:
    """Devuelve la media móvil simple; None donde aún no hay datos suficientes."""
    resultado = [None] * len(valores)
    suma = 0.0
    for i, v in enumerate(valores):
        suma += v
        if i >= periodo:
            suma -= valores[i - periodo]
        if i >= periodo - 1:
            resultado[i] = suma / periodo
    return resultado


def senal_en(cierres: Sequence[float], rapida: int, lenta: int, i: int) -> Optional[str]:
    """Señal en la vela i usando solo datos hasta i (sin mirar al futuro)."""
    if i < lenta:
        return None
    ventana = cierres[max(0, i - lenta - 1): i + 1]
    r = media_movil(ventana, rapida)
    l = media_movil(ventana, lenta)
    r_ant, r_act, l_ant, l_act = r[-2], r[-1], l[-2], l[-1]
    if None in (r_ant, r_act, l_ant, l_act):
        return None
    if r_ant <= l_ant and r_act > l_act:
        return COMPRAR
    if r_ant >= l_ant and r_act < l_act:
        return VENDER
    return None


def calcular_senal(cierres: Sequence[float], rapida: int, lenta: int) -> Optional[str]:
    """Señal sobre la última vela de la serie."""
    return senal_en(cierres, rapida, lenta, len(cierres) - 1)
