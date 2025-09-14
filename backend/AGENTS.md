> Note: The canonical contributor guide lives at the repo root: [AGENTS.md](../AGENTS.md).

# Repository Guidelines

## Project Structure & Modules
- `src/main.py`: FastAPI app, middleware, and router wiring.
- `src/api/`: HTTP route handlers (e.g., `translate.py`, `dictionary.py`, `session.py`).
- `src/services/`: Core services (`ai_client.py`, `shathyar_translator.py`, `rate_limiter.py`, `dictionary_reader.py`).
- `src/models/`: Domain models and persistence helpers.
- `scripts/`: Utilities like `scripts/init_db.py` (SQLite schema + dictionary import).
- `tests/`: `contract/` and `integration/` suites under `tests/`.

## Build, Test, and Development
- Setup (PowerShell): `python -m venv .venv; . .venv/Scripts/Activate.ps1; pip install -U pip; pip install -e .[dev]`
- Run API (dev): `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`
- Initialize DB: `python scripts/init_db.py --db-path shathyar.db --csv-path data/shasiyaer.csv`
- Tests (pytest + coverage configured in `pyproject.toml`): `pytest`
  - By marker: `pytest -m "contract or integration"`
- Lint/format/type-check: `black src tests && isort src tests && flake8 src tests && mypy src`

## Coding Style & Naming
- Python 3.11, 4-space indent, type hints required in non-test code.
- Formatting: `black` (line length 88) + `isort` (profile=black).
- Linting: `flake8`; Type checking: `mypy` (strict settings in `pyproject.toml`).
- Naming: snake_case for files/functions, PascalCase for classes; tests named `test_*.py`.

## Testing Guidelines
- Framework: `pytest`, `pytest-asyncio`, `pytest-cov`; coverage runs by default.
- Layout: place API contract tests in `tests/contract/`, integration in `tests/integration/`.
- Markers available: `unit`, `integration`, `contract`, `slow`.
- Add tests alongside new routes/services; prefer httpx-based API tests and service-level tests.

## Commit & Pull Requests
- Messages: imperative present; prefer Conventional Commits (e.g., `feat:`, `fix:`, `refactor:`, `test:`, `docs:`). Reference issues (e.g., `#123`).
- PRs must include: clear description, linked issues, test plan (commands run), and examples (e.g., curl or response snippets) for API changes.
- CI etiquette: run `black`, `isort`, `flake8`, `mypy`, and `pytest` locally before opening the PR.

## Security & Configuration
- Never commit secrets. Keep AI/provider keys outside the repo (env/secret manager) and pass into service wiring (see `src/services/ai_client.py`).
- Rate limits and quotas live in services; avoid hard-coding sensitive values in code.
