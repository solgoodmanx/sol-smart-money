# sol-smart-money v0.3.0 — OKX intelligence layer mapped

This release marks a meaningful expansion in how `sol-smart-money` thinks about Solana wallet intelligence.

The original project proved one core idea:

> use Helius to fetch the full holder set for a token, then intersect it against a high-signal tracked wallet list.

That remains the foundation.

What changed in `v0.3.0` is that we now understand — and have live-verified — a much richer intelligence overlay sitting on top of that raw holder truth.

## What we discovered

OKX OnchainOS is not just a generic market-data API.

It now exposes **two serious intelligence surfaces** that materially improve Solana coin analysis:

### 1. Portfolio API (`/api/v6/dex/market/portfolio/*`)
A wallet-analytics layer that exposes:
- realized PnL
- unrealized PnL
- average buy / sell price
- win rate
- preferred market-cap range
- per-token PnL snapshots
- DEX transaction history for a wallet + token

This is effectively the data layer behind OKX's top-traders style UI.

### 2. Strategy / Meme Pump API (`/api/v6/dex/market/memepump/*`)
A trenches scanner layer that exposes:
- supported launchpad protocols by chain
- token lifecycle stage (`NEW`, `MIGRATING`, `MIGRATED`)
- developer history (`totalTokens`, `migratedCount`, `rugPullCount`, `goldenGemCount`)
- holder-structure quality metrics (bundlers, insiders, snipers, fresh wallets, suspected phishing wallets)
- bundler concentration and ATH bundled share
- co-invested / aped wallet lists with labels like `SMART_MONEY`, `INFLUENCER`, `KOL`, `NORMAL`

This means `sol-smart-money` is no longer just about “which tracked wallets hold this?”
It now has a verified path toward answering:
- who is winning on this coin?
- what kind of wallets are in it?
- what kind of dev history sits behind it?
- how clean or dirty is the distribution?

## What was live-verified

Using the shared OKX key, we verified live responses for:

### Portfolio endpoints
- `/portfolio/supported/chain`
- `/portfolio/overview`
- `/portfolio/recent-pnl`
- `/portfolio/token/latest-pnl`
- `/portfolio/dex-history`

### Strategy endpoints
- `/memepump/supported/chainsProtocol`
- `/memepump/tokenList`
- `/memepump/tokenDevInfo`
- `/memepump/similarToken`
- `/memepump/tokenBundleInfo`
- `/memepump/apedWallet`

These were not theoretical doc reads — they returned real payloads on live Solana tokens.

## Architecture clarification

The stack is now best understood as:

- **Helius = raw truth layer**
  - full holder set
  - canonical source for current Solana holder intersection

- **OKX Portfolio = wallet PnL layer**
  - who actually made money
  - who is still sitting on paper gains
  - top-trader ranking primitives

- **OKX Strategy = trenches quality layer**
  - dev history
  - launchpad support
  - bundlers / snipers / fresh-wallet mix
  - aped wallet overlays

That architecture is the main substance of this release.

## Important caveats we documented

This release also records practical findings from live testing:

- some docs are sparse or inconsistent
- some endpoints are richer in payload than in documentation
- `tokenDetails` can return `null` while sibling Strategy endpoints still work
- ultra-bare Python requests may get HTTP 403 where curl/fetch-style requests with a normal `User-Agent` succeed
- Helius still remains essential for complete holder intersection; OKX does not replace that role

## What changed in the repo

- README updated to reflect the expanded intelligence stack
- data source documentation updated to show Helius + OKX Portfolio + OKX Strategy roles clearly
- changelog updated with live-verified endpoint coverage and quirks
- roadmap updated toward:
  - top traders ranking
  - realized PnL per wallet
  - wallet behavior profiling
  - trenches quality overlays
  - co-invested wallet analysis

## Why this is a minor-version release

`v0.3.0` is the right version bump because the project meaningfully expanded in scope and architecture.

This is not just a wording change or a typo fix.

The codebase still starts from holder intersection, but the verified data model behind the project is now substantially broader than `v0.2.0`.

## Short version

`sol-smart-money` started as:
> Which tracked wallets hold this Solana coin right now?

`sol-smart-money v0.3.0` becomes:
> Which tracked wallets hold it, which wallets are winning on it, and how clean or dirty is the coin's wallet/dev structure?
