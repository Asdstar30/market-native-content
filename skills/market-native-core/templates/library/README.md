# Market content library

Project: __PROJECT_NAME__
Owner: (person responsible for approvals)
Last review: (date)

All copy for this project is written from context packs generated from this folder.
Read `PROJECT-INSTRUCTIONS.md` before writing anything for this company.

## Layout

- `locales.json`: one entry per language + market.
- `core/`: company facts, products, claims with evidence, brand and differentiation.
- `markets/<locale>/`: glossary, objections, voice, banned terms, competitor signals.
- `channels/<channel>/`: limits and written copy per channel.
- `packs/`: generated context packs. Safe to delete.
- `decisions.md`: durable decisions, append only.

## Status conventions

Claims: `draft` | `verified` | `expired` | `retracted`.
Glossary terms: `draft` | `pending_review` | `approved` | `rejected`.
Copy assets: `draft` | `pending_review` | `approved` | `needs_revalidation` | `superseded` | `rejected`.

Nothing becomes `approved` or `verified` without a named human.
