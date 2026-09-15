# SEO fields

- `h1`: the glossary `search_term` for the product or category in this locale. Buyers search
  in their words, which are often not the approved technical term; the glossary carries both
  so the H1 can use one and the specs the other.
- `hero_title`: the promise. May equal the H1 when the search term reads naturally as a
  promise; otherwise keep both fields.
- `meta_title`: search term + company name, under the locale limit. No adjectives.
- Find out where the page title actually comes from before writing the hero. Many sites build
  `<title>` from the H1 or the hero lines; then every headline choice is also the search title,
  and a promise-led headline leaves the title without a search word. Give the title its own
  field in that case rather than bending the headline.
- `meta_description`: promise, proof, action, under the limit, using at least one required term.
- Per-locale pages of the same product must carry `hreflang` links to each other and a
  self-reference; two locales in the same language (`en-us`, `en-gb`) need distinct content
  and distinct `hreflang` region codes, or search engines treat them as duplicates.
- Do not stuff the search term. Once in the H1, once in the meta title, naturally in the body.
