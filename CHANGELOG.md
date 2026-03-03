# Changelog

## [0.2.0] — 2026-03-03

### Added
- `wallet_history.py` — pull buy/sell timeline for any wallet + token pair via Helius transaction API
  - Shows first buy timestamp, total buys/sells, net position, full event log
  - `--limit`, `--json` flags
- 11 new tests for `wallet_history.py` (21 total across suite)

### Changed
- Roadmap: OKX Web3 API items moved to Helius-native implementation
- `references/data-sources.md`: clarified OKX scope (cross-chain only); Helius is primary for all Solana wallet intelligence
- README roadmap updated: buy/sell timing marked complete



All notable changes to this project will be documented in this file.

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
