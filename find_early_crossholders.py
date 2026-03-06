#!/usr/bin/env python3
"""
find_early_crossholders.py

Find wallets that:
1. Currently hold target token (SUGEE)
2. Bought at <= max_mc_usd market cap (entry price filter)
3. Previously traded reference coins (coin_a, coin_b)
4. Have since EXITED the reference coins (no longer holding)

Usage:
    python3 find_early_crossholders.py <TARGET_CA> <MAX_MCAP_USD> <COIN_A_CA> <COIN_B_CA>
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

HELIUS_RPC_URL = "https://mainnet.helius-rpc.com/?api-key={key}"
HELIUS_TXN_URL = "https://api.helius.xyz/v0/addresses/{addr}/transactions?api-key={key}&limit=100&type=SWAP"

def load_api_key():
    key = os.environ.get("HELIUS_API_KEY")
    if key:
        return key
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip().startswith("HELIUS_API_KEY="):
                return line.split("=",1)[1].strip().strip('"\'')
    sys.exit("HELIUS_API_KEY not set")

def rpc_post(url, method, params):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get_all_holders(mint, rpc_url):
    """Get all token holders via getTokenAccounts (paginated)."""
    holders = {}
    cursor = None
    while True:
        params = {
            "mint": mint,
            "limit": 1000,
            "displayOptions": {"showZeroBalance": False}
        }
        if cursor:
            params["cursor"] = cursor
        resp = rpc_post(rpc_url, "getTokenAccounts", params)
        result = resp.get("result", {})
        accounts = result.get("token_accounts", [])
        for acc in accounts:
            owner = acc.get("owner", "")
            amount = float(acc.get("amount", 0))
            if owner and amount > 0:
                holders[owner] = amount
        cursor = result.get("cursor")
        if not cursor or not accounts:
            break
    return holders

def get_token_decimals(mint, rpc_url):
    try:
        resp = rpc_post(rpc_url, "getTokenSupply", [mint])
        return int(resp["result"]["value"]["decimals"])
    except Exception:
        return 6

def get_wallet_swaps(addr, api_key, target_mint, max_pages=3):
    """Get swap transactions for wallet, look for trades involving target_mint."""
    trades = []
    url = HELIUS_TXN_URL.format(addr=addr, key=api_key)
    before = None
    for page in range(max_pages):
        page_url = url
        if before:
            page_url += f"&before={before}"
        try:
            req = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                txns = json.loads(r.read())
        except Exception:
            break
        if not txns:
            break
        for tx in txns:
            ts = tx.get("timestamp", 0)
            # Look in tokenTransfers for target mint involvement
            token_transfers = tx.get("tokenTransfers", [])
            native_transfers = tx.get("nativeTransfers", [])
            involved_mints = set(t.get("mint","") for t in token_transfers)
            if target_mint in involved_mints:
                # Find how much of target_mint the wallet received (buy) or sent (sell)
                # Also find SOL amount
                sol_in = sum(t.get("amount",0) for t in native_transfers if t.get("toUserAccount","") == addr)
                sol_out = sum(t.get("amount",0) for t in native_transfers if t.get("fromUserAccount","") == addr)
                tok_in = sum(float(t.get("tokenAmount",0)) for t in token_transfers if t.get("mint")==target_mint and t.get("toUserAccount","")==addr)
                tok_out = sum(float(t.get("tokenAmount",0)) for t in token_transfers if t.get("mint")==target_mint and t.get("fromUserAccount","")==addr)
                if tok_in > 0 or tok_out > 0:
                    trades.append({
                        "ts": ts,
                        "sol_in": sol_in/1e9,
                        "sol_out": sol_out/1e9,
                        "tok_in": tok_in,
                        "tok_out": tok_out,
                        "sig": tx.get("signature","")[:12]
                    })
        before = txns[-1].get("signature") if txns else None
        time.sleep(0.05)
    return sorted(trades, key=lambda x: x["ts"])

def check_current_holding(wallet, mint, rpc_url):
    """Check if wallet currently holds a specific token mint."""
    params = [
        wallet,
        {"mint": mint},
        {"encoding": "jsonParsed", "commitment": "confirmed"}
    ]
    try:
        resp = rpc_post(rpc_url, "getTokenAccountsByOwner", params)
        accounts = resp.get("result", {}).get("value", [])
        for acc in accounts:
            info = acc.get("account",{}).get("data",{}).get("parsed",{}).get("info",{})
            amount = float(info.get("tokenAmount",{}).get("uiAmount") or 0)
            if amount > 0:
                return amount
    except Exception:
        pass
    return 0.0

def check_tx_history_for_mint(addr, api_key, target_mint, max_pages=5):
    """Check if wallet has any swap history involving target_mint."""
    url = HELIUS_TXN_URL.format(addr=addr, key=api_key)
    before = None
    for page in range(max_pages):
        page_url = url
        if before:
            page_url += f"&before={before}"
        try:
            req = urllib.request.Request(page_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as r:
                txns = json.loads(r.read())
        except Exception:
            break
        if not txns:
            break
        for tx in txns:
            token_transfers = tx.get("tokenTransfers", [])
            for t in token_transfers:
                if t.get("mint","") == target_mint:
                    return True
        before = txns[-1].get("signature") if txns else None
        time.sleep(0.05)
    return False

def get_sol_price_usd():
    """Get current SOL price from Kraken."""
    try:
        req = urllib.request.Request(
            "https://api.kraken.com/0/public/Ticker?pair=SOLUSD",
            headers={"User-Agent":"Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read())
            result = d.get("result", {})
            key = [k for k in result if k != "last"][0]
            return float(result[key]["c"][0])
    except Exception:
        return 90.0

def get_sol_hourly_prices(since_ts):
    """Get SOL/USD hourly prices from Kraken since given timestamp. Returns {hour_ts: price}."""
    try:
        url = f"https://api.kraken.com/0/public/OHLC?pair=SOLUSD&interval=60&since={int(since_ts)}"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            result = d.get("result", {})
            key = [k for k in result if k != "last"][0]
            candles = result[key]
            # {hour_start_ts: close_price}
            return {int(c[0]): float(c[4]) for c in candles}
    except Exception:
        return {}

def sol_price_at(ts, hourly_prices, fallback):
    """Get SOL price at a given timestamp using hourly buckets."""
    if not hourly_prices:
        return fallback
    # Floor to nearest hour
    hour_ts = (int(ts) // 3600) * 3600
    if hour_ts in hourly_prices:
        return hourly_prices[hour_ts]
    # Find closest
    closest = min(hourly_prices.keys(), key=lambda h: abs(h - hour_ts))
    return hourly_prices[closest]

def main():
    if len(sys.argv) < 5:
        print("Usage: python3 find_early_crossholders.py <TARGET_CA> <MAX_MCAP_USD> <COIN_A_CA> <COIN_B_CA>")
        sys.exit(1)

    target_ca = sys.argv[1]
    max_mcap = float(sys.argv[2])
    coin_a = sys.argv[3]
    coin_b = sys.argv[4]
    supply = 1_000_000_000  # standard pump.fun supply

    api_key = load_api_key()
    rpc_url = HELIUS_RPC_URL.format(key=api_key)

    sol_price = get_sol_price_usd()
    # Get today's hourly SOL prices for historical accuracy
    today_midnight = (int(time.time()) // 86400) * 86400
    hourly_sol_prices = get_sol_hourly_prices(today_midnight - 86400)
    print(f"SOL price now: ${sol_price:.2f} | Hourly history: {len(hourly_sol_prices)} candles", file=sys.stderr)
    max_price_usd = max_mcap / supply
    print(f"Max entry price: ${max_price_usd:.8f} (${max_mcap:,.0f} mcap)", file=sys.stderr)

    # Step 1: Get all current holders
    print(f"Step 1: Getting all {target_ca[:12]}... holders...", file=sys.stderr)
    holders = get_all_holders(target_ca, rpc_url)
    print(f"  Found {len(holders)} holders", file=sys.stderr)

    # Determine the timestamp cutoffs for ≤$65k entry
    # SUGEE crossed $65k (~$0.000065) at ~15:35 UTC on 2026-03-05
    # It dipped back below $65k during 16:55-17:25 UTC
    # Timestamps (UTC unix):
    UNDER_65K_BEFORE = 1772724900  # 15:35 UTC today — everything before this was under $65k
    DIP_START = 1772729700         # 16:55 UTC today
    DIP_END   = 1772731500         # 17:25 UTC today

    def is_under_65k_ts(ts):
        return ts < UNDER_65K_BEFORE or (DIP_START <= ts <= DIP_END)

    # Step 2: For each holder, get their SUGEE swap history and find earliest buy ts
    print("Step 2: Checking entry timestamps (≤$65k windows: before 15:35 UTC or 16:55-17:25 UTC)...", file=sys.stderr)
    early_buyers = {}  # wallet -> {amount, entry_mcap, entry_ts, sol_spent}

    def check_entry(wallet, balance):
        trades = get_wallet_swaps(wallet, api_key, target_ca, max_pages=3)
        if not trades:
            return None
        buys = [t for t in trades if t["tok_in"] > 0]
        if not buys:
            return None
        # Weighted average entry using historical SOL price at each buy timestamp
        total_usd_spent = sum(
            t["sol_out"] * sol_price_at(t["ts"], hourly_sol_prices, sol_price)
            for t in buys
        )
        total_tok = sum(t["tok_in"] for t in buys)
        if total_tok > 0 and total_usd_spent > 0:
            avg_price_usd = total_usd_spent / total_tok
            avg_mcap = avg_price_usd * supply
        else:
            return None
        if avg_mcap <= max_mcap:
            return {
                "balance": balance,
                "entry_mcap": avg_mcap,
                "entry_ts": buys[0]["ts"],
                "sol_spent": sum(t["sol_out"] for t in buys),
                "num_buys": len(buys),
            }
        return None

    completed = 0
    total = len(holders)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_entry, w, b): w for w, b in holders.items()}
        for future in as_completed(futures):
            wallet = futures[future]
            result = future.result()
            if result:
                early_buyers[wallet] = result
            completed += 1
            if completed % 50 == 0:
                print(f"  {completed}/{total} checked, {len(early_buyers)} early buyers so far...", file=sys.stderr)

    print(f"  Found {len(early_buyers)} wallets that entered at ≤${max_mcap:,.0f} mcap", file=sys.stderr)

    if not early_buyers:
        print("No early buyers found.")
        return

    # Step 3: Check which early buyers DON'T currently hold coin_a and coin_b (have exited)
    print("Step 3: Checking current holdings of reference coins...", file=sys.stderr)
    exited_both = {}

    def check_exits(wallet, data):
        holds_a = check_current_holding(wallet, coin_a, rpc_url)
        holds_b = check_current_holding(wallet, coin_b, rpc_url)
        # "exited" means not currently holding
        return wallet, data, holds_a, holds_b

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_exits, w, d): w for w, d in early_buyers.items()}
        for future in as_completed(futures):
            wallet, data, holds_a, holds_b = future.result()
            # Include if they don't currently hold either (exited)
            # We'll check if they EVER traded them next
            data["currently_holds_a"] = holds_a
            data["currently_holds_b"] = holds_b
            exited_both[wallet] = data

    # Filter: not currently holding (exited)
    not_holding = {w: d for w, d in exited_both.items() if d["currently_holds_a"] == 0 and d["currently_holds_b"] == 0}
    still_holding = {w: d for w, d in exited_both.items() if d["currently_holds_a"] > 0 or d["currently_holds_b"] > 0}
    print(f"  {len(not_holding)} don't hold reference coins currently | {len(still_holding)} still holding", file=sys.stderr)

    # Step 4: For wallets not currently holding, check if they EVER traded coin_a or coin_b
    print("Step 4: Checking tx history for reference coin trades...", file=sys.stderr)
    qualified = {}

    def check_history(wallet, data):
        traded_a = check_tx_history_for_mint(wallet, api_key, coin_a, max_pages=5)
        traded_b = check_tx_history_for_mint(wallet, api_key, coin_b, max_pages=5)
        return wallet, data, traded_a, traded_b

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(check_history, w, d): w for w, d in not_holding.items()}
        for future in as_completed(futures):
            wallet, data, traded_a, traded_b = future.result()
            if traded_a or traded_b:
                data["traded_a"] = traded_a
                data["traded_b"] = traded_b
                qualified[wallet] = data

    # Print results
    print(f"\n{'='*65}")
    print(f"RESULTS: Wallets holding SUGEE (≤${max_mcap:,.0f}k entry) who traded")
    print("         E=MC² / reference coins and have since EXITED")
    print(f"{'='*65}\n")

    if not qualified:
        print("None found matching all criteria.")
        # Still print early buyers for reference
        print(f"\nEarly buyers (${max_mcap:,.0f} entry) for reference: {len(early_buyers)}")
        for w, d in sorted(early_buyers.items(), key=lambda x: x[1]["entry_mcap"]):
            import datetime
            ts_str = datetime.datetime.utcfromtimestamp(d['entry_ts']).strftime('%H:%M UTC') if d['entry_ts'] else '?'
            print(f"  {w[:12]}... | entry ~${d['entry_mcap']:,.0f} mcap | {ts_str}")
        return

    for wallet, data in sorted(qualified.items(), key=lambda x: x[1]["entry_mcap"]):
        import datetime
        ts_str = datetime.datetime.utcfromtimestamp(data['entry_ts']).strftime('%H:%M UTC') if data['entry_ts'] else '?'
        print(f"Wallet: {wallet}")
        print(f"  SUGEE entry: ~${data['entry_mcap']:,.0f} mcap @ {ts_str} | {data['sol_spent']:.3f} SOL")
        print(f"  Current SUGEE balance: {data['balance']:,.0f}")
        print(f"  Traded E=MC²: {'✅' if data['traded_a'] else '❌'}")
        print(f"  Traded coin_b: {'✅' if data['traded_b'] else '❌'}")
        print()

if __name__ == "__main__":
    main()
