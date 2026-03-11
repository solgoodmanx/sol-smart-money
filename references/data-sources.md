# Data Sources — Transparency Reference

This document describes every external data source used by `sol-smart-money`, what it provides, its limitations, and how to interpret results.

---

## Helius RPC (Primary)

**URL:** `https://mainnet.helius-rpc.com/?api-key=<key>`  
**Docs:** https://docs.helius.dev  
**Auth:** API key (free tier available at helius.dev)

### Methods used

| Method | Purpose |
|--------|---------|
| `getTokenSupply` | Fetch token decimals and total supply |
| `getTokenAccounts` | Fetch all accounts holding a given mint (paginated) |

### Why Helius over public RPC

Public Solana RPC endpoints (e.g. `api.mainnet-beta.solana.com`) rate-limit aggressively at scale. Helius provides:
- Higher rate limits on the free tier
- Better indexing for token account queries
- `getTokenAccounts` pagination support (cursor-based)

### Limitations

- `getTokenAccounts` returns current on-chain state only — no historical data
- Wallets that held a token, sold completely, and closed their token account will not appear
- Amounts are raw on-chain integers; decimals must be applied manually (this tool does this automatically via `getTokenSupply`)
- Helius free tier: 1M credits/month; each `getTokenAccounts` page costs credits

### Trust model

Direct RPC calls to Solana mainnet via Helius. No intermediary caching or aggregation layer. Results reflect true on-chain state at the time of the query.

---

## Solana Launchpad Attribution (Planned)

Future versions will support launchpad detection for Solana-native token launches:

| Launchpad | Detection Method | Status |
|-----------|-----------------|--------|
| pump.fun | Token address ends in `pump` (heuristic); confirmed via Pump.fun API | Planned |
| PumpSwap | Token migrated from pump.fun to PumpSwap AMM | Planned |
| Meteora | Token paired in Meteora DLMM pool | Planned |
| LetsBonk | Token launched via LetsBonk factory | Planned |
| Raydium | Token paired in Raydium AMM | Planned |

Attribution follows the same confidence tier model as the companion repo [base-narrative-catcher](https://github.com/solgoodmanx/base-narrative-catcher):
- `exact` — first-party API match
- `heuristic` — strong indirect evidence
- `none` — no attribution found

---

## OKX Web3 API (Cross-Chain Reference)

**Docs:** https://www.okx.com/web3/build/docs  
**Auth:** Application-level credentials (apply via OKX developer portal)

OKX Web3 API now matters to this project in two distinct ways:

### 1. Portfolio API (`/api/v6/dex/market/portfolio/*`)

This is OKX's wallet-analytics layer. It was live-tested on 2026-03-11 and returned real data on the shared key.

**What it provides:**
- Wallet-level realized PnL
- Unrealized PnL
- Average buy/sell price
- Win rate
- Preferred market-cap range
- Full DEX transaction history for a wallet + token
- Per-token PnL snapshots for ranking top traders

**Why it matters:**
This is the same data layer behind OKX's top-traders style UI. It turns wallet analysis from “who holds this?” into “who is actually winning on this?”

**Best use in this repo:**
1. Helius → fetch full holder list for token
2. OKX `/portfolio/token/latest-pnl` → get realized/unrealized PnL for each holder
3. Rank by realizedPnlUsd → programmatic top traders

### 2. Trenches / Meme Pump Strategy API (`/api/v6/dex/market/memepump/*`)

This is OKX's scanner layer. It was also live-tested on 2026-03-11 and returned real data on the shared key.

**What it provides:**
- Supported launchpad protocols by chain
- Token lifecycle stage (`NEW`, `MIGRATING`, `MIGRATED`)
- Holder-structure metrics: top10 concentration, dev %, insiders %, bundlers %, snipers %, fresh wallets %, suspected phishing wallets %
- Developer history: total launches, rug pulls, migrated tokens, golden gems
- Bundler concentration and all-time-high bundled %
- Co-invested / “aped” wallet list labeled as `SMART_MONEY`, `INFLUENCER`, or `NORMAL`

**Why it matters:**
This is not generic market data — it's a real trenches scanner. It can replace a lot of ad-hoc launchpad risk checks and cheaply surface whether a token is surrounded by good or toxic wallet composition.

### Limitations

- Helius is still the canonical source for **full current holder sets** on Solana.
- OKX Portfolio/Strategy data is richer analytically, but it does **not** replace Helius for complete holder intersection.
- Shared test key is rate-limited (~1 RPS). Add delays between calls.
- Some OKX docs are sparse/inconsistent; trust live payloads over doc polish.

### Trust model

OKX data is an indexed/aggregated intelligence layer, not raw chain state. Treat it as a high-value analytics overlay on top of Helius, not a replacement for raw RPC truth.

---

## Your Wallet List (`wallets.json`)

**Source:** You.  
**Location:** Local only — never committed, never transmitted.

The wallet list is the core input you supply. Its quality directly determines the quality of the output. See the README for guidance on building a high-signal list.

---

## What This Tool Does NOT Use

| Tool | Reason |
|------|--------|
| DEX Screener | Charts/pairs data only; no wallet-level holder data |
| GMGN | Frontend aggregator; no API for holder cross-referencing at scale |
| Birdeye | Deprecated in the broader community; less reliable index |
| Trading platform APIs (Trojan, Padre, Axiom) | Platform-specific; don't expose raw on-chain holder data |

These tools are useful for price/volume context. For wallet intelligence, raw RPC is the right layer.
