# Changelog

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
