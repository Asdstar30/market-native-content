# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- French starter cliché list (`references/banned/generic-fr.txt`).

### Fixed

- `extract_signals.py`: a server that breaks the HTTP protocol (for example more than 100
  response headers) is recorded as a failed page instead of ending the whole batch.
- `extract_signals.py`: headlines built from one element per word (animated spans, `<br>`) no
  longer lose their spaces ("Planfirst.Paylater." became "Plan first. Pay later.");
  letter-by-letter spans still join into one word.
- `build_context.py`: a forbidden term that normalises to an approved term (for example a
  case-only variant of the brand name) no longer bans the approved term; it is dropped and
  reported as a pack warning. Found in the first real-project acceptance test.
- `validate_copy.py`: hero-only and section assets no longer warn about missing page-level
  fields such as `meta_title`; keys starting with `_` in `limits.json` are ignored.

### Changed

- `website-copy`: the hero rubric now requires measuring the top candidates in the rendered
  layout at the narrowest and widest breakpoint, per locale, and writing the budget back to
  `limits.json`.
- `website-copy`: SEO guidance asks where the page title comes from before a headline is chosen.
- `market-native-core`: `search_term` must come from evidence, not from a copy of the term.

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
