#!/usr/bin/env python3
"""sol-smart-money: wallet_history.py

Pull buy/sell history for a specific wallet + token pair using Helius.
Shows when the wallet entered, how many times they bought/sold, and net position.

Usage:
    python wallet_history.py <WALLET_ADDRESS> <TOKEN_CA>
    python wallet_history.py <WALLET_ADDRESS> <TOKEN_CA> --json
    python wallet_history.py <WALLET_ADDRESS> <TOKEN_CA> --limit 50
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key={key}"
HELIUS_API_URL = "https://api.helius.xyz/v0/addresses/{address}/transactions?api-key={key}"


def load_api_key() -> str:
    key = os.environ.get("HELIUS_API_KEY")
    if key:
        return key
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip().startswith("HELIUS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("Error: HELIUS_API_KEY not set.", file=sys.stderr)
    sys.exit(1)


def rpc_call(url: str, method: str, params: Any) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def get_token_decimals(rpc_url: str, mint: str) -> int:
    result = rpc_call(rpc_url, "getTokenSupply", [mint])
    return int(result["result"]["value"]["decimals"])


def fetch_transactions(address: str, api_key: str, mint: str, limit: int = 100) -> list[dict]:
    """Fetch parsed transactions for a wallet, filtered to a specific token mint."""
    txs = []
    before = None

    while len(txs) < limit:
        url = HELIUS_API_URL.format(address=address, key=api_key)
        url += "&limit=100&type=SWAP"
        if before:
            url += f"&before={before}"

        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                batch = json.loads(r.read())
        except Exception as e:
            print(f"Warning: fetch error — {e}", file=sys.stderr)
            break

        if not batch:
            break

        for tx in batch:
            if is_relevant(tx, address, mint):
                txs.append(tx)

        if len(batch) < 100:
            break

        before = batch[-1]["signature"]
        time.sleep(0.2)  # rate limit respect

        if len(txs) >= limit:
            break

    return txs[:limit]


def is_relevant(tx: dict, wallet: str, mint: str) -> bool:
    """Check if a transaction involves the wallet and the target token."""
    token_transfers = tx.get("tokenTransfers", [])
    for t in token_transfers:
        if t.get("mint") == mint:
            if t.get("fromUserAccount") == wallet or t.get("toUserAccount") == wallet:
                return True
    return False


def parse_transfers(tx: dict, wallet: str, mint: str, decimals: int) -> list[dict]:
    """Extract buy/sell events from a transaction."""
    events = []
    ts = tx.get("timestamp", 0)
    sig = tx.get("signature", "")

    for t in tx.get("tokenTransfers", []):
        if t.get("mint") != mint:
            continue
        raw = int(t.get("tokenAmount", 0))
        amount = raw / (10 ** decimals)
        if amount == 0:
            continue

        if t.get("toUserAccount") == wallet:
            events.append({"type": "BUY", "amount": amount, "timestamp": ts, "sig": sig})
        elif t.get("fromUserAccount") == wallet:
            events.append({"type": "SELL", "amount": amount, "timestamp": ts, "sig": sig})

    return events


def format_ts(ts: int) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts, datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")


def analyze_history(wallet: str, mint: str, limit: int = 100, as_json: bool = False) -> dict:
    api_key = load_api_key()
    rpc_url = HELIUS_RPC_URL.format(key=api_key)

    decimals = get_token_decimals(rpc_url, mint)
    raw_txs = fetch_transactions(wallet, api_key, mint, limit=limit)

    events = []
    for tx in raw_txs:
        events.extend(parse_transfers(tx, wallet, mint, decimals))

    events.sort(key=lambda x: x["timestamp"])

    total_bought = sum(e["amount"] for e in events if e["type"] == "BUY")
    total_sold = sum(e["amount"] for e in events if e["type"] == "SELL")
    net_position = total_bought - total_sold
    buy_count = sum(1 for e in events if e["type"] == "BUY")
    sell_count = sum(1 for e in events if e["type"] == "SELL")
    first_buy = next((e for e in events if e["type"] == "BUY"), None)

    result = {
        "wallet": wallet,
        "mint": mint,
        "first_buy_ts": first_buy["timestamp"] if first_buy else None,
        "first_buy_time": format_ts(first_buy["timestamp"]) if first_buy else None,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "total_bought": round(total_bought, 2),
        "total_sold": round(total_sold, 2),
        "net_position": round(net_position, 2),
        "events": events,
    }

    if as_json:
        return result

    w_short = wallet[:6] + "..." + wallet[-4:]
    m_short = mint[:6] + "..." + mint[-4:]
    print(f"\nWallet: {w_short} | Token: {m_short}")
    print(f"First buy:    {result['first_buy_time'] or 'N/A'}")
    print(f"Buys/Sells:   {buy_count} buys / {sell_count} sells")
    print(f"Total bought: {total_bought:,.2f}")
    print(f"Total sold:   {total_sold:,.2f}")
    print(f"Net position: {net_position:,.2f}")
    if events:
        print(f"\nTransaction log ({len(events)} events):")
        for e in events:
            arrow = "↑ BUY " if e["type"] == "BUY" else "↓ SELL"
            print(f"  {arrow}  {e['amount']:>14,.2f}  {format_ts(e['timestamp'])}")
    print()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull buy/sell history for a wallet + token pair.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wallet_history.py <WALLET> <CA>
  python wallet_history.py <WALLET> <CA> --limit 200
  python wallet_history.py <WALLET> <CA> --json
        """,
    )
    parser.add_argument("wallet", help="Solana wallet address")
    parser.add_argument("mint", help="Token mint (CA)")
    parser.add_argument("--limit", type=int, default=100, help="Max transactions to scan (default: 100)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    result = analyze_history(wallet=args.wallet, mint=args.mint, limit=args.limit, as_json=args.as_json)
    if args.as_json:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        print()


if __name__ == "__main__":
    main()
