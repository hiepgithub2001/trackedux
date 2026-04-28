.PHONY: help backend-lint backend-test backend-build frontend-lint frontend-test frontend-build ci-local

help:
	@echo "Local CI helpers (mirror what .github/workflows/ci.yml runs)"
	@echo ""
	@echo "Targets:"
	@echo "  make backend-lint     Run Ruff against backend/"
	@echo "  make backend-test     Run Pytest against backend/ (Docker required for testcontainers)"
	@echo "  make backend-build    Build the backend wheel via 'python -m build'"
	@echo "  make frontend-lint    Run ESLint against frontend/"
	@echo "  make frontend-test    Run Playwright E2E (REQUIRES the Vite dev server on :5173)"
	@echo "  make frontend-build   Build the frontend production bundle"
	@echo "  make ci-local         Run all non-E2E checks; prints how to run E2E manually"

backend-lint:
	cd backend && ruff check .

backend-test:
	cd backend && pytest

backend-build:
	cd backend && pip install --quiet build && python -m build --wheel

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
