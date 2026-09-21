# Beacon

Beacon is a small local-news dashboard starter. It deliberately has no authentication, database, scraper, or deployment setup yet.

## Layout

- `api/` — FastAPI service and its typed API models, managed with `uv`.
- `spa/` — React + TypeScript dashboard, managed with `pnpm`.

The SPA consumes only the API. Its TypeScript definitions are generated from FastAPI's OpenAPI schema, so the boundary stays explicit.

## Run locally

Use two terminals:

```sh
cd api
uv sync --group dev
uv run fastapi dev src/beacon_api/main.py --port 8100
```

```sh
cd spa
pnpm install
pnpm dev
```

Open `http://localhost:5180`. Vite proxies `/api` requests to the backend. The API is also available at `http://localhost:8100`, with interactive documentation at `/docs`.

## API contract workflow

The API exposes its contract at `/openapi.json`. After changing typed endpoint models, start the API and refresh the SPA definitions:

```sh
cd spa
pnpm generate:api
pnpm typecheck
```

Generated definitions live at `spa/src/api/openapi.d.ts` and should be committed with the related API change.

## Checks

```sh
cd api && uv run pytest
cd spa && pnpm typecheck && pnpm build
```

## Configuration

`BEACON_CORS_ORIGINS` accepts a JSON list of allowed browser origins. It defaults to `["http://localhost:5180"]` for local development.
