# Beacon

Local-news dashboard starter: a FastAPI service and a React SPA that consumes it.
There is no auth, database, scraper, or deployment setup yet — data in `api/src/beacon_api/data.py` is static.

## Project structure

| Path | Contents |
| --- | --- |
| `api/` | FastAPI backend (`beacon_api` package under `src/`), managed with `uv` |
| `api/src/beacon_api/main.py` | App setup, CORS, and all route handlers |
| `api/src/beacon_api/models.py` | Pydantic request/response models — the API contract |
| `api/src/beacon_api/config.py` | `Settings` read from `BEACON_*` environment variables |
| `api/tests/` | pytest suite |
| `Makefile` | Entry point for every common command |
| `spa/` | React + TypeScript dashboard, managed with `pnpm` |
| `spa/src/api/openapi.d.ts` | Generated from the API's OpenAPI schema — never edit by hand |
| `spa/src/api/client.ts` | Thin fetch wrapper; the only place that talks to the API |

## Commands

Run `make` targets from the repository root; `make help` lists them all.

| Target | Does |
| --- | --- |
| `make install` | Install API (`uv sync --group dev`) and SPA (`pnpm install`) dependencies |
| `make dev-api` | Run the API on http://localhost:8100 |
| `make dev-spa` | Run the SPA on http://localhost:5180 (proxies `/api` to :8100) |
| `make test` | API test suite (`pytest`) |
| `make typecheck` | SPA typecheck |
| `make build` | SPA production build |
| `make generate-api` | Regenerate `spa/src/api/openapi.d.ts` (needs the API running) |
| `make check` | `test` + `typecheck` + `build` |

`dev-api` and `dev-spa` are long-running; use two terminals.

Underneath, every target is `uv` for Python work and `pnpm` for frontend work. When running a
command directly instead of through `make`, use those tools — never `pip`, `python -m`, `npm`, or
`yarn`. New shared commands belong in the `Makefile` alongside the existing targets.

## Conventions

### API

- Routes live under `/api/v1/...` and declare `response_model` plus a `tags` entry.
- Handlers are `async def` and annotate their return type with a model from `models.py`.
- Every response shape is a Pydantic model in `models.py`; do not return bare dicts.
- New configuration goes on `Settings` as a typed field with a default, read via `get_settings()`.

### SPA

- Types come from `components['schemas'][...]` in the generated `openapi.d.ts`; do not hand-write API types.
- All network calls go through `beaconApi` in `spa/src/api/client.ts`.
- Requests use relative `/api/...` paths so the Vite proxy handles them in development.

## Changing the API contract

The API/SPA boundary is the OpenAPI schema. When endpoint models change:

1. Update `api/src/beacon_api/models.py` and the handler.
2. Add or update the matching test in `api/tests/test_main.py`.
3. With `make dev-api` running, run `make generate-api` and `make typecheck`.
4. Commit the regenerated `spa/src/api/openapi.d.ts` with the API change in the same commit.

## Git

- Write commit messages in Conventional Commits format (`type(scope): summary`) before pushing.
- Clean up any temporary task sessions or scratch branches you create once the work is genuinely
  complete, unless the user asks to keep them.

## Before finishing a change

- Touched `api/`: `make test`
- Touched `spa/`: `make typecheck && make build`
- Touched endpoint models: `make check`, plus a regenerated `openapi.d.ts`
