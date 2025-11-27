# Repository Guidelines

## Project Structure & Module Organization
- Entry points: `main.py` (root) and `news_analyzer/main.py` start the PyQt5 GUI, wiring storage, collectors, and UI.
- Core package `news_analyzer/`:
  - `ui/`: Qt widgets, dialogs, settings, and the cleaning UI.
  - `collectors/`: `rss_collector.py` (feedparser + requests) and `org_collector.py` (HTML/JSON scrapers for international orgs/NewsAPI); defaults in `default_sources.py`.
  - `storage/`: PostgreSQL persistence in `news_storage.py`.
  - `llm/`: client and prompts.
  - Runtime artifacts: `data/`, `logs/`; samples under `data/news`.
- Tests (when added) should live in `tests/`.

## Build, Test, and Development Commands
- Setup venv & deps:  
  - `python3 -m venv .venv && source .venv/bin/activate`  
  - `pip install -r requirements-txt.txt` (or root `requirements.txt`).
- Run GUI: `python main.py`
- Quick syntax check: `python -m py_compile news_analyzer/**/**/*.py`
- Tests (if present): `pytest`

## Coding Style & Naming Conventions
- Python 3, PEP 8, 4-space indent; snake_case for modules/functions/vars.
- Add type hints on new/modified functions; concise docstrings.
- Use `logging` with module loggers (e.g., `news_analyzer.collectors.rss`); avoid `print`.
- Keep UI logic in `ui/`; network/storage/LLM in their modules.

## Testing Guidelines
- Framework: `pytest`; name files `test_*.py`.
- Prefer fixtures and HTTP stubs for collectors; cover RSS parsing, HTML scraping, storage persistence, and date-based cleaning/dedupe.

## Commit & Pull Request Guidelines
- Small, focused commits; conventional prefixes encouraged (`feat:`, `fix:`, `chore:`).
- PRs: purpose summary, key implementation choices, manual verification (`python main.py`), screenshots/GIFs for UI changes. Link issues and note new deps/config.

## Security & Configuration Tips
- Secrets via env vars: `LLM_API_KEY`, `LLM_API_URL`, `LLM_MODEL`, `NEWS_API_KEY`; never commit keys.
- `data/` and `logs/` may contain fetched content—scrub before sharing.
- Network calls live in collectors; keep timeouts/UAs robust. RSSHub base is configurable—swap mirrors if unstable.
