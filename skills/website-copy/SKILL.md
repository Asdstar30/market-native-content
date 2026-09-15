---
name: website-copy
description: Write market-native website copy (hero, product pages, home page, RFQ and contact flows, section headings, CTAs, microcopy, meta title and description) from a context pack produced by market-native-core, in any language and locale, with a 20-variant hero rubric, per-locale length limits and automated validation. Use this whenever a user asks for website text, a landing page, hero or headline copy, a product page, "the words for the site", website localisation into another language, or complains that the site copy sounds like AI or like a translation. Not for emails, chat messages, internal documents or quick translations. Requires a market content library; if none exists, run market-native-core in build mode first.
---

# website-copy

This adapter turns a context pack into website copy. It owns what is specific to the web:
page blueprints, field names, length limits, SEO fields and the hero rubric. Everything about
the company and the market comes from the pack; nothing here should be edited to fit one
company.

## Before writing

1. Confirm a library exists. If not, stop and run `market-native-core` in build mode. Copy
   written without a library is the generic copy the user is trying to leave behind.
2. Generate the pack: `python <core>/scripts/build_context.py --library <lib> --locale <id>
   --channel web --page <blueprint> --audience <id> [--product-id <id>]`. Read it.
3. Read `references/blueprints/web/<page>.md`. If the pack contains a blueprint override, it
   wins.
4. If the pack's warnings say there are no eligible claims, no approved terms, or no
   differentiation rows, report that and ask for the missing piece. Do not write around it.

## Page priority

In B2B, buyers read the product page, the datasheet, the delivery terms and the request-for-quote
path long before they admire the hero. When a user asks for "the website", build in this order
unless told otherwise: product page, RFQ or contact flow, home page, about page. The hero is
polished last, once the rest of the page has given it something to point at.

## Writing the page

Work field by field from the blueprint. For each field:

- Say one thing. The hero title is the promise, the subtitle is the mechanism, the CTA is the
  action buyers in this market actually take (the pack names it).
- Use the required terms as written. If the natural sentence wants a synonym, the sentence is
  wrong, not the glossary.
- Every promise maps to a claim id from the pack. Keep the list; it goes into `claim_refs`.
- Answer the objections in the pack in the order the market builds trust (the voice file says
  whether this market wants specs first or approvals first).
- Read the competitor hero lines in the pack once, for vocabulary and structure, then write
  from the differentiation section. If the draft could be pasted onto a competitor's site
  without anyone noticing, it is not finished.

Write each locale from its own pack. A page in a second language is a new writing task with a
new pack, never a translation of the first. Facts (numbers, certifications, delivery terms)
must match across locales because they come from the same claims, and the validator compares
numbers against claims for that reason.

## The hero

Generate twenty title candidates. This is not ceremony: the space of good headlines is wide and
the first few candidates are always the obvious ones. Twenty short lines cost a few hundred
tokens. Then score them with `references/hero-rubric.md` (clarity, specificity, differentiation,
proof, fit to limit, buyer words used) and present the top three with their scores and the
reasoning. The user picks; the model does not grade its own final choice.

Keep the H1 and the visible hero title separate in your head. The H1 carries the search term
from the glossary (`search_term`), the hero title carries the promise. They can be the same
line when the search term fits naturally; when they conflict, the blueprint has a field for each.

## Final critique, before showing the page

The validator is a floor: copy can pass every check and still give the buyer no reason to
choose. Before presenting, read the whole page once as the buyer in the pack's audience and
answer four questions in one line each. If any answer is "no", revise first.

1. Reason to choose: does the page state the differentiation from `brand.md`, with its proof,
   above the fold?
2. Objections: is every objection in the pack answered where a buyer would look for it?
3. Action: is the conversion path the one this market actually uses, and is it reachable
   without scrolling back?
4. Search: does the H1 carry the search term, and does the page answer the question a buyer
   who typed it was asking?

Attach the four answers to the delivery note. They are the part of quality a script cannot
check.

## After writing

1. Save the asset at `<lib>/channels/web/copy/<locale>/<page>--<product_id>--<audience>.md`
   with the front matter from the core schema, `status: draft`, `claim_refs` filled,
   `context_pack_id` from the pack.
2. Run `python <core>/scripts/validate_copy.py --copy <file> --pack <lib>/packs/<pack_id>.json`.
   Fix every error. Show the warnings next to the copy; a warning about a number without a
   claim usually means a promise slipped in.
3. Present the copy, the three hero options, the validation summary and the pack's warnings.
   Record any durable choice (why this CTA, why this section order) in `decisions.md`.

## Microcopy and RTL

Navigation labels, form fields, button text and error messages are where translated sites
give themselves away. Treat them as copy: pull the CTA and navigation terms from the glossary,
respect the `hero_cta` limit for buttons, and for right-to-left locales keep product codes and
standards in Latin script inside the sentence (the market reads them that way) and note in
the asset that bidirectional marks may be needed around them.

## References

- `references/blueprints/web/product-page.md`: fields, order, what each field must do.
- `references/blueprints/web/home.md`: same for the home page.
- `references/hero-rubric.md`: how to score and present hero candidates.
- `references/seo-fields.md`: meta title, description, H1 versus hero, hreflang note.
