import unittest

from crypto_bot import indicators as ind


class TestIndicators(unittest.TestCase):
    def test_sma(self):
        self.assertEqual(ind.sma([1, 2, 3, 4, 5], 3), [None, None, 2, 3, 4])

    def test_ema_seed_and_step(self):
        out = ind.ema([1, 2, 3, 4], 3)
        self.assertEqual(out[:2], [None, None])
        self.assertAlmostEqual(out[2], 2.0)
        self.assertAlmostEqual(out[3], 4 * 0.5 + 2 * 0.5)

    def test_rsi_extremes(self):
        up = [float(i) for i in range(1, 40)]
        down = list(reversed(up))
        self.assertEqual(ind.rsi(up)[-1], 100.0)
        self.assertEqual(ind.rsi(down)[-1], 0.0)
        flat = [5.0] * 30
        self.assertEqual(ind.rsi(flat)[-1], 50.0)

    def test_rsi_known_value(self):
        # Ejemplo clásico de Wilder / StockCharts: RSI exacto ≈ 70.46 (la tabla de StockCharts muestra 70.53 por redondear las medias)
        closes = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
                  45.89, 46.03, 45.61, 46.28, 46.28]
        self.assertAlmostEqual(ind.rsi(closes)[-1], 70.464, delta=0.01)

    def test_macd_lengths(self):
        closes = [float(i % 7 + i * 0.1) for i in range(100)]
        line, sig, hist = ind.macd(closes)
        self.assertEqual(len(line), 100)
        self.assertIsNone(line[24])
        self.assertIsNotNone(line[25])
        self.assertIsNone(sig[32])
        self.assertIsNotNone(sig[33])
        self.assertAlmostEqual(hist[-1], line[-1] - sig[-1])

    def test_bollinger_flat(self):
        lo, mid, up = ind.bollinger([10.0] * 25)
        self.assertEqual((lo[-1], mid[-1], up[-1]), (10.0, 10.0, 10.0))

    def test_atr_constant_range(self):
        n = 30
        highs, lows, closes = [11.0] * n, [9.0] * n, [10.0] * n
        self.assertAlmostEqual(ind.atr(highs, lows, closes)[-1], 2.0)


if __name__ == "__main__":
    unittest.main()
