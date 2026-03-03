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

OKX Web3 API covers wallet history, token flows, cross-chain asset tracking, and DEX aggregation. It's most useful if you want to track wallets across multiple chains (Solana + Base + EVM) from a single API.

**For Solana-only analysis, Helius covers the same ground natively** — transaction history, token transfers, buy/sell timing — with better Solana-specific indexing and no cross-chain overhead. `sol-smart-money` uses Helius directly for all wallet intelligence features.

The OKX Web3 DEX API (swap routing, price quotes, liquidity) is a separate product from the wallet data endpoints and requires separate access approval.

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
