.PHONY: help backend-lint backend-test backend-build frontend-lint frontend-test frontend-build ci-local backend-dev frontend-dev migrate db-revision db-downgrade

help:
	@echo "Development commands:"
	@echo "  make backend-dev      Start the FastAPI backend server with auto-reload"
	@echo "  make frontend-dev     Start the Vite frontend server"
	@echo "  make migrate          Run Alembic database migrations to latest (upgrade head)"
	@echo "  make db-revision m=\"msg\" Create a new Alembic migration revision"
	@echo "  make db-downgrade     Downgrade the database by 1 revision"
	@echo ""
	@echo "Local CI helpers (mirror what .github/workflows/ci.yml runs)"
	@echo "Targets:"
	@echo "  make backend-lint     Run Ruff against backend/"
	@echo "  make backend-test     Run Pytest against backend/ (Docker required for testcontainers)"
	@echo "  make backend-build    Build the backend wheel via 'python -m build'"
	@echo "  make frontend-lint    Run ESLint against frontend/"
	@echo "  make frontend-test    Run Playwright E2E (REQUIRES the Vite dev server on :5173)"
	@echo "  make frontend-build   Build the frontend production bundle"
	@echo "  make ci-local         Run all non-E2E checks; prints how to run E2E manually"

backend-dev:
	cd backend && venv/bin/uvicorn app.main:app --reload

frontend-dev:
	cd frontend && npm run dev

migrate:
	cd backend && venv/bin/alembic upgrade head

db-revision:
	@if [ -z "$(m)" ]; then echo "Error: Please provide a message using m=\"your message\""; exit 1; fi
	cd backend && venv/bin/alembic revision --autogenerate -m "$(m)"

db-downgrade:
	cd backend && venv/bin/alembic downgrade -1

backend-lint:
	cd backend && venv/bin/ruff check .

backend-test:
	cd backend && venv/bin/pytest

backend-build:
	cd backend && venv/bin/pip install --quiet build && venv/bin/python -m build --wheel

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npx playwright test

frontend-build:
	cd frontend && npm run build

ci-local: backend-lint backend-build frontend-lint frontend-build backend-test
	@echo ""
	@echo "All non-E2E checks passed."
	@echo "To run E2E: in another terminal run 'cd frontend && npm run dev', then run 'make frontend-test'."
