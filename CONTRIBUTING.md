# Contributing

Thanks for looking at this. The bar is simple: a change should make the copy that
agents produce more native to a real market, or make the scripts more reliable.

## Ground rules

- **No real company data in the repo.** Examples use fictional companies, `.invalid`
  domains and facts marked `"status": "example"`. Pull requests that add a real
  company's glossary, claims or competitors will be closed.
- **Standard library only** for scripts. Zero-dependency install is a feature.
  Python 3.10 or newer.
- **Linux and Windows both pass.** CI runs both. Encoding bugs are bugs.
- **Language files are starters, not truth.** `references/banned/generic-<lang>.txt`
  lists marketing clichés for one language. Add a language by adding a file with
  the same name pattern and a short comment header on where the terms come from.

## Code style

- `from __future__ import annotations` at the top of every script.
- Type hints on every function signature. Docstrings on public functions.
- `main(argv: list[str] | None = None) -> int`. Errors go to stderr with a non-zero
  exit code. No `sys.exit()` inside library functions.
- Every `open()` passes `encoding="utf-8"`. Every `json.dump` passes
  `ensure_ascii=False`. stdout and stderr are reconfigured to UTF-8 at startup so
  Arabic, Cyrillic and CJK print correctly on Windows consoles.
- `pathlib.Path` for paths. No hard-coded absolute paths. No vendor or user paths.
- Deterministic output: sorted keys, stable ordering, no timestamps except where a
  field is explicitly a timestamp.
- No side effects at import time. Scripts are importable so tests can call `main()`.
- Keep lines readable and functions short. `ruff` and `black` are welcome on new code
  but are not enforced; neither is a dependency.
- English identifiers, comments and messages. Data may be in any language.
- No emoji in code, commit messages or documentation.

## Skills

- `SKILL.md` stays under 200 lines. Details go in `references/` and are loaded when
  the workflow reaches them.
- Explain why a rule exists instead of writing it in capitals. The model reading the
  skill is capable; give it the reasoning.
- The `description` field decides whether the skill triggers. Keep it concrete and
  slightly pushy: what it does, and the phrases a user would type.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests never touch the network. Competitor pages are fixtures under `tests/fixtures/`.
A new script needs a test. A bug fix needs a regression test.

## Commits and pull requests

- Conventional commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- One topic per pull request. Describe what changed and why in the body.
- Update `CHANGELOG.md` under `Unreleased`.
