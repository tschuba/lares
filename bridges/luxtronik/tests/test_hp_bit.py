import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# paho/luxtronik sind für hp_bit nicht nötig
for _m in ("paho", "paho.mqtt", "paho.mqtt.client", "luxtronik"):
    sys.modules.setdefault(_m, MagicMock())
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from luxtronik2mqtt import hp_bit  # noqa: E402


def lux_with(raw):
    return SimpleNamespace(inputs={"heatpump_status": SimpleNamespace(raw=raw)})


class HpBitTest(unittest.TestCase):
    def bits(self, raw):
        return [hp_bit(lux_with(raw), b) for b in range(5)]

    def test_idle(self):
        self.assertEqual(self.bits(0), [0, 0, 0, 0, 0])

    def test_only_zwe1_does_not_trigger_compressor(self):
        self.assertEqual(self.bits(4), [0, 0, 1, 0, 0])

    def test_compressor_and_heater(self):
        self.assertEqual(self.bits(5), [1, 0, 1, 0, 0])

    def test_all(self):
        self.assertEqual(self.bits(31), [1, 1, 1, 1, 1])

    def test_missing_or_non_int(self):
        self.assertEqual(self.bits(None), [0] * 5)
        self.assertEqual(hp_bit(SimpleNamespace(inputs={}), 0), 0)


if __name__ == "__main__":
    unittest.main()
