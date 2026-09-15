# Quality gates

## Human gates

Two points where the agent stops and the user decides. Both exist because the cost of a wrong
entry is multiplied by every page that later reads it.

**Gate 1: competitor selection.** The agent proposes 5 to 8 candidates per locale with a
one-line reason each (market, audience, price band, native or translated site). The user picks.
Fewer than 5 makes term frequency unreliable; more than 8 adds cost without adding signal.

**Gate 2: glossary review.** Technical and regulatory terms are `pending_review` until the user
(or a native-speaking colleague) approves them. Commercial terms may be used as `draft`. Batch
the review: one session, at most 15 items, rather than an interruption per term. Gate fatigue
is the most likely way this system fails, so design the review to be short.

## Status lifecycle

Glossary terms: `draft` → `pending_review` → `approved` | `rejected`.

Claims: `draft` → `verified` → `expired` | `retracted`.

Copy assets: `draft` → `pending_review` → `approved` → `superseded`, with `rejected` from any
state and `needs_revalidation` set automatically when a referenced claim changes.

## Rejection reasons

Free-text rejections teach nothing. Use one of these in `rejection_reason`, plus an optional
note:

- `too-generic`: could describe any company in the category
- `wrong-term`: uses a term buyers in this market do not use
- `unsupported-claim`: promises something without an eligible claim
- `wrong-register`: too formal, too casual, wrong dialect
- `too-long`: exceeds layout limits
- `translated-feel`: reads as a translation of another locale
- `off-message`: does not carry the differentiation
- `wrong-cta`: asks for an action this market does not take

## Automated checks (`validate_copy.py`)

Errors block; warnings are shown with the copy.

Errors:
- front matter missing required fields
- locale or channel disagree with the pack
- forbidden term present (banned list, alternatives to avoid, rejected term, blocked
  technical term)
- `claim_refs` entry that is not eligible in this pack
- field longer than its limit

Warnings:
- no approved glossary term appears anywhere in the copy (strong sign of generic text)
- a number in the copy that does not appear in any referenced claim
- em dash present (the single most reliable AI-text tell in Latin-script copy)
- a field the limits file names is missing from the asset
- pack older than the library files it was built from

## What the checks cannot do

They cannot tell whether the copy gives a buyer a reason to choose. That is the user's
judgment and the reason the differentiation file exists. A copy that passes every check and
says nothing is still a failure; treat the checks as a floor.
