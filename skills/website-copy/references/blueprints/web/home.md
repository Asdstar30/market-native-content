# Blueprint: home page

The home page routes. Its hero says what the company does, for whom, and why a buyer would
choose it; every section below hands the reader to a product page or the contact path.

| Field              | Job                                                            | Limit key          |
|--------------------|-----------------------------------------------------------------|--------------------|
| `h1`               | Category search term + market qualifier                        | `h1`               |
| `hero_title`       | What we do + for whom + the differentiation, one line          | `hero_title`       |
| `hero_subtitle`    | The strongest claim with its proof                             | `hero_subtitle`    |
| `hero_cta`         | Market's conversion action                                     | `hero_cta`         |
| `who_we_serve`     | Audiences by name, each with the outcome they get              |                    |
| `products`         | Product families as links, using glossary terms                |                    |
| `proof`            | Certifications, references, numbers, all from claims           |                    |
| `differentiation`  | The rows from `core/brand.md`, in the market's words           |                    |
| `how_to_buy`       | Enquiry to delivery, the market's real steps                   |                    |
| `final_cta`        | Repeat the action                                              | `hero_cta`         |
| `meta_title`       | Category term + company                                        | `meta_title`       |
| `meta_description` | What, for whom, proof, action                                  | `meta_description` |

Section order follows the pack's competitor pattern unless the differentiation argues for a
change; record that change in `decisions.md` so the next locale does not undo it.
