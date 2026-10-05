# Issues

Real incidents from the build, newest first. Each one actually happened on this machine.

## 2026-10-05: "two espressos" was refused on `product`, not `quantity`

- **What I saw:** `uv run buyer --cards --recorded` printed `3/4`, and the quantity card
  read `REFUSED on product: asked 'espressos'` while the fixture expects `quantity`.
- **What was actually wrong:** `parse_intent` matched a menu item by its first word only
  when the ask contained that exact word. The menu says `Espresso`; the card asks for
  `espressos`, so no product matched and the buyer refused earlier than it should have.
- **How I found it:** the card line in the smoke output naming the field, `product`,
  against the fixture's `expected.field`, `quantity`.
- **What I changed:** product matching now treats a trailing plural `s` as the same word
  (`_same_word`). `tests/test_your_work.py::test_each_recorded_case_ends_as_expected[
  cards/quantity]` is the test that goes red if this comes back. Cards went 3/4 to 4/4.
- **What it cost:** a few minutes. No signature; nothing was signed on a product refusal.
- **Would the checks have caught it?** The refusal was correct per the code and wrong per
  the spec. No field check could catch it: the bug was in the pin, which is exactly the
  thing the checks trust. This is why "what does your receipt not prove" has the answer it
  does.

## 2026-10-05: 25 tests failed on Windows before any capstone code was written

- **What I saw:** `uv run pytest` reported `25 failed, 51 passed, 24 xfailed`. Every
  failure was in `tests/test_mainnet_wallet.py` and the mainnet lane of
  `tests/test_signer.py`, and one said
  `refusing: C:\Users\...\.config\dev3pack\mainnet-wallet.json already exists`.
- **What was actually wrong:** the tests set `HOME` to a scratch directory, but on Windows
  `Path.home()` reads `USERPROFILE` and ignores `HOME`. `buyer/signer.py:config_dir()`
  therefore resolved the real `~/.config/dev3pack/`, so the tests were not hermetic.
- **How I found it:** `HOME=/tmp/x uv run python -c "from pathlib import Path; print(Path.home())"`
  printed the real home, not `/tmp/x`. That one line explained all 25 failures.
- **What I changed:** the fixtures now monkeypatch `Path.home` (not only `HOME`), and the
  0600 file-mode assertion runs only where POSIX mode bits exist (`os.name == "posix"`;
  Windows `chmod` supports no permission bits). `uv run pytest` is green.
- **What it cost:** nothing but time. No test was weakened: the hermetic intent is the same,
  asserted on the platform that can express it.
- **Would the checks have caught it?** No. It is a test-isolation bug, not a purchase bug;
  the seven checks never ran.
