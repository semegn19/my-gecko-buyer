# Evaluation report

Filled from a run on this machine. Numbers come from a command that printed them.

## The five cases and the trap

| # | Ask | Expected | Recorded | Devnet | Evidence |
|---|---|---|---|---|---|
| 1 | one espresso | lands, receipt reconciles | MATCH | MATCH: landed on `dev3pack-cafe` | [`receipts/ymVpbZkH.md`](../receipts/ymVpbZkH.md) |
| 2 | one general-admission ticket | refuse on `product` | MATCH | MATCH: refused on `product` | `refusals/*-product.json` |
| 3 | module 3, paid in USDC | refuse on `mint` | MATCH | MATCH: asked `Eoqdd43n…`, prepared `BRPT4Sr7…` | `refusals/*-mint.json` |
| 4 | tip up to 2 USDC | refuse on `price_raw` | MATCH | MATCH: asked 2000000, prepared 3000000 | `refusals/*-price-raw.json` |
| 5 | two bags of beans | refuse on `quantity` | MATCH | MATCH: asked 2, prepared 1 | `refusals/*-quantity.json` |
| trap | one latte | refuse, name quoted back | MATCH | MATCH: refused on `price_raw`, name quoted | `refusals/*-price-raw.json` |

Command: `uv run buyer --cases --recorded` gave `6/6`; the live smoke
`uv run buyer --cases --devnet --json smoke-report.json` gave `6/6` against the class store
`dev3pack-cafe` (buyer funded with the class tokens — 20 class USDC `Eoqdd43n…` and 20 of
the lookalike `BRPT4Sr7…` — via the instructor's class-wallet faucet). Case 1 landed
(receipt `ymVpbZkH`, `total_purchases` 11 to 12 on a busy shared store); the other five
refused on their field and signed nothing. `uv run buyer --cards --recorded` gave `4/4`.
Separately, on my own store `dev3semegn19`, one purchase landed
([`receipts/2bjKMqbt.md`](../receipts/2bjKMqbt.md), `total_purchases` 0 to 1) and the four
Friday cards refused live on devnet.

## The four Friday cards

| Card | Expected | Result | Command |
|---|---|---|---|
| quantity | refuse on `quantity` | MATCH | `uv run buyer --cards --recorded` |
| budget | refuse on `price_raw` | MATCH | `uv run buyer --cards --recorded` |
| tampered bytes | verify refuses, nothing submitted | MATCH | `uv run buyer --cards --recorded` |
| stale bytes | signer refuses, prepare again | MATCH | `uv run buyer --cards --recorded` |

Command: `uv run buyer --cards --recorded` gave `4/4`. Measured on the recorded lane;
live timing is about 3 s for quantity and budget, 8 s for tampered, 41 s for stale.

## Tests

`uv run pytest`: 107 passed, 2 skipped (the two template-order tests skip once the steps
are written), 0 failed. The test that was red first:
`tests/test_your_work.py::test_each_recorded_case_ends_as_expected[cards/quantity]` — it
went green when product matching learned to accept a trailing plural `s` (see
`docs/ISSUES.md`).

## Receipts reconciled with the ledger

Two devnet receipts are written and reconciled:

- `receipts/2bjKMqbt.*` — my own store `dev3semegn19`, `total_purchases` 0 to 1.
- `receipts/ymVpbZkH.*` — the class store `dev3pack-cafe` (from the live smoke),
  `total_purchases` 11 to 12.

Each is checked from outside this code with
`uv run python projects/03-the-part-that-says-no/check.py --online`, which asks devnet
directly whether the signature exists and succeeded (`getSignatureStatuses`) — it printed
`PASS devnet receipt`, confirmed on devnet. For both, the buyer delta equals `-price_raw`
and the store delta `+price_raw`.

## What this does not prove

- Devnet only. It says nothing about mainnet beyond Friday's three capped espressos.
- One unit per purchase: buying N is N separately checked purchases.
- The check compares against my own pin, so a wrong pin is signed faithfully. The receipt
  proves what moved, never that I asked for the right thing.
- The recorded lane proves the code path and the refusals; it is never evidence that a
  transaction landed.
