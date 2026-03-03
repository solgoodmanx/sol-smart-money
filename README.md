# sol-smart-money

**On-chain wallet intelligence for Solana memecoins.**

One question: *what is smart money doing with this coin right now?*

```
python check_holders.py <TOKEN_MINT_ADDRESS>

  6 tracked wallets holding:

  Wallet                          Amount            % Supply
  ----------------------------    ----------------  --------
  good whale                      33,000,000.00        3.30%
  low entry                       17,122,186.00        1.71%
  bottom bidder                   10,384,800.00        1.04%
  lowcap hunter                    3,592,000.00        0.36%
  ...
```

---

## How It Works

Instead of checking each wallet individually (slow, rate-limited), `sol-smart-money` flips the problem:

1. **One call** fetches all holders of the token
2. **Set intersection** against your tracked wallet list
3. Result in seconds, regardless of list size

This architecture scales. 1,000 wallets or 10,000 — same speed.

---

## The On-Chain Stack

Frontend tools — DEX Screener, GMGN, Birdeye, trading terminals — are good for price and volume. They don't tell you *who* is holding and *when* they got in.

For serious on-chain analysis, the right tools are lower in the stack:

- **[OKX Web3 API](https://www.okx.com/web3/build/docs)** — wallet history, token flows, PnL, cross-chain data. The most comprehensive public API for on-chain intelligence. This is the layer serious analysts use when they need the full picture: entry timing, wallet behavior, flow patterns.
- **Solana RPC** — raw on-chain state. `sol-smart-money` uses a reliable Solana RPC endpoint to fetch the full holder list for any token in one call. Helius (free tier at [helius.dev](https://helius.dev)) works well for this; any Solana RPC that supports `getTokenAccounts` will do.

The roadmap for this repo moves progressively deeper into the OKX Web3 API layer — buy/sell timing, average entry price, PnL context per wallet.

---

## Setup

### 1. Get a Solana RPC key

Free tier at [helius.dev](https://helius.dev) — no credit card needed. Any RPC supporting `getTokenAccounts` works.

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
  { "address": "...", "name": "low entry",     "chain": "solana" },
  { "address": "...", "name": "good whale",    "chain": "solana" },
  { "address": "...", "name": "bottom bidder", "chain": "solana" }
]
```

**Your `wallets.json` is gitignored and stays local.** It never leaves your machine.

> **Building a quality wallet list is what makes this tool powerful.** The more high-signal wallets you track — consistent early buyers, wallets with strong PnL history, known alpha wallets — the more signal you extract from each query. Start small (10–20 wallets), watch their trades for a few weeks, and expand from there. Quality beats quantity.

### 3. Run

```bash
python check_holders.py <CA>
python check_holders.py <CA> --wallets ~/my-wallets.json
python check_holders.py <CA> --json
```

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
- [x] Buy/sell timing — when did tracked wallets enter? (`wallet_history.py`)
- [ ] Average entry price per wallet
- [ ] PnL context — unrealized gain/loss at current price
- [ ] Historical overlap patterns — which wallets cluster together?
- [ ] Solana launchpad attribution (pump.fun, PumpSwap, Meteora, LetsBonk, etc.)
- [ ] Wallet scoring — entry frequency, win rate, avg hold time

---

## Data Sources

See [references/data-sources.md](references/data-sources.md) for a full breakdown of data sources, their limitations, and trust model.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).
