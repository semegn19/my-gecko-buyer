"""The part that says no: seven fields of the prepared purchase against the pinned intent.

Each check returns a `FieldResult`. A refusal names the field and BOTH values: what was
asked (from the pin) and what was found (in the prepared bytes). "Cannot buy" is not a
refusal; "price_raw: asked at most 2000000, prepared 3000000" is.

Two checks are written as worked examples: `check_program` and `check_store`. The other
five are yours. Until you write one it raises `NotYetWritten`, and `check_all` treats that
as a refusal: an unwritten check never lets a signature through.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from solders.pubkey import Pubkey

from . import letmebuy

if TYPE_CHECKING:
    from .intent import IntentRecord
    from .prepared import Prepared


class NotYetWritten(NotImplementedError):
    """A TODO the student has not written yet. Never caught as a pass."""

    def __init__(self, what: str, hint: str) -> None:
        self.what, self.hint = what, hint
        super().__init__(f"{what} is not written yet ({hint})")


@dataclass(frozen=True)
class FieldResult:
    field: str
    ok: bool
    asked: Any
    found: Any
    #: where `found` came from: "prepared", "menu", "signer", "verify"
    where: str = "prepared"
    note: str = ""

    def line(self) -> str:
        if self.ok:
            return f"{self.field}: {self.found!r}"
        text = f"{self.field}: asked {self.asked!r}, {self.where} {self.found!r}"
        return f"{text} ({self.note})" if self.note else text


class Refused(Exception):
    """Raised from any step that decides not to go on. Carries the field that decided."""

    def __init__(self, result: FieldResult) -> None:
        self.result = result
        super().__init__(result.line())


def refuse(
    field_name: str, asked: Any, found: Any, where: str = "prepared", note: str = ""
) -> FieldResult:
    return FieldResult(field_name, False, asked, found, where, note)


def agree(field_name: str, value: Any) -> FieldResult:
    return FieldResult(field_name, True, value, value)


# --- worked example 1 ---------------------------------------------------------------------


def check_program(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    """The bytes call the store program, and nothing else that could move money.

    Compared as an address. `letmebuy.program_id()` comes from the IDL shipped in this
    repo, not from Gecko's answer: the thing being checked never supplies the answer.
    """
    expected = str(letmebuy.program_id())
    if prepared.program != expected:
        return refuse("program", expected, prepared.program)
    if prepared.programs != (expected,):
        return refuse(
            "program", [expected], list(prepared.programs), note="an extra program is called"
        )
    return agree("program", expected)


# --- worked example 2 ---------------------------------------------------------------------


def check_store(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    """The store account is the one DERIVED from the pinned store name.

    Never a constant, and never the address Gecko reported: PDA(['receipts', name]) is
    computed here, from the name the person asked for. A store with a similar name, or a
    swapped account, gives a different address.
    """
    expected = str(letmebuy.store_address(intent.store))
    if prepared.store != expected:
        return refuse("store", f"{intent.store} at {expected}", prepared.store)
    return agree("store", expected)


# --- yours --------------------------------------------------------------------------------


def check_product(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    """The product in the bytes is the pinned product, by its exact name.

    Use case 2 ("one general-admission ticket") refuses here when the prepared purchase is
    the VIP ticket. Names are compared whole: a different name is a different product, and
    an instruction inside a name changes nothing (see the ADR).
    """
    if prepared.product != intent.product:
        return refuse("product", intent.product, prepared.product)
    return agree("product", prepared.product)


def check_price(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    """The amount leaving the buyer is at or under the pinned budget, in raw units.

    Whole numbers of the smallest unit on both sides; no float touches a price. A
    simulation that reports no amount at all is refused, not waved through: an unknown
    price cannot be shown to be within a budget. Use case 4 ("tip up to 2 USDC") refuses a
    3 USDC tip and names both numbers.
    """
    price = prepared.price_raw
    if price is None:
        return refuse(
            "price_raw",
            f"at most {intent.budget_raw}",
            None,
            note="the simulation reported no amount, so there is nothing to compare",
        )
    if price > intent.budget_raw:
        return refuse(
            "price_raw",
            f"at most {intent.budget_raw}",
            price,
            note=f"for the pinned product {intent.product!r}",
        )
    return agree("price_raw", price)


def check_mint(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    """The token paid is the pinned mint, compared as an ADDRESS.

    A token called USDC at another address is another token: use case 3 refuses exactly
    that. There is no symbol anywhere in `Prepared`, on purpose.
    """
    if prepared.mint != intent.mint:
        return refuse("mint", intent.mint, prepared.mint)
    return agree("mint", prepared.mint)


def check_quantity(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    """The number of purchases in the bytes is the number asked for.

    `prepare_purchase` prepares one unit, so "two bags of beans" is refused: asked 2,
    prepared 1. Refusing is the honest answer; buying one is not what was asked for.
    """
    if prepared.quantity != intent.quantity:
        return refuse("quantity", intent.quantity, prepared.quantity)
    return agree("quantity", prepared.quantity)


def check_destination(intent: IntentRecord, prepared: Prepared) -> FieldResult:
    """The money goes to the store authority's token account for the pinned mint.

    The destination is derived here, with `letmebuy.token_account`, from the authority the
    menu showed when the intent was pinned and the pinned mint. It is never copied from
    Gecko's answer: the thing being checked does not supply the answer.
    """
    expected = str(
        letmebuy.token_account(
            Pubkey.from_string(intent.store_authority), Pubkey.from_string(intent.mint)
        )
    )
    if prepared.destination != expected:
        return refuse("destination", expected, prepared.destination)
    return agree("destination", expected)


#: The order is part of the design: cheap, structural checks first.
CHECKS: tuple[Callable[[IntentRecord, Prepared], FieldResult], ...] = (
    check_program,
    check_store,
    check_product,
    check_price,
    check_mint,
    check_quantity,
    check_destination,
)


@dataclass
class Verdict:
    results: list[FieldResult] = field(default_factory=list)
    refusal: FieldResult | None = None
    unwritten: NotYetWritten | None = None

    @property
    def passed(self) -> bool:
        return self.refusal is None and self.unwritten is None


def check_all(intent: IntentRecord, prepared: Prepared) -> Verdict:
    """Run every check in order and stop at the first that does not agree."""
    verdict = Verdict()
    for check in CHECKS:
        try:
            result = check(intent, prepared)
        except NotYetWritten as todo:
            verdict.unwritten = todo
            return verdict
        verdict.results.append(result)
        if not result.ok:
            verdict.refusal = result
            return verdict
    return verdict
