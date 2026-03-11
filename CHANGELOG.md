# Changelog

## [0.3.0] — 2026-03-11

### Changed
- Reframed OKX as two real intelligence layers instead of generic cross-chain reference only:
  - **Portfolio API** (`/api/v6/dex/market/portfolio/*`) for wallet PnL, win rate, average buy/sell price, and DEX history
  - **Trenches / Meme Pump Strategy API** (`/api/v6/dex/market/memepump/*`) for stage scanning, dev history, bundler concentration, and co-invested wallet overlays
- `references/data-sources.md` updated to reflect live-tested OKX Portfolio + Strategy support
- README updated to show OKX's newer surfaces and how they complement Helius

### Verified
- Shared OKX key returned live data for Strategy endpoints including:
  - supported Solana launchpads/protocols
  - token scanner list
  - developer history (`rugPullCount`, `migratedCount`, `goldenGemCount`)
  - bundle metrics
  - aped wallet lists with `SMART_MONEY` / `INFLUENCER` / `NORMAL` labels and PnL
- Shared OKX key returned live data for Portfolio endpoints including:
  - wallet overview / win rate
  - recent token PnL
  - latest token PnL for specific wallet+token pair
  - DEX transaction history
- Documented practical quirks from live testing:
  - `tokenDetails` may return `null` while other Strategy endpoints still work
  - bare Python requests may get 403 where curl/fetch-style requests with normal `User-Agent` succeed

## [0.2.0] — 2026-03-03

All notable changes to this project will be documented in this file.


### Added
- `wallet_history.py` — pull buy/sell timeline for any wallet + token pair via Helius transaction API
  - Shows first buy timestamp, total buys/sells, net position, full event log
  - `--limit`, `--json` flags
- 11 new tests for `wallet_history.py` (21 total across suite)

### Changed
- Roadmap: OKX Web3 API items moved to Helius-native implementation
- `references/data-sources.md`: clarified OKX scope (cross-chain only); Helius is primary for all Solana wallet intelligence
- README roadmap updated: buy/sell timing marked complete

## [0.1.0] — 2026-03-03

### Added
- `check_holders.py` — cross-reference any Solana token's holders against a local tracked wallet list
- Helius `getTokenAccounts` architecture: one inbound call → set intersection (scales regardless of list size)
- Proper decimal handling via `getTokenSupply` — amounts displayed in human-readable units
- % of total supply display per wallet
- `--json` flag for machine-readable output
- `--wallets` flag for custom wallet list path
- `wallets.example.json` — schema reference for building your own wallet list
- MIT license
- CI via GitHub Actions (ruff lint + unittest, Python 3.11 + 3.12)
- `SECURITY.md`, `CONTRIBUTING.md`
- `references/data-sources.md` — full data source transparency doc
