# Security Policy

## Private Data

**Your `wallets.json` is never committed.** It is listed in `.gitignore` and should never be pushed to any remote repository. This is intentional — your tracked wallet list is your alpha and should stay local.

Similarly, your `.env` file (containing your Helius API key) is gitignored and should never be committed.

## API Key Safety

- Store your `HELIUS_API_KEY` in `.env` (gitignored) or as an environment variable
- Never hardcode API keys in source files
- Helius free-tier keys have usage caps — monitor your dashboard if running at scale

## No External Calls Except Helius RPC

`check_holders.py` makes calls only to `mainnet.helius-rpc.com`. No analytics services, no tracking, no third-party data brokers. You can verify this by reading the source — it's intentionally kept to stdlib only.

## Reporting Vulnerabilities

Open a GitHub issue. This project has no proprietary secrets to protect — the wallet list is yours and stays with you.
