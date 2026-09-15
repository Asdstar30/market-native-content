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

Vary the twenty deliberately: outcome-first, audience-first, objection-first, proof-first,
question, contrast with the usual alternative, process, number-led (only with a claim). The
same structure twenty times is not twenty candidates.

The model does not score its own final pick as "chosen". It presents three; the person decides.
Record the rejected finalists with a `rejection_reason` when the user explains the choice, so
the next page starts from a better prior.
