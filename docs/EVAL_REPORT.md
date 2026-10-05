# Evaluation report

Filled from a run on this machine. Numbers come from a command that printed them.

## The five cases and the trap

| # | Ask | Expected | Recorded | Devnet | Evidence |
|---|---|---|---|---|---|
| 1 | one espresso | lands, receipt reconciles | MATCH | MATCH on my own store `dev3semegn19` | [`receipts/2bjKMqbt.md`](../receipts/2bjKMqbt.md) |
| 2 | one general-admission ticket | refuse on `product` | MATCH | refused live: own store has no such product, name quoted back | `refusals/*-product.json` |
| 3 | module 3, paid in USDC | refuse on `mint` | MATCH | pending: needs class tokens | `refusals/*-mint.json` |
| 4 | tip up to 2 USDC | refuse on `price_raw` | MATCH | refused live: budget 500000, price 1000000 | `refusals/*-price-raw.json` |
| 5 | two bags of beans | refuse on `quantity` | MATCH | refused live: asked 2, prepared 1 | `refusals/*-quantity.json` |
| trap | one latte | refuse, name quoted back | MATCH | refused live on own store via `price_raw` | `refusals/*-price-raw.json` |

Command: `uv run buyer --cases --recorded` gave `6/6`; `uv run buyer --cards --recorded`
gave `4/4`. The devnet column is what actually ran on my store `dev3semegn19`
(owner `FXFmd6SD…`, buyer `UZ5CtjS5…`), not the class store: rows 2, 4, 5 and the trap
refused through real devnet calls, and row 1 landed. Row 3 needs the class lookalike token
`BRPT4Sr7…` sent to my buyer; the same `mint` check is covered by the recorded case and my
tests. The class-store live smoke (`uv run buyer --cases --devnet`, writing
`smoke-report.json`) was **deliberately skipped**: it needs the class tokens
`Eoqdd43n…` / `BRPT4Sr7…` minted to the buyer, whose authority is the instructor's, and
that lane was declined. No `smoke-report.json` is claimed; `smoke-report.recorded.json` is
the committed rollback evidence.

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

One devnet receipt is written: `receipts/2bjKMqbt.json` / `.md`, signature
`2bjKMqbtg6YKe653XB9JiPqV4PtUZBHK34n9jJgSaYCtxtE17x6sNSFH4jJZ3DUNkrkf1YAbkTcuUmftedq9BPBP`.
It is checked from outside this code with
`uv run python projects/03-the-part-that-says-no/check.py --online`, which asks devnet
directly whether the signature exists and succeeded (`getSignatureStatuses`) — it printed
`PASS devnet receipt 1 reconciled devnet receipt(s) in receipts/, confirmed on devnet`.
The buyer delta equals `-price_raw`, the store delta `+price_raw`, and `total_purchases`
went 0 to 1.

## What this does not prove

- Devnet only. It says nothing about mainnet beyond Friday's three capped espressos.
- One unit per purchase: buying N is N separately checked purchases.
- The check compares against my own pin, so a wrong pin is signed faithfully. The receipt
  proves what moved, never that I asked for the right thing.
- The recorded lane proves the code path and the refusals; it is never evidence that a
  transaction landed.
