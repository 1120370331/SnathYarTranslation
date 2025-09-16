# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: FastAPI service. Key paths: `src/main.py` (app), `src/api/` (routes), `src/services/` (business logic), `src/db.py` (SQLAlchemy), `tests/{contract,integration}/`.
- `frontend/`: Vite + React + TypeScript UI. Entry: `src/main.tsx`, assets under `src/` and `index.css`.
- `scripts/`: Repo automation (feature scaffolding, plan helpers). See `create-new-feature.sh`, `setup-plan.sh`.
- `specs/`: Feature specs, plans, and contracts; `templates/`: authoring templates.
- Root helpers: `start.sh`/`start.bat` (run full stack), `shathyar.db`, `shasiyaer.csv`.

## Build, Test, and Development Commands
- Backend setup: `cd backend && python -m venv venv && .\venv\Scripts\Activate.ps1` (PowerShell) then `pip install -e .[dev]`.
- Run API (dev): `cd backend && uvicorn src.main:app --reload --host 127.0.0.1 --port 8000`.
- Frontend dev: `cd frontend && npm install && npm run dev`.
- Full stack: Windows `start.bat`; Unix `./start.sh` (opens http://localhost:5173).
- Backend tests: `cd backend && pytest` (markers: `-m "unit or integration or contract"`).
- Backend quality: `cd backend && black src tests && isort src tests && flake8 src tests && mypy src`.
- Frontend tests/quality: `cd frontend && npm run test` | `npm run test:coverage` | `npm run lint` | `npm run type-check` | `npm run build`.

## Coding Style & Naming Conventions
- Python: 4‑space indent, type hints in non‑test code. Formatting via `black` (88 cols) and `isort` (profile=black). Lint with `flake8`; types via `mypy` (strict).
- TypeScript/React: follow ESLint rules; camelCase for vars/functions, PascalCase for components; `.tsx` for components, `.ts` for utilities.

## Testing Guidelines
- Backend: `pytest` with coverage configured in `pyproject.toml`; place contract tests in `tests/contract/`, integration in `tests/integration/`.
- Frontend: `vitest` + Testing Library; colocate unit tests near components or under `src/__tests__/`.

## Commit & Pull Request Guidelines
- Commits: Conventional Commits preferred (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`). Use imperative mood and reference issues (e.g., `#123`).
- PRs: include description, linked issues, test plan (commands run), and screenshots/recordings for UI changes; for API changes, add curl/example responses.
- Pre‑merge: run backend linters/tests and frontend lint/type‑check/tests.

## Security & Configuration Tips
- Do not commit secrets. Configure providers via environment variables; override DB with `SHATHYAR_DB_URL`. Rate‑limit and quota settings live under `backend/src/services/`.
