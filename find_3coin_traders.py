#!/usr/bin/env python3
"""
find_3coin_traders.py

Find wallets that traded ALL 3 coins with >= $min_vol_usd volume each.
Ignores entry price, ignores whether currently holding or exited.

Usage:
    python3 find_3coin_traders.py <COIN_A> <COIN_B> <COIN_C> [min_vol_usd=100]
"""

import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key={key}"
HELIUS_TXN_URL = "https://api.helius.xyz/v0/addresses/{addr}/transactions?api-key={key}&limit=100&type=SWAP"

def load_api_key():
    key = os.environ.get("HELIUS_API_KEY")
    if key:
        return key
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        for line in open(env_file):
            if line.strip().startswith("HELIUS_API_KEY="):
                return line.split("=",1)[1].strip().strip('"\'')
    sys.exit("HELIUS_API_KEY not set")

def rpc_post(url, method, params):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get_all_holders(mint, rpc_url):
    holders = set()
    cursor = None
    while True:
        params = {"mint": mint, "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        result = rpc_post(rpc_url, "getTokenAccounts", params).get("result", {})
        for acc in result.get("token_accounts", []):
            if float(acc.get("amount", 0)) > 0:
                holders.add(acc["owner"])
        cursor = result.get("cursor")
        if not cursor or not result.get("token_accounts"):
            break
    return holders

def get_sol_price():
    try:
        req = urllib.request.Request(
            "https://api.kraken.com/0/public/Ticker?pair=SOLUSD",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read())
            result = d.get("result", {})
            key = [k for k in result if k != "last"][0]
            return float(result[key]["c"][0])
    except Exception:
        return 90.0

def get_wallet_volume(wallet, api_key, mint, sol_price, max_pages=5):
    """Get total USD volume (buys + sells) for a wallet in a specific token."""
    url = HELIUS_TXN_URL.format(addr=wallet, key=api_key)
    total_sol_volume = 0.0
    before = None
    for _ in range(max_pages):
        page_url = url + (f"&before={before}" if before else "")
        try:
            req = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                txns = json.loads(r.read())
        except Exception:
            break
        if not txns:
            break
        for tx in txns:
            tt = tx.get("tokenTransfers", [])
            nt = tx.get("nativeTransfers", [])
            mints = {t.get("mint","") for t in tt}
            if mint in mints:
                # SOL spent on buys
                sol_out = sum(t.get("amount", 0) for t in nt if t.get("fromUserAccount","") == wallet)
                # SOL received from sells
                sol_in = sum(t.get("amount", 0) for t in nt if t.get("toUserAccount","") == wallet)
                total_sol_volume += (sol_out + sol_in) / 1e9
        before = txns[-1].get("signature") if txns else None
        time.sleep(0.03)
    return total_sol_volume * sol_price

def check_current_holding(wallet, mint, rpc_url):
    params = [wallet, {"mint": mint}, {"encoding": "jsonParsed", "commitment": "confirmed"}]
    try:
        result = rpc_post(rpc_url, "getTokenAccountsByOwner", params).get("result", {})
        for acc in result.get("value", []):
            amount = float(acc.get("account",{}).get("data",{}).get("parsed",{}).get("info",{}).get("tokenAmount",{}).get("uiAmount") or 0)
            if amount > 0:
                return True
    except Exception:
        pass
    return False

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 find_3coin_traders.py <CA_A> <CA_B> <CA_C> [min_vol_usd]")
        sys.exit(1)

    coin_a, coin_b, coin_c = sys.argv[1], sys.argv[2], sys.argv[3]
    min_vol = float(sys.argv[4]) if len(sys.argv) > 4 else 100.0
    names = {coin_a: "SUGEE", coin_b: "E=MC²", coin_c: "ANTS"}

    api_key = load_api_key()
    rpc_url = HELIUS_RPC_URL.format(key=api_key)
    sol_price = get_sol_price()
    print(f"SOL: ${sol_price:.2f} | Min vol per coin: ${min_vol:.0f}", file=sys.stderr)

    # Step 1: Get all current holders of all 3 coins
    print("Step 1: Getting current holders...", file=sys.stderr)
    holders_a = get_all_holders(coin_a, rpc_url)
    holders_b = get_all_holders(coin_b, rpc_url)
    holders_c = get_all_holders(coin_c, rpc_url)
    print(f"  {names[coin_a]}: {len(holders_a)} | {names[coin_b]}: {len(holders_b)} | {names[coin_c]}: {len(holders_c)}", file=sys.stderr)

    # Step 2: Build candidate universe
    # Start with coins with fewer holders, check tx history for the rest
    # Candidates = union of smallest two coin holders (can extend later)
    # Strategy: anyone currently holding ≥2 coins is a strong candidate
    # Also: anyone holding coin_a or coin_c (smallest sets) is a candidate for cross-check
    all_a_c = holders_a | holders_c  # SUGEE + ANTS (smaller pools)
    print(f"  SUGEE ∪ ANTS: {len(all_a_c)} unique wallets to check", file=sys.stderr)

    # Step 3: For each candidate, check volume in all 3 coins
    print(f"Step 2: Checking $100+ volume across all 3 coins for {len(all_a_c)} wallets...", file=sys.stderr)
    qualified = {}

    def check_wallet(wallet):
        vol_a = get_wallet_volume(wallet, api_key, coin_a, sol_price)
        if vol_a < min_vol:
            return None  # Skip if no meaningful SUGEE vol
        vol_b = get_wallet_volume(wallet, api_key, coin_b, sol_price)
        vol_c = get_wallet_volume(wallet, api_key, coin_c, sol_price)
        if vol_b >= min_vol and vol_c >= min_vol:
            holds = {
                coin_a: wallet in holders_a,
                coin_b: wallet in holders_b,
                coin_c: wallet in holders_c,
            }
            return {"vol_a": vol_a, "vol_b": vol_b, "vol_c": vol_c, "holds": holds}
        return None

    completed = 0
    total = len(all_a_c)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(check_wallet, w): w for w in all_a_c}
        for future in as_completed(futures):
            wallet = futures[future]
            result = future.result()
            if result:
                qualified[wallet] = result
            completed += 1
            if completed % 50 == 0:
                print(f"  {completed}/{total} checked | {len(qualified)} qualified so far...", file=sys.stderr)

    # Print results
    print(f"\n{'='*65}")
    print("WALLETS with $100+ volume in ALL 3 COINS")
    print(f"  {names[coin_a]} | {names[coin_b]} | {names[coin_c]}")
    print(f"{'='*65}\n")

    if not qualified:
        print("None found.")
        return

    for wallet, data in sorted(qualified.items(), key=lambda x: -(x[1]["vol_a"]+x[1]["vol_b"]+x[1]["vol_c"])):
        total_vol = data["vol_a"] + data["vol_b"] + data["vol_c"]
        h = data["holds"]
        status_a = "✅ holds" if h[coin_a] else "📤 exited"
        status_b = "✅ holds" if h[coin_b] else "📤 exited"
        status_c = "✅ holds" if h[coin_c] else "📤 exited"
        print(f"🎯 {wallet}")
        print(f"   {names[coin_a]}: ${data['vol_a']:,.0f} [{status_a}]")
        print(f"   {names[coin_b]}: ${data['vol_b']:,.0f} [{status_b}]")
        print(f"   {names[coin_c]}: ${data['vol_c']:,.0f} [{status_c}]")
        print(f"   Total vol: ${total_vol:,.0f}")
        print()

if __name__ == "__main__":
    main()
