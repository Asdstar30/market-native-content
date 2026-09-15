# Library schema

The library lives inside the user's project, by default at `market-content-library/`. It is
the single source of truth for everything an agent writes for that company. Scripts read it;
humans edit it; nothing in it is derived from another file inside it except `packs/`.

## Ownership rule

Three folders, three reasons to change. When unsure where a fact goes, ask which event would
make it change.

| Folder      | Contains                                                          | Changes when              |
|-------------|-------------------------------------------------------------------|---------------------------|
| `core/`     | Facts independent of market and channel                           | The company changes       |
| `markets/`  | Everything specific to one locale regardless of channel           | The market changes        |
| `channels/` | Everything specific to one output format, including written copy  | The output format changes |

A German web hero is `markets/de-de` for its terms and `channels/web/copy/de-de/` for the
text. It is never stored under `markets/`.

## Files

### `locales.json`

```json
{
  "locales": [
    {
      "id": "en-us",
      "language": "en",
      "market": "US",
      "jurisdiction": "US",
      "primary_language_for_buyers": true,
      "search_engine": "google.com",
      "default_cta": "booking-form",
      "audience_notes": "Adults booking for themselves; they compare three clinics online before visiting.",
      "stale_after_days": 180,
      "status": "active"
    }
  ]
}
```

`id` is always `language-market` (`en-us`, `en-gb`, `de-de`, `es-mx`, `ja-jp`). A bare
language is rejected by the scripts, because the same language is sold differently in
different markets.

### `core/company.json`

Name, one-line description, audiences (ids used everywhere else), and `status`. Example
libraries set `"status": "example"` so nobody mistakes them for real data.

### `core/products.json`

```json
{
  "products": [
    {"product_id": "clear-aligners", "name": {"en": "Clear aligners"}, "category": "orthodontics",
     "tags": ["orthodontics", "adult"], "status": "active"}
  ]
}
```

`product_id` is the stable key every other file uses. Names can change; ids do not.

### `core/claims.json`

```json
{
  "claims": [
    {
      "claim_id": "claim-same-day-scan-001",
      "statement": "A panoramic X-ray is taken during the first visit.",
      "evidence": "In-house panoramic unit; booking log shows same-day scans since 2024.",
      "source": "Clinic manager, internal",
      "owner": "clinic-manager",
      "status": "verified",
      "last_verified": "2026-09-01",
      "expires": "2027-09-01",
      "eligible_markets": ["en-us"],
      "eligible_channels": ["web", "email"],
      "jurisdictions": ["US"],
      "product_ids": [],
      "audiences": ["patient"],
      "tags": ["speed", "trust"]
    }
  ]
}
```

- `status`: `draft`, `verified`, `expired`, `retracted`. Only `verified` reaches a pack.
- Empty `product_ids` or `audiences` means "applies to all". `"*"` in `eligible_markets` or
  `eligible_channels` means all.
- `eligible_channels` is where "fine in a quote, not on the website" is recorded.
- `expires` is required. Certifications lapse; delivery times change.

### `core/brand.md`

Company-level voice and, more important, differentiation: what this company says that the
competitors do not, and the `claim_id` that proves each point. Keep it under a page.

### `markets/<locale>/glossary.json`

```json
{
  "locale": "en-us",
  "terms": [
    {
      "concept_id": "clear_aligners",
      "term": "clear aligners",
      "term_type": "commercial",
      "status": "approved",
      "definition": "Removable transparent orthodontic trays.",
      "search_term": "clear aligners",
      "usage_example": "Clear aligners suit mild to moderate cases.",
      "alternatives_to_avoid": ["aligner trays", "clear braces"],
      "do_not_translate": false,
      "source": "Patient enquiries, booking form notes",
      "last_verified": "2026-09-01",
      "tags": ["orthodontics"],
      "product_ids": ["clear-aligners"]
    }
  ]
}
```

- `term_type`: `technical`, `regulatory`, `commercial`, `brand`.
- `status`: `draft`, `pending_review`, `approved`, `rejected`.
- Technical and regulatory terms in `pending_review` are blocked from copy. Commercial terms
  in `pending_review` may appear with a warning.
