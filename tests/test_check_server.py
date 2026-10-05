"""Project 03's guard and check server, offline: no network, no key."""

from __future__ import annotations

from typing import Any

import pytest
from conftest import fixture

from server.check_server import check_purchase
from server.guard import is_public_url

AUTHORITY = "Dt8quRFWgTMrrDgVa4GGFRJWksncskbs1tpYAQHkEPwJ"
MUST_REFUSE = [
    "http://127.0.0.1:8899",
    "https://169.254.169.254/",
    "https://10.0.0.8/",
    "file:///etc/passwd",
    "https://localhost/",
]


@pytest.mark.parametrize("url", MUST_REFUSE)
def test_the_guard_refuses_private_loopback_and_non_https(url: str) -> None:
    assert is_public_url(url) is False


def test_the_guard_accepts_a_public_https_literal() -> None:
    # A literal public IP needs no DNS, so this holds even with the network blocked.
    assert is_public_url("https://8.8.8.8/") is True


def case5_intent(**overrides: Any) -> dict[str, Any]:
    context = fixture("cases/5-beans")["context"]
    intent: dict[str, Any] = {
        "ask": "two bags of beans",
        "store": context["store"],
        "product": "Beans",
        "quantity": 2,
        "budget_raw": context["budget_raw"],
        "mint": context["pay_mint"],
        "buyer": context["buyer"],
        "network": context["network"],
        "store_authority": AUTHORITY,
        "menu_price_raw": 1_500_000,
    }
    intent.update(overrides)
    return intent


def test_the_server_refuses_case_five_on_quantity_keyless() -> None:
    prepared = fixture("cases/5-beans")["calls"]["prepare_purchase"]
    verdict = check_purchase(case5_intent(), prepared)
    assert verdict["passed"] is False
    assert verdict["field"] == "quantity"
    assert verdict["asked"] == 2 and verdict["found"] == 1


def test_the_server_refuses_a_private_rpc_url_before_anything_is_fetched() -> None:
    prepared = fixture("cases/5-beans")["calls"]["prepare_purchase"]
    verdict = check_purchase(case5_intent(), prepared, rpc_url="http://127.0.0.1:8899")
    assert verdict["passed"] is False and verdict["field"] == "rpc_url"


def test_the_server_passes_an_agreeing_purchase() -> None:
    case = fixture("cases/1-espresso")
    context = case["context"]
    intent = {
        "ask": "one espresso",
        "store": context["store"],
        "product": "Espresso",
        "quantity": 1,
        "budget_raw": context["budget_raw"],
        "mint": context["pay_mint"],
        "buyer": context["buyer"],
        "network": context["network"],
        "store_authority": AUTHORITY,
        "menu_price_raw": 1_000_000,
    }
    verdict = check_purchase(intent, case["calls"]["prepare_purchase"])
    assert verdict["passed"] is True and verdict["field"] is None
