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

## What this repo does

- finds tracked-wallet overlap for any Solana token fast
- fetches holder truth from Helius instead of relying on frontend aggregators
- supports wallet-history style analysis for entry / exit timing
- documents and validates OKX Portfolio + Strategy overlays for PnL, wallet quality, and trenches context

## What this repo does not do

- execute trades
- guarantee token legitimacy
- reconstruct every historical holder who fully exited and closed accounts
- replace raw Solana RPC truth with an aggregator

## Architecture

```text
Helius getTokenAccounts / getTokenSupply
        ↓
full holder set + decimals
        ↓
tracked wallet intersection
        ↓
OKX Portfolio overlay (PnL / avg buy-sell / overview)
        ↓
OKX Strategy overlay (dev history / bundlers / aped wallets / stage)
        ↓
final Solana wallet-intelligence scan
```

---

## The On-Chain Stack

Frontend tools — DEX Screener, GMGN, Birdeye, trading terminals — are good for price and volume. They don't tell you *who* is holding and *when* they got in.

For serious on-chain analysis, the right tools are lower in the stack:

- **[OKX Web3 API](https://www.okx.com/web3/build/docs)** — wallet history, token flows, PnL, cross-chain data. The most comprehensive public API for on-chain intelligence. Two surfaces matter most now:
  - `/api/v6/dex/market/portfolio/*` exposes per-wallet realized PnL, average buy/sell price, win rate, hold duration, and full DEX transaction history — the same data layer that powers OKX's top traders UI, now API-accessible.
  - `/api/v6/dex/market/memepump/*` exposes OKX's trenches scanner: token stage (`NEW/MIGRATING/MIGRATED`), developer history, bundler concentration, suspected sniper/insider/fresh-wallet ratios, and labeled co-invested wallets (`SMART_MONEY`, `INFLUENCER`, `NORMAL`) with holdings and PnL.
- **Solana RPC** — raw on-chain state. `sol-smart-money` uses a reliable Solana RPC endpoint to fetch the full holder list for any token in one call. Helius (free tier at [helius.dev](https://helius.dev)) works well for this; any Solana RPC that supports `getTokenAccounts` will do.

The roadmap for this repo now moves progressively deeper into OKX's official OnchainOS skill stack, with Helius staying the canonical source for full holder intersection.

### Official OKX split (important)

As of the official `okx/onchainos-skills` release, the clean way to think about OKX's stack is:

- **`okx-dex-token`** — token discovery, metadata, market-cap/liquidity views, holders, top traders, filtered token trade history
- **`okx-dex-market`** — raw price feeds, candles/K-line, index price, wallet PnL
- **`okx-dex-signal`** — market-wide smart-money / whale / KOL tracking
- **`okx-dex-trenches`** — meme launch scanning, dev reputation, bundle detection, aped-wallet overlays
- **`okx-dex-swap`** — quotes and swap execution
- **`okx-onchain-gateway`** — gas, simulation, broadcast, order tracking
- **`okx-wallet-portfolio`** — balances, holdings, total portfolio value

For `sol-smart-money`, the most important distinction is this:

- **Helius** answers: who holds this token right now?
- **OKX Token / Market / Trenches / Signal** answer: what kind of token is this, who is winning, what kind of wallets surround it, and what broader signal context exists around it?

That separation matters because this repo is strongest when it treats OKX as an analytics overlay on top of Solana holder truth, not as a replacement for Solana RPC.

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

### Example output

```text
$ python check_holders.py 61Np...pump

6 tracked wallets holding:

Wallet              Amount         % Supply
------------------  -------------  --------
LEAP                13,606,646.01    1.36%
low entry            8,001,871.42    0.80%
good whale           7,818,300.49    0.78%
...
```

This is the core holder-truth layer. Newer OKX overlays are documented in this repo and can enrich that result with:
- wallet PnL
- average entry / exit
- top-trader ranking
- dev / bundler / aped-wallet context

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

### Completed
- [x] Holder cross-reference (v0.1.0)
- [x] Proper decimals + % supply display
- [x] Buy/sell timing — when did tracked wallets enter? (`wallet_history.py`)
- [x] Average entry price per wallet (OKX Portfolio API — `/portfolio/token/latest-pnl`)
- [x] Realized PnL per wallet per token (OKX Portfolio API — `/portfolio/recent-pnl`)
- [x] Top traders ranking — Helius holder list + OKX PnL sort
- [x] Wallet overview — win rate, preferred market cap, buy patterns (`/portfolio/overview`)
- [x] Trenches quality scan — dev history, bundlers, snipers, insiders, fresh-wallet %, social presence (`/memepump/tokenDetails`, `/memepump/tokenDevInfo`)
- [x] Co-invested wallet overlay — smart-money / influencer / normal aped wallets (`/memepump/apedWallet`)
- [x] Solana launchpad attribution (pump.fun, PumpSwap, Meteora, LetsBonk, etc.)

### Next
- [ ] Historical overlap patterns — which wallets cluster together?
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