- `search_term` is what buyers type into a search engine. It is frequently not the approved
  technical term; both are needed.
- `alternatives_to_avoid` become forbidden terms in every pack for this locale.

### `markets/<locale>/objections.json`

```json
{
  "locale": "en-us",
  "objections": [
    {
      "objection_id": "obj-cost-unknown",
      "statement": "I will not know the total cost until I am already committed.",
      "buyer_words": ["Will I know the total cost before I start?", "Are there hidden fees?"],
      "audiences": ["patient"],
      "answer_claim_refs": ["claim-written-plan-002"],
      "tags": ["price", "trust"]
    }
  ]
}
```

`buyer_words` are verbatim phrases from emails, calls or reviews. They are the raw material
for headlines that sound like the market.

### `markets/<locale>/voice.md`

Register (formal, direct, technical), the variant decision (US or UK spelling, European or
Brazilian Portuguese, a standard language or a dialect), sentence length, how trust is built
in this market, and three example sentences that sound right and three that sound wrong.

### `markets/<locale>/banned.txt`

One term per line, `#` for comments. Seeded from `references/banned/generic-<lang>.txt`, then
extended with clichés every local competitor repeats.

### `markets/<locale>/competitors.json`

```json
{
  "locale": "en-us",
  "competitors": [
    {
      "name": "Example clinic",
      "url": "https://example-clinic.invalid/",
      "retrieved_at": "2026-09-10",
      "market_relevance": "high",
      "extraction_quality": "high",
      "hero": {"h1": "...", "subtitle": "...", "cta": "..."},
      "section_order": ["services", "doctors", "reviews", "booking"],
      "proof_used": ["doctor credentials", "before/after photos"],
      "terms_observed": ["clear aligners", "dental implants"],
      "gaps": "No prices, no treatment duration, no written plan."
    }
  ]
}
```

Paraphrase everything except the hero line and CTA. Store the URL and date so the entry can be
refreshed and so nobody has to re-read the page to know where a pattern came from.

### `channels/<channel>/limits.json`

```json
{
  "default": {"hero_title": 60, "hero_subtitle": 140, "hero_cta": 24, "meta_title": 60, "meta_description": 155},
  "de-de": {"hero_title": 55, "hero_subtitle": 130, "hero_cta": 22, "meta_title": 60, "meta_description": 155}
}
```

Limits are character counts per field, per locale, measured on the real layout with the real
font. Do not derive them from expansion ratios; measure.

### `channels/<channel>/copy/<locale>/<page>--<product_id>--<audience>.md`

Copy assets. One shallow folder per locale so a person can find the file; everything else in
front matter so scripts can filter.

```yaml
---
asset_id: web-enus-product-clear-aligners-patient
revision: 1
supersedes_revision: 0
status: draft
locale: en-us
channel: web
page: product
content_scope: full-page
route: /clear-aligners
product_id: clear-aligners
audience: patient
claim_refs:
  - claim-same-day-scan-001
context_pack_id: cp-20260915-en-us-web-product-1a2b3c4d
approved_by:
approved_at:
validated_at: 2026-09-15
validation_status: passed
rejection_reason:
---

## hero_title
...

## hero_subtitle
...
```

- `asset_id` never changes. A new version increments `revision` and sets
  `supersedes_revision`. Putting the version in the id would make every revision a new asset.
- `status`: `draft`, `pending_review`, `approved`, `needs_revalidation`, `superseded`,
  `rejected`. Status lives in front matter, not in the folder name, so a file's path never
  changes as it moves through review.
- `content_scope`: `full-page`, `hero`, `section`, `cta`, `microcopy`, `meta`.
- `claim_refs` lists every claim the copy relies on. `validate_copy.py` checks each one is
  eligible for this locale and channel, and `--revalidate` flags the asset when a claim changes.
- Body fields are `## field_name` headings matching the adapter's blueprint. Field names are
  what `limits.json` keys refer to.
- `rejection_reason` uses the fixed list in `quality-gates.md`.

### `decisions.md`

Append only. Date, locale, scope, decision, reason, approver. Not a log of every draft; a log
of choices that should survive the person who made them.

### `packs/`

Generated by `build_context.py`. Safe to delete. Never edit by hand; edit the source file and
regenerate.
