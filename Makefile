.PHONY: help bootstrap dev dev-api dev-web check test clean

help:  ## Show this help
	@awk 'BEGIN{FS=":.*## "} /^[a-z][a-zA-Z_-]+:.*## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap:  ## Install api + web dependencies
	cd api && uv pip install -e .
	cd web && bun install

dev:  ## Run api (:8000) and web (:5173) in parallel — Ctrl+C kills both
	@(cd api && uvicorn app.main:app --reload --port 8000) & \
	 (cd web && bun run dev) & \
	 wait

dev-api:  ## Run only the api
	cd api && uvicorn app.main:app --reload --port 8000

dev-web:  ## Run only the web frontend
	cd web && bun run dev

check:  ## Typecheck both sides
	cd api && python -m py_compile $$(find app -name '*.py')
	cd web && bun run typecheck

clean:  ## Remove build artifacts and caches
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name dist -o -name .vite \) -exec rm -rf {} +
	rm -f web/*.tsbuildinfo
