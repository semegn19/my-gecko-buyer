# The buyer signs only when seven fields match the pinned intent

## Status and date

accepted, 2026-10-05

## Context

My buyer holds a key that can pay. Gecko prepares the bytes; the buyer signs them. A wrong
transaction that lands looks exactly like a right one, and by the time it is visible the
money has moved. A spending cap sees one number; it does not see the wrong store, the VIP
ticket when a general-admission ticket was asked for, a token called USDC at another
address, or a byte changed between the signer and the network. So the interesting code is
the comparison that runs **before** any signature, and refuses when it disagrees.

## Decision

Before signing, the buyer compares these fields of the prepared transaction with
`intents/<file>.json` and refuses on the first mismatch, naming the field and both values:

| Field | Compared how | Why this one |
|---|---|---|
| program | address equality, and no other program riding along | a purchase aimed at a lookalike program must not sign; `letmebuy.program_id()` comes from the vendored IDL, not from Gecko |
| store | address, derived from `['receipts', name]`, never a constant | `list_stores` filters by substring, so a similar name can return the wrong account; the address is recomputed here |
| product | exact name equality | "VIP ticket" is not "General admission ticket", and a name is never obeyed, only compared |
| price_raw | integer, at or under the pinned budget; `None` refuses | the amount that leaves the buyer is the thing a cap exists to bound; an unreported amount cannot be shown to be within it |
| mint | address equality, never the symbol | a token called USDC at another address is another token; the buyer cannot pay with it where the price is in a different one |
| quantity | integer equality | `prepare_purchase` prepares one unit; asked 2, prepared 1 is a refusal, not a silent downgrade |
| destination | the store authority's token account for the pinned mint, derived with `letmebuy.token_account` | the money must go to the store's own account; the destination is derived here, never copied from the answer being checked |
| signed bytes | `verify_signed_transaction` before `submit_transaction` | a signer will sign substituted bytes; this catches a changed byte while it is still free, before a broadcast |

The pins themselves (`parse_intent`) are written to `intents/` **before** `prepare_purchase`
is called, and the runner stops the run if the pin is not on disk first.

## What this forbids

- Signing on a partial match: `check_all` stops at the first disagreement.
- Retrying a refusal unchanged: a refusal writes `refusals/<stamp>-<field>.json` and signs
  nothing; the fix is to change the request, not to re-run it.
- Signing without a passing simulation: a `prepare_purchase` answer with `status != "pass"`
  never reaches the signer, even if every field matched.
- Re-signing expired bytes: past `last_valid_block_height` the signer refuses on `blockhash`;
  the purchase is prepared again instead.

## What I left out, and why

I do not check the fee payer's SOL balance or the token account's rent. Those are
properties of the wallet, not of the order; a shortfall shows up as a failed simulation
(`receipt-failed`) before anything is signed, so a separate check would duplicate Gecko's
work without guarding a field a buyer actually chose.

## What would reverse this

The decision to check `price_raw` and `mint` here would be reversed if
`verify_signed_transaction` were shown to bind the simulated effect (amount and mint) as
well as the bytes: then my own price and mint checks would be duplicate work, and I would
drop them and rely on the verified effect instead. The decision to refuse a `None` price
would be reversed if the simulation ever legitimately reported no token movement for a
purchase — which it does not for `let_me_buy`.

## What this does not prove

That my pin was right. The buyer faithfully signs a wrong request. And it proves nothing
beyond one unit per purchase: buying N means N separately checked purchases.
