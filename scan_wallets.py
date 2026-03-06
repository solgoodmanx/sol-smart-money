#!/usr/bin/env python3
"""
scan_wallets.py - Scan all tracked wallets for current token holdings,
aggregate by token, find tokens held by 6+ wallets.
Then filter by token age using DexScreener.
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key={key}"
WALLETS_PATH = Path(__file__).parent.parent / "life/areas/projects/wallet-tracker/wallets.json"
MIN_WALLETS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
MAX_AGE_HOURS = int(sys.argv[2]) if len(sys.argv) > 2 else 72

def load_api_key():
    key = os.environ.get("HELIUS_API_KEY")
    if key:
        return key
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip().startswith("HELIUS_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"\'')
    sys.exit("HELIUS_API_KEY not set")

def get_token_accounts(wallet_addr, rpc_url):
    """Get all token accounts for a wallet."""
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_addr,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed", "commitment": "confirmed"}
        ]
    }).encode()
    req = urllib.request.Request(rpc_url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            accounts = result.get("result", {}).get("value", [])
            holdings = {}
            for acc in accounts:
                info = acc.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                mint = info.get("mint", "")
                amount = float(info.get("tokenAmount", {}).get("uiAmount") or 0)
                if mint and amount > 0:
                    holdings[mint] = amount
            return holdings
    except Exception:
        return {}

def check_dexscreener_age(ca_list):
    """Check token ages via DexScreener. Returns {ca: age_hours, ...}"""
    results = {}
    # DexScreener allows up to 30 CAs per request
    chunk_size = 30
    now = time.time() * 1000
    for i in range(0, len(ca_list), chunk_size):
        chunk = ca_list[i:i+chunk_size]
        url = f"https://api.dexscreener.com/tokens/v1/solana/{','.join(chunk)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
                pairs = data if isinstance(data, list) else data.get("pairs", [])
                seen = set()
                for p in pairs:
                    ca = p.get("baseToken", {}).get("address", "")
                    created = p.get("pairCreatedAt", 0)
                    if ca and ca not in seen and created:
                        age_h = (now - created) / 3600000
                        results[ca] = {
                            "age_h": age_h,
                            "symbol": p.get("baseToken", {}).get("symbol", "?"),
                            "vol24": p.get("volume", {}).get("h24", 0),
                            "mcap": p.get("marketCap", 0),
                        }
                        seen.add(ca)
        except Exception:
            pass
        time.sleep(0.2)
    return results

def main():
    api_key = load_api_key()
    rpc_url = HELIUS_RPC_URL.format(key=api_key)

    wallets = json.loads(WALLETS_PATH.read_text())
    print(f"Scanning {len(wallets)} wallets...", file=sys.stderr)

    # token -> list of wallet names holding it
    token_holders = defaultdict(list)

    def scan_wallet(w):
        holdings = get_token_accounts(w["address"], rpc_url)
        return w["name"], holdings

    completed = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(scan_wallet, w): w for w in wallets}
        for future in as_completed(futures):
            name, holdings = future.result()
            for mint, amount in holdings.items():
                token_holders[mint].append({"name": name, "amount": amount})
            completed += 1
            if completed % 100 == 0:
                print(f"  {completed}/{len(wallets)} wallets scanned...", file=sys.stderr)

    print(f"Done. {len(token_holders)} unique tokens found across all wallets.", file=sys.stderr)

    # Find tokens with 6+ tracked wallets
    hot_tokens = {mint: holders for mint, holders in token_holders.items() if len(holders) >= MIN_WALLETS}
    print(f"{len(hot_tokens)} tokens held by {MIN_WALLETS}+ tracked wallets", file=sys.stderr)

    if not hot_tokens:
        print(f"\nNo tokens found with {MIN_WALLETS}+ tracked wallets.")
        return

    # Check ages via DexScreener
    print("Checking token ages...", file=sys.stderr)
    age_data = check_dexscreener_age(list(hot_tokens.keys()))

    # Filter by age and print results
    results = []
    for mint, holders in hot_tokens.items():
        info = age_data.get(mint, {})
        age_h = info.get("age_h", 9999)
        if age_h <= MAX_AGE_HOURS:
            results.append((len(holders), mint, holders, info))

    results.sort(reverse=True)

    if not results:
        print(f"\nNo tokens with {MIN_WALLETS}+ wallets that are ≤{MAX_AGE_HOURS}h old.")
        print("\nTop tokens by wallet count (any age):")
        top = sorted(hot_tokens.items(), key=lambda x: -len(x[1]))[:10]
        for mint, holders in top:
            info = age_data.get(mint, {})
            age_h = info.get("age_h", 9999)
            print(f"  {len(holders)} wallets | {info.get('symbol','?')} | {mint[:12]}... | {age_h:.0f}h | ${info.get('mcap',0):,.0f} mcap")
        return

    print(f"\n{'='*60}")
    print(f"COINS ≤{MAX_AGE_HOURS}h OLD WITH {MIN_WALLETS}+ TRACKED WALLETS")
    print(f"{'='*60}\n")
    for count, mint, holders, info in results:
        print(f"🔥 {info.get('symbol','?')} — {count} tracked wallets")
        print(f"   CA: {mint}")
        print(f"   Age: {info.get('age_h',0):.1f}h | MCap: ${info.get('mcap',0):,.0f} | Vol24: ${info.get('vol24',0):,.0f}")
        holders_sorted = sorted(holders, key=lambda x: -x["amount"])
        for h in holders_sorted[:10]:
            print(f"   • {h['name']}: {h['amount']:,.0f}")
        print()

if __name__ == "__main__":
    main()
