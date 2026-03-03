# Fee Redirect Narrative — Signal Framework

## What It Is

A class of Solana tokens (primarily launched via pump.fun / PumpSwap) where the
developer permanently locks trading fees to an external address — typically a
wallet belonging to a publicly identifiable person rather than the dev themselves.

The recipient is usually a researcher, builder, artist, or public figure whose
work is thematically aligned with the coin's name and concept. The fee lock is
onchain and irreversible: the dev cannot reclaim or redirect it after the fact.

---

## Why It Creates Narrative Momentum

### 1. Trust signal (structural)
Locked fees remove a core rug vector. The dev cannot drain fee income after
launch. This is verifiable onchain, which makes it credible to skeptical buyers.

### 2. "Deserving recipient" framing
The implicit message is: *fees go to the person who actually built the thing
the coin is named after, not to a random dev.* This reframes a speculative
token as a form of tribute or recognition — a different psychological register
than a normal memecoin.

### 3. Suspense loop
If the recipient hasn't claimed or acknowledged the fees yet, the coin becomes
a live event. The community watches: *will they notice? will they post? will
they embrace it?* Each day without a response extends the anticipation cycle.
A single acknowledgment tweet from the recipient can function as a catalyst.

### 4. Identity credibility multiplier
The strength of this mechanic scales with the recipient's public credibility.
A real researcher with verifiable work, a long GitHub history, or institutional
ties makes the narrative stick. A pseudonymous account with no track record
weakens it. The coin borrows legitimacy from the recipient's identity.

---

## How to Identify It Onchain

On pump.fun and PumpSwap, the creator fee destination is a configurable field
set at launch. To detect this pattern:

1. Pull the token's creation transaction from Helius
   (`getTransaction` with the mint signature)
2. Look for a `feeRecipient` or equivalent field in the program instruction data
3. If the fee recipient address differs from the deployer/authority address,
   resolve the recipient wallet
4. Cross-reference the recipient address against known public identities:
   - GitHub account with linked wallet
   - ENS / Solana domain name
   - Prior onchain activity linked to a public persona

Helius enhanced transactions parse most of this — look for `tokenTransfers`
and `accountData` changes in the creation tx, or check the AMM pool
initialization accounts.

---

## Signal Grading

| Factor | Bullish | Bearish |
|--------|---------|---------|
| Recipient identity | Verifiable, credible, real work | Anonymous or unverifiable |
| Thematic alignment | Name/concept directly tied to recipient's work | Loose or forced connection |
| Lock status | Confirmed irreversible onchain | Unverified, dev retains control |
| Claim status | Unclaimed (suspense active) OR just claimed (catalyst) | Claimed long ago, old news |
| Recipient activity | Recently active (repo updates, posts) | Dormant account |
| CT pickup | High-signal accounts discussing the connection | No CT awareness yet |

---

## Lifecycle Pattern

```
Launch → fee lock verified → community discovers recipient identity
  → suspense builds (unclaimed phase)
    → [path A] recipient acknowledges → catalyst event, price spike
    → [path B] CT narrative peaks before claim → organic run, fades
    → [path C] recipient ignores → narrative dies, holders exit
```

The highest-EV window is typically **before CT awareness peaks** — when the
fee lock has been verified onchain but the recipient connection isn't yet
widely known.

---

## Related Concepts

- **Tribute coins** — tokens named after real people/projects without the fee
  mechanic. Weaker structural signal (no onchain lock), but same identity
  borrowing dynamic.
- **Revenue-share tokens** — fees go to token holders rather than an external
  identity. Different mechanic, no narrative suspense component.
- **Locked LP** — related trust signal (liquidity can't be pulled), but
  distinct from fee destination locking.
