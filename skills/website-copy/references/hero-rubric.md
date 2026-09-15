# Hero rubric

Generate twenty title candidates, then score each on six criteria, 0 to 2 each. Present the top
three with scores and one line of reasoning. The user chooses.

| Criterion        | 0                                   | 1                                  | 2                                          |
|------------------|--------------------------------------|------------------------------------|--------------------------------------------|
| Clarity          | Needs the subtitle to be understood  | Understood on second read          | Understood in one read by a buyer          |
| Specificity      | Could be any company in the category | Names the product or audience      | Names product, audience and a concrete fact |
| Differentiation  | Says what competitors say            | Hints at the difference            | States the difference from `brand.md`      |
| Proof            | Adjective without evidence           | Implies evidence                   | Carries or points to an eligible claim     |
| Fit              | Over the limit                       | Within limit, awkward line break   | Within limit, breaks cleanly on mobile     |
| Buyer words      | Company vocabulary                   | Mix                                | Uses phrases from `objections.buyer_words` |

Discard anything scoring 0 on Clarity or Fit before ranking. Ties break toward Differentiation.

## Fit is measured, not counted

Character limits are a proxy. Before presenting the top three, render them in the real layout
at the narrowest and the widest breakpoint (390 and 1440 px unless the project says otherwise)
and check each display line against its own container: no overflow, one row per line. Put the
text into the live element and compare a range's width with the container's width; a hidden
overflow on a reveal mask clips the last glyph without any visible error. Measure per locale,
because each script has its own font and width. Two traps seen in practice: a second line that
is indented holds fewer characters than the first, and a limit derived from the length of the
current string says nothing about how much room is left. Write the measured budget back to
`limits.json`, and score Fit 0 for any candidate that overflows.

Vary the twenty deliberately: outcome-first, audience-first, objection-first, proof-first,
question, contrast with the usual alternative, process, number-led (only with a claim). The
same structure twenty times is not twenty candidates.

The model does not score its own final pick as "chosen". It presents three; the person decides.
Record the rejected finalists with a `rejection_reason` when the user explains the choice, so
the next page starts from a better prior.
