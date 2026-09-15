# Writing instructions for this project

Before writing or editing any text a customer will see (website, app, document, email,
presentation, social post):

1. Generate a context pack for the exact locale, channel, page and audience:
   `python <skill>/scripts/build_context.py --library <this folder> --locale <id> --channel <ch> --page <p> --audience <a>`
2. Write from the pack only. Do not translate another locale's copy. Do not state a claim
   that is not in the pack. Do not use a term listed as blocked or forbidden.
3. Run `validate_copy.py` on the result and fix errors before showing the copy.
4. Save the asset with front matter and `status: draft`. Only a named person sets `approved`.

If the pack reports missing or stale data, say so and stop rather than writing around it.
