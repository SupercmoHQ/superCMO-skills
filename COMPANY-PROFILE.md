# The `company/` brand-profile convention

SuperCMO grounds every campaign, script, and answer in a small folder of brand-context
files. Hosted SuperCMO researches and manages this folder for you; **open-source and BYOK
users get the identical convention as plain local files** — no tools required, the agent
reads and edits the files directly. This is the v0 parity surface: the files *are* the API.

## The folder

A `company/` folder (the agent's working directory) holds:

| File | Holds |
| --- | --- |
| `README.md` | The self-describing maintenance contract — the file the agent reads first. It is the single source of truth for how to keep the folder current. |
| `brand.md` | Positioning, messaging, and voice. |
| `personas.md` | The ICP and personas. |
| `competitors.md` | One battlecard per competitor (fast-moving). |
| `products.md` | The product catalog (fast-moving). |
| `brand.json` | A generated structured summary — read-only; edit the markdown, not this. |
| `assets/` | Logo, product images, demo videos. |

The fixed set above is the whole taxonomy — new information goes **into** an existing
file; there are no new top-level files in v0.

## The rules live in the folder, not here

`company/README.md` is the **canonical contract** — each file's one job, when to update
(durable learnings only, cited to real evidence), the freshness marker, and the
fast-moving vs stable tiers. It is product-owned and stamped into the folder; **read it
there.** This page is only a pointer and the parity record — it deliberately does not
restate those rules (one canonical contract, no duplication).

## OSS / BYOK

Point the agent at a local `company/` folder (default `./company`, or set
`CMO_COMPANY_DIR`). Create the files by the shapes above and the agent will read and
maintain them exactly as the hosted product does. No database, no tools, no sync — the
local files are canonical.
