# Repository Guidelines

## Project Structure & Module Organization
- `app.py` is the Streamlit entry point and UI flow.
- `src/` contains core logic: `models.py` (Pydantic data + parsing), `validators.py` (RUT/patente/email/tel), `autotramite.py` (Playwright automation), `config.py` (selectors + settings), `logging_utils.py` (PII masking).
- `tests/` holds pytest tests (currently `tests/test_validators.py`).
- `docs/` includes migration notes and test data; `docs/test.md` is used by the preview script.
- `test_preview.py` runs a dry-run Playwright preview and writes screenshots to `screenshots/`.

## Build, Test, and Development Commands
- `python -m venv .venv` creates a virtual environment.
- `.venv\Scripts\activate` activates it on Windows.
- `pip install -r requirements.txt` installs dependencies.
- `playwright install chromium` installs the browser used by automation.
- `streamlit run app.py` starts the app at `http://localhost:8501`.
- `python test_preview.py` runs the dry-run preview flow without registering a contract.
- `pytest` runs unit tests; `pytest -v` for verbose.
- `pytest --cov=src tests/` runs tests with coverage.

## Coding Style & Naming Conventions
- Use 4-space indentation and Python 3.10+ syntax with type hints as seen in `src/`.
- Follow snake_case for functions/variables and PascalCase for classes (e.g., `ContratoData`, `crear_contrato_autotramite`).
- Keep domain naming in Spanish to match existing APIs and UI fields.
- Centralize CSS selectors and timeouts in `src/config.py`; avoid hard-coding them elsewhere.

## Testing Guidelines
- Tests live in `tests/` and follow `test_*.py` naming with `Test*` classes and `test_*` methods.
- Prefer `python test_preview.py` when validating Playwright flows; it uses `docs/test.md` and does not register contracts.
- Add or update tests when changing validators or parsing rules.

## Commit & Pull Request Guidelines
- This checkout has no Git history; use concise, imperative commit subjects (example: `Add RUT edge-case validation`).
- PRs should describe the change, list test commands run, and include Streamlit screenshots when UI changes are involved.
- Update `docs/README.md` or `INSTRUCCIONES_TEST.md` when workflows or commands change.

## Security & Configuration Tips
- Store credentials only in `.env`; never commit real values.
- Use `PLAYWRIGHT_HEADLESS=False` and `PLAYWRIGHT_SLOW_MO=1000` for debugging.
- Logs can contain sensitive data; rely on `logging_utils.py` masking and avoid sharing raw logs.
