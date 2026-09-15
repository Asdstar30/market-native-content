# Example: Maple Dental (fictional)

A complete, small market content library for a **fictional** dental clinic in Denver,
Colorado, locale `en-us`. Every company, person, claim, competitor and URL in this folder is
invented for the example. Competitor URLs use the reserved `.invalid` domain so they cannot
resolve.

It exists to show what a filled library looks like, to give the tests a realistic fixture, and
to prove the pipeline works for a service business, not only for an industrial exporter.

Try it:

```bash
python skills/market-native-core/scripts/build_context.py \
  --library examples/maple-dental/market-content-library \
  --locale en-us --channel web --page product --audience patient --product-id clear-aligners --stdout

python skills/market-native-core/scripts/validate_copy.py \
  --copy examples/maple-dental/market-content-library/channels/web/copy/en-us/product--clear-aligners--patient.md \
  --library examples/maple-dental/market-content-library
```

The copy asset passes validation. Change a phrase in it to a term from
`markets/en-us/banned.txt`, or add a number that is not in a claim, and run the validator
again to see the checks fire.
