import math
import tempfile
import unittest
from pathlib import Path

from crypto_bot.bot import normalize_symbol
from crypto_bot.market import Candles
from crypto_bot.messages import format_analysis, format_summary
from crypto_bot.signals import BUY, NEUTRAL, SELL, analyze
from crypto_bot.state import State


def make_candles(closes, volumes=None, interval="1h"):
    n = len(closes)
    return Candles("TESTUSDT", interval, list(range(n)), closes[:],
                   [c * 1.01 for c in closes], [c * 0.99 for c in closes], closes[:],
                   volumes or [100.0] * n)


class TestSignals(unittest.TestCase):
    def test_capitulation_after_uptrend_is_buy(self):
        # Larga tendencia alcista y luego una caída brusca -> sobreventa en tendencia alcista
        closes = [100 + i * 0.5 for i in range(250)] + [225 - i * 4 for i in range(12)]
        a = analyze(make_candles(closes))
        self.assertEqual(a.signal, BUY, a)
        self.assertLess(a.rsi, 30)
        stop, target = a.levels()
        self.assertLess(stop, a.price)
        self.assertGreater(target, a.price)

    def test_blowoff_after_downtrend_is_sell(self):
        closes = [300 - i * 0.5 for i in range(250)] + [175 + i * 4 for i in range(12)]
        a = analyze(make_candles(closes))
        self.assertEqual(a.signal, SELL, a)
        self.assertGreater(a.rsi, 70)
        stop, target = a.levels()
        self.assertGreater(stop, a.price)
        self.assertLess(target, a.price)

    def test_sideways_is_neutral(self):
        closes = [100 + math.sin(i / 3) for i in range(260)]
        a = analyze(make_candles(closes))
        self.assertEqual(a.signal, NEUTRAL, a)
        self.assertIsNone(a.levels())

    def test_too_few_candles(self):
        with self.assertRaises(ValueError):
            analyze(make_candles([1.0] * 10))

    def test_works_without_200_candles(self):
        closes = [100 + i * 0.5 for i in range(70)] + [135 - i * 4 for i in range(10)]
        a = analyze(make_candles(closes))
        self.assertIsNone(a.ema200)
        self.assertIsNotNone(a.ema50)

    def test_messages_render(self):
        closes = [100 + i * 0.5 for i in range(250)] + [225 - i * 4 for i in range(12)]
        a = analyze(make_candles(closes))
        text = format_analysis(a)
        self.assertIn("POSIBLE COMPRA", text)
        self.assertIn("No es consejo financiero", text)
        self.assertIn("TESTUSDT", format_summary([a], ["X: error"]))


class TestState(unittest.TestCase):
    def test_dedupe_and_cooldown(self):
        with tempfile.TemporaryDirectory() as d:
            st = State(str(Path(d) / "s.json"), ["BTCUSDT"])
            self.assertTrue(st.should_notify("BTCUSDT", BUY, 12, now=0))
            self.assertFalse(st.should_notify("BTCUSDT", BUY, 12, now=3600))
            self.assertTrue(st.should_notify("BTCUSDT", SELL, 12, now=7200))
            self.assertFalse(st.should_notify("BTCUSDT", NEUTRAL, 12, now=8000))
            # Tras volver a neutral, una nueva compra sí avisa aunque no pase el cooldown
            self.assertTrue(st.should_notify("BTCUSDT", BUY, 12, now=9000))
            # Pasado el cooldown, la misma señal se repite
            self.assertTrue(st.should_notify("BTCUSDT", BUY, 12, now=9000 + 13 * 3600))
            # Persistencia
            st2 = State(str(Path(d) / "s.json"), [])
            self.assertEqual(st2.data["last"]["BTCUSDT"]["signal"], BUY)
            self.assertEqual(st2.symbols, ["BTCUSDT"])

    def test_add_remove(self):
        with tempfile.TemporaryDirectory() as d:
            st = State(str(Path(d) / "s.json"), ["BTCUSDT"])
            self.assertTrue(st.add_symbol("ETHUSDT"))
            self.assertFalse(st.add_symbol("ETHUSDT"))
            self.assertTrue(st.remove_symbol("BTCUSDT"))
            self.assertEqual(st.symbols, ["ETHUSDT"])


class TestNormalize(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_symbol("btc"), "BTCUSDT")
        self.assertEqual(normalize_symbol("sol"), "SOLUSDT")
        self.assertEqual(normalize_symbol("eth/usdt"), "ETHUSDT")
        self.assertEqual(normalize_symbol("ETHBTC"), "ETHBTC")
        self.assertEqual(normalize_symbol("pepe"), "PEPEUSDT")


if __name__ == "__main__":
    unittest.main()
