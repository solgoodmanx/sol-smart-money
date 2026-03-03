# Contributing

Contributions welcome. Keep it focused — this repo does one thing well.

## What fits here

- Bug fixes in `check_holders.py`
- New Solana launchpad attribution scripts (pump.fun, PumpSwap, Meteora, LetsBonk, etc.)
- Additional analysis scripts (buy timing, entry price, PnL context)
- Test coverage improvements
- Documentation improvements

## What doesn't fit here

- EVM/Base chain support (see [base-narrative-catcher](https://github.com/solgoodmanx/base-narrative-catcher))
- Frontend or UI code
- Wallet lists, private data, or anything that shouldn't be public

## Standards

- Python 3.11+
- stdlib only — no external dependencies
- `ruff check .` must pass
- Tests in `tests/` using `unittest`; all tests must pass
- New scripts: include a `--help` argparse description and at least 3 unit tests

## Running tests locally

```bash
python -m pytest tests/ -v
```

## Linting

```bash
pip install ruff
ruff check .
```
