# Repository Guidelines

## Project Structure & Module Organization
- Entry points: `main.py` (root) and `news_analyzer/main.py` launch the PyQt5 GUI, wiring storage, collectors, and the main window.
- Core package: `news_analyzer/`
  - `ui/`: Qt widgets (main window, panels, dialogs, settings).
  - `collectors/`: `rss_collector.py` (feedparser + requests) and `org_collector.py` (HTML/JSON scrapers for IMF/World Bank/OECD/WTO/UNCTAD/ITU); default RSS sources in `default_sources.py`.
  - `storage/`: PostgreSQL persistence in `news_storage.py`.
  - `llm/`: API client and prompts.
  - `data/`, `logs/`: runtime artifacts and samples.
- Planned tests belong in `tests/` (not yet present).

## Build, Test, and Development Commands
- Create venv & install deps:  
  - `python3 -m venv .venv && source .venv/bin/activate`  
  - `pip install -r requirements-txt.txt` (or `requirements.txt` in root).
- Run the GUI: `python main.py`
- Quick syntax check: `python -m py_compile news_analyzer/**/**/*.py`
- (When added) run tests: `pytest`

## Coding Style & Naming Conventions
- Python 3, PEP 8, 4-space indentation; snake_case for functions, variables, and files.
- Prefer type hints on new/modified functions; concise docstrings.
- Use `logging` (module-level loggers like `news_analyzer.collectors.rss`), avoid `print`.
- UI logic stays in `ui/`; network/storage logic stays in collectors/storage.

## Testing Guidelines
- Framework: `pytest` (add to `tests/`).
- Name tests `test_*.py`; prefer fixture-driven tests for collectors and to stub HTTP calls.
- Aim to cover parsing paths (RSS feedparser, HTML scrapers) and storage interactions.

## Commit & Pull Request Guidelines
- Use small, focused commits; conventional prefixes encouraged (`feat:`, `fix:`, `chore:`).
- PRs should include: purpose summary, notable implementation choices, manual verification steps (e.g., `python main.py`), and screenshots/GIFs for UI changes. Link related issues and call out new dependencies or setup steps.

## Security & Configuration Tips
- Provide LLM credentials via env vars: `LLM_API_KEY`, `LLM_API_URL`, `LLM_MODEL`; never commit secrets.
- Runtime `data/` and `logs/` may contain fetched content—scrub before sharing.
- Network calls live in `collectors/rss_collector.py` and `collectors/org_collector.py`; keep timeouts and handle failures with logged errors, not crashes.
