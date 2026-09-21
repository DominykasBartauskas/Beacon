.DEFAULT_GOAL := help
.PHONY: help install api-install spa-install dev-api dev-spa test typecheck build check generate-api clean

help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: api-install spa-install ## Install API and SPA dependencies

api-install: ## Install API dependencies (uv)
	cd api && uv sync --group dev

spa-install: ## Install SPA dependencies (pnpm)
	cd spa && pnpm install

dev-api: ## Run the API on http://localhost:8100
	cd api && uv run fastapi dev src/beacon_api/main.py --port 8100

dev-spa: ## Run the SPA on http://localhost:5180
	cd spa && pnpm dev

test: ## Run the API test suite
	cd api && uv run pytest

typecheck: ## Typecheck the SPA
	cd spa && pnpm typecheck

build: ## Build the SPA
	cd spa && pnpm build

generate-api: ## Regenerate SPA API types (requires the API running on :8100)
	cd spa && pnpm generate:api

check: test typecheck build ## Run every check

clean: ## Remove build output and caches
	rm -rf spa/dist
	find api -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf api/.pytest_cache
