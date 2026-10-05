# Deploying the check server

The check server holds no key and no secret: it takes an intent and a prepared answer and
returns a verdict. So deploying it is only "serve this over HTTPS".

## Run it

Locally, over stdio (a client on the same machine spawns it):

```bash
uv run python server/check_server.py
```

As a deployable HTTP server (streamable HTTP transport), the mode the Dockerfile uses:

```bash
uv run python server/check_server.py --transport streamable-http --host 0.0.0.0 --port 8000
```

It answers at `/mcp`. A platform that terminates TLS gives it a public HTTPS URL.

## Verified, locally over HTTP

Started on `127.0.0.1:8765` and driven through an MCP session (`initialize`,
`notifications/initialized`, `tools/call`). Fed case 5's pin and prepared answer:

```json
{"passed": false, "field": "quantity", "asked": 2, "found": 1,
 "reason": "quantity: asked 2, prepared 1",
 "checks": [ {"field": "program", "ok": true}, {"field": "store", "ok": true},
             {"field": "product", "ok": true}, {"field": "price_raw", "ok": true},
             {"field": "mint", "ok": true}, {"field": "quantity", "ok": false} ]}
```

Fed a private `rpc_url` (`http://127.0.0.1:8899`), it refused before fetching anything:

```json
{"passed": false, "field": "rpc_url", "asked": "a public https URL",
 "found": "http://127.0.0.1:8899",
 "reason": "refused before any fetch: private, loopback, link-local or non-https"}
```

## Deploy config in this repository

- [`Dockerfile`](../../Dockerfile): installs `uv`, syncs the project, and runs the server
  on `$PORT` over streamable HTTP. Keyless; nothing secret is configured.
- [`render.yaml`](../../render.yaml): a Render blueprint for one free web service built
  from that Dockerfile.

## Public URL

**Pending.** Deploy steps (Render; any container host works the same way):

1. In Render: **New → Blueprint**, connect this repository, apply `render.yaml`.
2. Render builds the Dockerfile and gives a public URL on `onrender.com` (HTTPS).
3. Point an MCP client at that URL, path `/mcp`, and call `check_purchase`.

The URL is filled in here once it answers. Nothing is claimed until then.

## If it goes down during the defence

Switch to the recorded answers and say so:
`GECKO_SOURCE=recorded uv run buyer "one espresso" --devnet`. The committed
`smoke-report.recorded.json` is the evidence that the same code path still refuses.
