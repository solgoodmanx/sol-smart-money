"""Tests for check_holders.py"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from check_holders import get_all_holders, get_token_info, load_wallets, rpc_call


# ---------------------------------------------------------------------------
# rpc_call
# ---------------------------------------------------------------------------

class TestRpcCall(unittest.TestCase):
    def test_returns_parsed_json(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"result": {"value": 42}}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = rpc_call("http://fake-url", "getTestMethod", ["param"])
        self.assertEqual(result["result"]["value"], 42)


# ---------------------------------------------------------------------------
# get_token_info
# ---------------------------------------------------------------------------

class TestGetTokenInfo(unittest.TestCase):
    def _mock_supply_response(self, decimals: int, ui_amount: float):
        mock_response = MagicMock()
        payload = {
            "result": {
                "value": {
                    "decimals": decimals,
                    "uiAmount": ui_amount,
                    "amount": str(int(ui_amount * 10 ** decimals)),
                }
            }
        }
        mock_response.read.return_value = json.dumps(payload).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    def test_decimals_and_supply(self):
        with patch("urllib.request.urlopen", return_value=self._mock_supply_response(6, 1_000_000.0)):
            decimals, supply = get_token_info("http://fake", "FAKE_MINT")
        self.assertEqual(decimals, 6)
        self.assertAlmostEqual(supply, 1_000_000.0)

    def test_zero_supply(self):
        with patch("urllib.request.urlopen", return_value=self._mock_supply_response(6, 0.0)):
            decimals, supply = get_token_info("http://fake", "FAKE_MINT")
        self.assertEqual(supply, 0.0)


# ---------------------------------------------------------------------------
# get_all_holders
# ---------------------------------------------------------------------------

class TestGetAllHolders(unittest.TestCase):
    def _mock_holders_response(self, accounts: list, cursor: str | None = None):
        mock_response = MagicMock()
        payload = {
            "result": {
                "token_accounts": accounts,
                "cursor": cursor,
            }
        }
        mock_response.read.return_value = json.dumps(payload).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    def test_single_page_holders(self):
        accounts = [
            {"owner": "WALLET_A", "amount": "1000000"},
            {"owner": "WALLET_B", "amount": "500000"},
        ]
        with patch("urllib.request.urlopen", return_value=self._mock_holders_response(accounts)):
            holders = get_all_holders("http://fake", "FAKE_MINT", decimals=6)
        self.assertEqual(holders["wallet_a"], 1.0)
        self.assertEqual(holders["wallet_b"], 0.5)

    def test_zero_amount_excluded(self):
        accounts = [
            {"owner": "WALLET_A", "amount": "0"},
            {"owner": "WALLET_B", "amount": "1000000"},
        ]
        with patch("urllib.request.urlopen", return_value=self._mock_holders_response(accounts)):
            holders = get_all_holders("http://fake", "FAKE_MINT", decimals=6)
        self.assertNotIn("wallet_a", holders)
        self.assertIn("wallet_b", holders)

    def test_owner_lowercased(self):
        accounts = [{"owner": "UPPERCASE_WALLET", "amount": "1000000"}]
        with patch("urllib.request.urlopen", return_value=self._mock_holders_response(accounts)):
            holders = get_all_holders("http://fake", "FAKE_MINT", decimals=6)
        self.assertIn("uppercase_wallet", holders)
        self.assertNotIn("UPPERCASE_WALLET", holders)


# ---------------------------------------------------------------------------
# load_wallets
# ---------------------------------------------------------------------------

class TestLoadWallets(unittest.TestCase):
    def test_loads_solana_wallets(self):
        data = [
            {"address": "WalletAAA", "name": "Alice", "chain": "solana"},
            {"address": "WalletBBB", "name": "Bob", "chain": "solana"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)
        wallets = load_wallets(path)
        self.assertIn("walletaaa", wallets)
        self.assertEqual(wallets["walletaaa"], "Alice")

    def test_excludes_non_solana(self):
        data = [
            {"address": "SolWallet", "name": "SOL", "chain": "solana"},
            {"address": "EvmWallet", "name": "EVM", "chain": "ethereum"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)
        wallets = load_wallets(path)
        self.assertIn("solwallet", wallets)
        self.assertNotIn("evmwallet", wallets)

    def test_address_lowercased(self):
        data = [{"address": "UPPER_WALLET", "name": "Test", "chain": "solana"}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = Path(f.name)
        wallets = load_wallets(path)
        self.assertIn("upper_wallet", wallets)

    def test_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            load_wallets(Path("/nonexistent/wallets.json"))


if __name__ == "__main__":
    unittest.main()
