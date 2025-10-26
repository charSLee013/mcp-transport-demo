# Repository Guidelines

## Project Structure & Module Organization
Core SDK code lives in `src/mcp` (clients, servers, shared primitives, typed exports in `types.py`). Tests mirror those packages under `tests/`, while docs live in `docs/` and reference implementations land in `examples/clients` and `examples/servers`, with site configuration tracked in `mkdocs.yml`.

## Build, Test, and Development Commands
Install dependencies with `uv sync --frozen --all-extras --dev`. Run `uv run pytest` for the suite, adding `-k` or `-n auto` when iterating locally. Lint and format via `uv run ruff check .` and `uv run ruff format .`, then confirm types with `uv run pyright`. Refresh README snippets through `uv run scripts/update_readme_snippets.py`, and smoke-test the CLI using `uv run mcp ...`.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and a 120-column limit enforced by Ruff. Use `snake_case` for modules, functions, and coroutines; reserve `PascalCase` for classes and `SCREAMING_SNAKE_CASE` for constants or environment keys. Public APIs ship with type hints and concise docstrings, while Ruff manages import ordering and Pyright guards against unused symbols.

## Testing Guidelines
Add or update `pytest` modules under the matching path in `tests/` using the `test_*.py` naming pattern. Cover success, failure, edge, and async paths instead of duplicating implementation details. Because `xfail_strict` is enabled, clear temporary xfails before submission and scale from `uv run pytest tests/server/test_my_feature.py` to the full suite once green.

## Commit & Pull Request Guidelines
Structure commits with the conventional prefixes used here (`feat:`, `fix:`, `docs:`) and keep messages in the imperative mood (e.g., `fix: handle reconnect retries`). Keep related tests or docs beside the code change. Pull requests should explain motivation, link GitHub issues, and flag user-visible impacts or migration steps. Add screenshots or terminal captures for CLI-facing updates and confirm lint, type check, and tests pass before requesting review.

## Documentation & Examples
Update the relevant markdown in `docs/` whenever protocol contracts or public behavior shift, and verify `uv run mkdocs serve` or `mkdocs build` stays clean. Keep examples aligned with the SDK: reusable patterns belong in `examples/snippets`, while full clients or servers remain under their workspace directories. Annotate configs with placeholder environment variables (`API_KEY`, `DB_URL`) so downstream agents can adapt them quickly.
