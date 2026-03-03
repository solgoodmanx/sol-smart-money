#!/usr/bin/env python3
"""sol-smart-money: check_holders.py

Instantly cross-references all holders of a Solana token against your
private tracked wallet list using Helius getTokenAccounts.

Architecture: one inbound call to fetch all holders → set intersection.
Scales regardless of wallet list size.

Usage:
    python check_holders.py <CA>
    python check_holders.py <CA> --wallets /path/to/wallets.json
    python check_holders.py <CA> --json

Requirements:
    HELIUS_API_KEY env var (or set in .env)
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_WALLETS_PATH = Path(__file__).parent / "wallets.json"
HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key={key}"


def load_api_key() -> str:
    """Load Helius API key from env or .env file."""
    key = os.environ.get("HELIUS_API_KEY")
    if key:
        return key
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("HELIUS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("Error: HELIUS_API_KEY not set. Copy .env.example to .env and add your key.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helius helpers
# ---------------------------------------------------------------------------

def rpc_call(url: str, method: str, params: Any) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_token_info(url: str, ca: str) -> tuple[int, float]:
    """Return (decimals, total_supply_ui)."""
    result = rpc_call(url, "getTokenSupply", [ca])
    info = result["result"]["value"]
    return int(info["decimals"]), float(info["uiAmount"] or 0)


def get_all_holders(url: str, ca: str, decimals: int) -> dict[str, float]:
    """Fetch all token holders via Helius getTokenAccounts. Returns {owner_lower: ui_amount}."""
    holders: dict[str, float] = {}
    cursor = None
    page = 0

    while True:
        params: dict[str, Any] = {"mint": ca, "limit": 1000}
        if cursor:
            params["cursor"] = cursor

        data = rpc_call(url, "getTokenAccounts", params)
        result = data.get("result") or {}
        accounts = result.get("token_accounts") or []

        if not accounts:
            break

        for acct in accounts:
            raw = int(acct.get("amount", 0))
            if raw > 0:
                holders[acct["owner"].lower()] = raw / (10 ** decimals)

        cursor = result.get("cursor")
        page += 1
        if not cursor or page > 50:  # safety cap
            break

    return holders


# ---------------------------------------------------------------------------
# Wallet list
# ---------------------------------------------------------------------------

def load_wallets(path: Path) -> dict[str, str]:
    """Load wallet list. Returns {address_lower: name}."""
    if not path.exists():
        print(
            f"Error: wallet list not found at {path}\n"
            "Copy wallets.example.json to wallets.json and add your tracked wallets.",
            file=sys.stderr,
        )
        sys.exit(1)

    data = json.loads(path.read_text())
    result: dict[str, str] = {}
    for entry in data:
        chain = entry.get("chain", "solana").lower()
        if chain != "solana":
            continue
        addr = entry.get("address", "").strip()
        name = entry.get("name", addr[:8])
        if addr:
            result[addr.lower()] = name
    return result


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def check_holders(
    ca: str,
    wallets_path: Path = DEFAULT_WALLETS_PATH,
    as_json: bool = False,
) -> dict:
    api_key = load_api_key()
    url = HELIUS_RPC_URL.format(key=api_key)
    ca = ca.strip()

    decimals, total_supply = get_token_info(url, ca)
    all_holders = get_all_holders(url, ca, decimals)
    tracked = load_wallets(wallets_path)

    matches = []
    for addr, amount in all_holders.items():
        if addr in tracked:
            pct = (amount / total_supply * 100) if total_supply > 0 else 0.0
            matches.append({
                "name": tracked[addr],
                "address": addr,
                "amount": amount,
                "pct_supply": round(pct, 4),
            })

    matches.sort(key=lambda x: -x["amount"])

    output = {
        "ca": ca,
        "total_holders": len(all_holders),
        "total_supply": total_supply,
        "tracked_holding": len(matches),
        "holders": matches,
    }

    if as_json:
        return output

    # Human-readable output
    ca_short = ca[:6] + "..." + ca[-4:]
    print(f"\n{ca_short} — {len(all_holders):,} total holders")
    if not matches:
        print("  No tracked wallets holding.")
    else:
        print(f"  {len(matches)} tracked wallet(s) holding:\n")
        print(f"  {'Wallet':<28} {'Amount':>16}   {'% Supply':>8}")
        print(f"  {'-'*28}   {'-'*16}   {'-'*8}")
        for h in matches:
            amt_str = f"{h['amount']:,.2f}"
            pct_str = f"{h['pct_supply']:.2f}%"
            print(f"  {h['name']:<28} {amt_str:>16}   {pct_str:>8}")
    print()

    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-reference a Solana token's holders against your tracked wallet list.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_holders.py GMD16hpoKqfpXpPTWoymvzjddsruQsdqPu8T28ZKpump
  python check_holders.py <CA> --wallets ~/my-wallets.json
  python check_holders.py <CA> --json
        """,
    )
    parser.add_argument("ca", help="Solana token contract address (mint)")
    parser.add_argument(
        "--wallets",
        type=Path,
        default=DEFAULT_WALLETS_PATH,
        help="Path to wallets.json (default: ./wallets.json)",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output raw JSON instead of formatted table",
    )
    args = parser.parse_args()

    result = check_holders(ca=args.ca, wallets_path=args.wallets, as_json=args.as_json)
    if args.as_json:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        print()


if __name__ == "__main__":
    main()
