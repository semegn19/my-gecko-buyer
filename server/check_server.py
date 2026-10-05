"""Project 03's MCP server: the part that says no, served as a tool.

One tool, `check_purchase`, runs the buyer's seven field checks on a prepared purchase and
returns the verdict: whether it passed, and if not, the field that refused with both
values. It is keyless: it never loads a signer and signs nothing. Any agent can ask it
"should I sign this?" without holding the buyer's key.

The optional `rpc_url` lets a caller ask the server to re-read the store itself, which is
exactly the kind of fetch that can be pointed somewhere private, so `is_public_url` guards
it before anything is fetched.

Serve it over stdio (default) or streamable HTTP:

    uv run python server/check_server.py
    uv run python server/check_server.py --transport streamable-http --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Importable whether it is run as a script (`python server/check_server.py`) or imported
# by a test: put the repository root on the path so `from server.guard import ...` works.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.mcpserver import MCPServer  # noqa: E402

from buyer.check import check_all  # noqa: E402
from buyer.intent import IntentRecord  # noqa: E402
from buyer.prepared import Prepared  # noqa: E402
from server.guard import is_public_url  # noqa: E402

server = MCPServer(
    name="dev3pack-check",
    title="Dev3Pack purchase check",
    description=(
        "Runs the buyer's seven field checks on a prepared purchase and returns the "
        "verdict. Keyless: it never loads a signer and never signs."
    ),
)


@server.tool()
def check_purchase(
    intent: dict[str, Any],
    prepared_answer: dict[str, Any],
    rpc_url: str | None = None,
) -> dict[str, Any]:
    """Compare a prepared purchase with the pinned intent, field by field.

    `intent` is an `intents/<file>.json` record; `prepared_answer` is a `prepare_purchase`
    answer. Returns `passed`, the `field` that refused (if any), and both `asked` and
    `found`. A private or non-https `rpc_url` is refused before anything is fetched.
    """
    if rpc_url is not None and not is_public_url(rpc_url):
        return {
            "passed": False,
            "field": "rpc_url",
            "asked": "a public https URL",
            "found": rpc_url,
            "reason": "refused before any fetch: private, loopback, link-local or non-https",
        }

    record = IntentRecord(**intent)
    prepared = Prepared.from_answer(prepared_answer)
    verdict = check_all(record, prepared)

    if verdict.unwritten is not None:
        return {
            "passed": False,
            "field": verdict.unwritten.what,
            "asked": None,
            "found": None,
            "reason": str(verdict.unwritten),
        }

    checks = [
        {"field": r.field, "ok": r.ok, "asked": r.asked, "found": r.found, "where": r.where}
        for r in verdict.results
    ]
    if verdict.refusal is not None:
        refusal = verdict.refusal
        return {
            "passed": False,
            "field": refusal.field,
            "asked": refusal.asked,
            "found": refusal.found,
            "reason": refusal.line(),
            "checks": checks,
        }
    return {
        "passed": True,
        "field": None,
        "asked": None,
        "found": None,
        "reason": "all seven fields agree with the pinned intent",
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_server", description="The buyer's check, served as one MCP tool."
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="stdio for a local client, streamable-http to deploy",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    if args.transport == "streamable-http":
        server.run("streamable-http", host=args.host, port=args.port)
    else:
        server.run(args.transport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
