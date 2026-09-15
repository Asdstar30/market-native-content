# Blueprint: product page

Fields, in the order they appear on the page. Field names are the `## headings` in the copy
asset and the keys in `channels/web/limits.json`. A market may reorder sections; the pack's
competitor pattern shows the order buyers there expect, and `voice.md` says how trust is built.

| Field              | Job                                                                 | Limit key         |
|--------------------|----------------------------------------------------------------------|-------------------|
| `h1`               | Search term for this product in this market (glossary `search_term`) | `h1`              |
| `hero_title`       | The promise: outcome + for whom + what makes it credible             | `hero_title`      |
| `hero_subtitle`    | The mechanism: how the promise is delivered, one sentence            | `hero_subtitle`   |
| `hero_cta`         | The action this market takes (WhatsApp, RFQ form, phone)             | `hero_cta`        |
| `problem`          | The buyer's situation in the buyer's words (from objections)         |                   |
| `specs`            | What the product is, using required terms; codes stay Latin          |                   |
| `proof`            | Claims with evidence, in the order this market trusts                |                   |
| `how_it_works`     | Steps from enquiry to delivery or result                             |                   |
| `objections`       | Each objection from the pack, answered by its claim                  |                   |
| `faq`              | Questions buyers actually ask (buyer words), short answers            |                   |
| `final_cta`        | Repeat the action with the lowest-friction next step                 | `hero_cta`        |
| `meta_title`       | Search term + company, no promises                                   | `meta_title`      |
| `meta_description` | Promise + proof + action, plain                                      | `meta_description`|

Rules that apply to every field:

- No claim without a `claim_id` in the pack. If the proof section is thin, say so; do not pad.
- Numbers come from claims verbatim. The validator flags any number it cannot trace.
- Required terms appear as written. Blocked terms do not appear at all.
- Product codes, standards and certifications stay in Latin script in every locale.
- B2B pages put `specs`, `proof` and the RFQ path above `faq`. Consumer pages may move
  `problem` above `specs`.
