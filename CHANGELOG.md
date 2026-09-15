# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-09-15

### Added

- `market-native-core` skill: library schema, templates, three workflow modes,
  two human gates, context pack specification, quality gates.
- `website-copy` adapter skill: product page and home page blueprints, hero rubric,
  UI limits, writing workflow.
- Scripts (standard library only): `init_library.py`, `extract_signals.py`,
  `build_context.py`, `validate_copy.py`.
- Starter cliché lists for English, German, Spanish, Arabic, Turkish and Russian.
- Fictional example library `examples/maple-dental` (`en-us`) that passes validation.
- Test suite with offline HTML fixtures, including legacy-encoded pages, a right-to-left
  page and a page whose hero is rendered by JavaScript.
- CI on Linux and Windows, Python 3.10 and 3.12.
