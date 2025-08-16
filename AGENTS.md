# Repository Guidelines

This repository contains a small Flask-based web app for order analytics with Excel/CSV ingestion and export. Use this guide to contribute consistently and safely.

## Project Structure & Module Organization
- `app.py`: Flask server (port 4004), SKU metrics endpoint and views.
- `compute_logic.py`: Core metrics engine (file parsing, date filtering, rates).
- `compute_province_metrics.py`: Province-level breakdown and workbook builder.
- `templates/` and `static/`: UI templates and styles.
- `start.sh` / `stop.sh`: Local run helpers (Linux/macOS). `start.bat` for Windows.
- `requirements.txt`: Runtime dependencies.

## Build, Test, and Development Commands
- Create venv: `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
- Install deps: `pip install -r requirements.txt`.
- Run app: `bash start.sh` (auto-creates `.venv` and installs deps) or `python app.py`.
- Stop app: `bash stop.sh` (uses `app.pid`).
- Province CLI (optional): `python compute_province_metrics.py` to generate `省份指标分析结果.xlsx`.

## Coding Style & Naming Conventions
- Python 3, PEP 8, 4-space indentation, UTF-8.
- Functions/variables: `snake_case`; constants: `UPPER_SNAKE_CASE`; modules/files: `snake_case.py`.
- Prefer pure functions in `compute_*` modules; keep Flask routes thin.
- Optional tools: `pip install black ruff`; format with `black .` and lint with `ruff check .`.

## Testing Guidelines
- Current repo has no automated tests. Add `pytest` when contributing logic changes.
- Test files: place under `tests/`, name `test_*.py`. Example: `tests/test_compute_logic.py`.
- Quick manual check: run `bash start.sh`, open `http://localhost:4004`, upload sample `.xlsx/.csv`, verify result table and downloadable workbook.

## Commit & Pull Request Guidelines
- Use Conventional Commit prefixes seen in history: `feat:`, `fix:`, `chore:`, `refactor:`, `style:`, `docs:`, `ui:` (e.g., `feat(results): add date filter`).
- PRs must include: problem statement, concise summary of changes, screenshots/GIFs for UI changes, reproduction/testing steps, and linked issues.
- Keep diffs focused; include migration notes if changing file headers/columns.

## Security & Configuration Tips
- Secret key: replace the hardcoded `app.secret_key` with an environment value in production. Example: `export FLASK_SECRET_KEY='...'` and read it in `app.py`.
- Port: defaults to `4004`; adjust via env or script if needed.
