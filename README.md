# sol-smart-money

**On-chain wallet intelligence for Solana memecoins.**

One question: *what is smart money doing with this coin right now?*

```
python check_holders.py <TOKEN_MINT_ADDRESS>

  6 tracked wallets holding:

  Wallet                          Amount            % Supply
  ----------------------------    ----------------  --------
  bottom bidder                   10,384,800.00        1.04%
  low entry                       17,122,186.00        1.71%
  good whale                       3,592,000.00        0.36%
  ...
```

---

## How It Works

Instead of checking each wallet individually (slow, rate-limited), `sol-smart-money` flips the problem:

1. **One call** to Helius fetches all holders of the token
2. **Set intersection** against your tracked wallet list
3. Result in seconds, regardless of list size

This architecture scales. 1,000 wallets or 10,000 — same speed.

---

## Setup

### 1. Get a Helius API key

Free tier at [helius.dev](https://helius.dev) — no credit card needed. Helius is the recommended Solana RPC for this kind of work. It's faster, more reliable, and better indexed than public endpoints.

```bash
cp .env.example .env
# Add your HELIUS_API_KEY to .env
```

### 2. Build your wallet list

Copy the example and populate it with wallets you want to track:

```bash
cp wallets.example.json wallets.json
```

```json
[
  { "address": "...", "name": "SmartTrader1", "chain": "solana" },
  { "address": "...", "name": "EarlyAlpha",   "chain": "solana" }
]
```

**Your `wallets.json` is gitignored and stays local.** It never leaves your machine.

> **Building a quality wallet list is what makes this tool powerful.** The more high-signal wallets you track — consistent early buyers, wallets with strong PnL history, known community figures — the more signal you extract from each query. Start small (10–20 wallets), track their trades for a few weeks, and expand from there. Quality beats quantity.

### 3. Run

```bash
python check_holders.py <CA>
python check_holders.py <CA> --wallets ~/my-wallets.json
python check_holders.py <CA> --json
```

---

## Why Helius over DEX Screener / GMGN / on-platform tools?

Most traders use DEX Screener for quick chart checks or rely on trading platforms (Trojan, Padre, Axiom) for token info. These are great for price/volume, but they don't give you wallet-level intelligence.

For deep on-chain analysis, **[OKX Web3 API](https://www.okx.com/web3/build/docs)** is worth exploring — it provides wallet history, token flows, and cross-chain data in ways that no frontend tool surfaces. It's what serious on-chain analysts reach for when they need the raw picture.

`sol-smart-money` uses Helius directly because:
- `getTokenAccounts` returns the full holder list in one paginated call — no equivalent on GMGN or DEX Screener
- No rate-limit hell at scale
- Returns raw amounts + owner addresses, which is all we need for cross-referencing
- Zero frontend overhead — pure on-chain truth

---

## Output

| Field | Description |
|-------|-------------|
| `name` | Your label for the wallet |
| `amount` | Token balance (human-readable, decimals applied) |
| `pct_supply` | % of total token supply held |

Sorted by amount descending. JSON output available via `--json`.

---

## Roadmap

- [x] Holder cross-reference (v0.1.0)
- [x] Proper decimals + % supply display
- [ ] Buy/sell timing analysis (when did tracked wallets enter?)
- [ ] Average entry price per wallet
- [ ] PnL context (unrealized gain/loss at current price)
- [ ] Historical overlap patterns (which wallets cluster together?)
- [ ] Solana launchpad attribution (pump.fun, PumpSwap, Meteora, LetsBonk, etc.)
- [ ] Wallet scoring (frequency of early entries, win rate)

---

## Data Sources

See [references/data-sources.md](references/data-sources.md) for a full breakdown of data sources used, their limitations, and trust model.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).
