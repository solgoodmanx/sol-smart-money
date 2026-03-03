"""Tests for wallet_history.py"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from wallet_history import format_ts, is_relevant, parse_transfers


class TestIsRelevant(unittest.TestCase):
    def _tx(self, transfers):
        return {"tokenTransfers": transfers}

    def test_buy_is_relevant(self):
        tx = self._tx([{"mint": "MINT_A", "toUserAccount": "WALLET_X", "fromUserAccount": "OTHER"}])
        self.assertTrue(is_relevant(tx, "WALLET_X", "MINT_A"))

    def test_sell_is_relevant(self):
        tx = self._tx([{"mint": "MINT_A", "fromUserAccount": "WALLET_X", "toUserAccount": "OTHER"}])
        self.assertTrue(is_relevant(tx, "WALLET_X", "MINT_A"))

    def test_different_mint_not_relevant(self):
        tx = self._tx([{"mint": "MINT_B", "toUserAccount": "WALLET_X", "fromUserAccount": "OTHER"}])
        self.assertFalse(is_relevant(tx, "WALLET_X", "MINT_A"))

    def test_different_wallet_not_relevant(self):
        tx = self._tx([{"mint": "MINT_A", "toUserAccount": "WALLET_Y", "fromUserAccount": "OTHER"}])
        self.assertFalse(is_relevant(tx, "WALLET_X", "MINT_A"))

    def test_empty_transfers(self):
        self.assertFalse(is_relevant({"tokenTransfers": []}, "WALLET_X", "MINT_A"))


class TestParseTransfers(unittest.TestCase):
    def test_buy_detected(self):
        tx = {
            "timestamp": 1700000000,
            "signature": "SIG1",
            "tokenTransfers": [
                {"mint": "MINT_A", "toUserAccount": "WALLET_X", "fromUserAccount": "OTHER", "tokenAmount": 1_000_000}
            ],
        }
        events = parse_transfers(tx, "WALLET_X", "MINT_A", decimals=6)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "BUY")
        self.assertAlmostEqual(events[0]["amount"], 1.0)

    def test_sell_detected(self):
        tx = {
            "timestamp": 1700000000,
            "signature": "SIG2",
            "tokenTransfers": [
                {"mint": "MINT_A", "fromUserAccount": "WALLET_X", "toUserAccount": "OTHER", "tokenAmount": 500_000}
            ],
        }
        events = parse_transfers(tx, "WALLET_X", "MINT_A", decimals=6)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "SELL")
        self.assertAlmostEqual(events[0]["amount"], 0.5)

    def test_zero_amount_excluded(self):
        tx = {
            "timestamp": 1700000000,
            "signature": "SIG3",
            "tokenTransfers": [
                {"mint": "MINT_A", "toUserAccount": "WALLET_X", "fromUserAccount": "OTHER", "tokenAmount": 0}
            ],
        }
        events = parse_transfers(tx, "WALLET_X", "MINT_A", decimals=6)
        self.assertEqual(len(events), 0)

    def test_wrong_mint_excluded(self):
        tx = {
            "timestamp": 1700000000,
            "signature": "SIG4",
            "tokenTransfers": [
                {"mint": "MINT_B", "toUserAccount": "WALLET_X", "fromUserAccount": "OTHER", "tokenAmount": 1_000_000}
            ],
        }
        events = parse_transfers(tx, "WALLET_X", "MINT_A", decimals=6)
        self.assertEqual(len(events), 0)


class TestFormatTs(unittest.TestCase):
    def test_known_timestamp(self):
        result = format_ts(0)
        self.assertIn("1970", result)

    def test_returns_utc_string(self):
        result = format_ts(1700000000)
        self.assertIn("UTC", result)


if __name__ == "__main__":
    unittest.main()
