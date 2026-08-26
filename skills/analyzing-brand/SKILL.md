---
name: analyzing-brand
description: Analyzes a brand from its own website — its colours and fonts, the logo and imagery it uses, how it sounds, who it sells to, the claims it makes, and what it sells. Reads the site and its pictures with a vision model, and marks anything the site doesn't evidence as unconfirmed rather than guessing. Facts only — nothing is generated, planned or judged here. Use when a brand's guidelines, palette, typography, voice, tone or positioning need establishing, or when another skill needs the brand before it plans or generates.
license: Apache-2.0
metadata:
  version: "0.2.0"
  category: creative
  summary: "Works out your brand from your website — your colours, fonts and logo, how you sound, who you sell to, what you sell, and the claims you stand behind. Anything your site doesn't actually say is written down as unconfirmed rather than invented, so the skills that plan and make your ads work from your real brand."
---

# Brand

Analyze what a brand is from its **website**.  Not for analyzing a single product's facts — that is `analyzing-products` skill.

## Workflow

### Step 1: Check whether the brand is already known

**Where `get_brand_details` is available, call it first.** A brand that has already been analyzed
comes back from the tool — hand that back and stop. Re-researching it bills again and tells the user
nothing new. Where the tool isn't installed, or returns nothing, carry on.

### Step 2: Check what you were given

| What you have | What to do |
| --- | --- |
| A brand website | Carry on. |
| A product page — Amazon, Shopify, a single listing | Wrong skill. Hand it to `analyzing-products`, and say which you used. |
| Nothing, or a URL that won't load | Ask for the website. A brand described from memory is invented, not read. |

### Step 3: Read the site

Call `url_extraction` with the homepage as the `url` and the prompt in
`references/reading-the-brand.md` as the `prompt`. It returns the brand's identity as strict JSON —
the brand's name, what it sells, the palette, the typography, the logo, the tagline, how it writes,
who it sells to, what sets it apart, and the proof it offers for it. Where the params are uncertain, send `dry_run: true` once: it returns the
exact request that would go out and spends nothing.

Treat the call as failed when it comes back empty, unauthorized, a 4xx, or an anti-bot challenge — a
wall of markup with no brand text in it is a challenge, not a minimal site. Where it fails, ask the
user for the palette, the typeface and the tagline in one message. **Don't abort** — the pictures
(Step 4) and the end-state check (Step 5) run regardless.

### Step 4: Look at the pictures

The palette and the type are already covered by Step 3. What the pictures give you that the page's
markup can't is the brand's **photography style** — the art direction other skills need to generate
something that looks like it belongs to this brand.

- Take the hero photographs Step 3 found on the page.
- **One `image_analysis` call carrying all of them**, up to ten, so they are read at once rather than
  one after another.
- Ask for the brand's photography style across the set: what kind of shots these are (product-only,
  lifestyle, on-model), how they're lit, how they're composed and framed, the settings and
  backgrounds, who's cast and how they're styled, the colour grading and mood, and what recurs across
  the set versus what's never in frame.

**A download that fails is a gap, not a stop** — carry on. Where the page has no photographs at all,
there is no photography style to record; say so.

### Step 5: Write it down

Everything this run produces goes in one folder: `brand-analysis/<date-time>` under
`$SUPERCMO_OUTPUT_DIR` (default `./supercmo-media`), with an `assets/` subfolder for the downloads.
Make it fresh for this run — where a folder for this minute already exists, add `-2`, `-3`, … rather
than writing into it.

Download the logo and the hero photographs into `assets/`, then write `brand.md` from what Step 3
extracted and what Step 4 saw — one file, in the order below. **Where there is no evidence for a
section, write `unconfirmed — needs user input` and move on — never invent a fact, a number, a colour
or a claim.**

| Section | What goes in it |
| --- | --- |
| Name | The brand's own name (`brand_name`), spelled as the brand spells it. |
| What it sells | The category the business is in and what a customer actually buys (`what_it_sells`), plus how it is sold. |
| Source | The homepage this was read from, and the date it was read. |
| Palette | The hex codes (`palette_hex`), and where each is used on the page. Say whether they were declared by the page or read off what it renders (`palette_source`) — an achromatic brand is a real palette, not a missing one. Only `palette_source: none` is unconfirmed. |
| Typography | The font family as the page declares it (`typography_font_family`), the plain-language description of how it looks (`typography_descriptor`), and the reference URL where the page gave one (`typography_reference_url`). |
| Tagline | The line the brand leads with (`tagline`). |
| Target audience | Who the page says it sells to (`target_audience`), in the page's own terms — carried as it came back, never expanded beyond what the page evidenced. |
| Voice | How the brand writes (`voice_descriptor`), then its own sentences (`voice_examples`), quoted exactly rather than tidied. |
| Key differentiators | What the brand says sets it apart (`key_differentiators`). |
| Proof | The checkable claims the brand makes for itself (`proof_points`) — ratings, review and customer counts, named testimonials, awards, guarantees — each quoted exactly as the page wrote it, not paraphrased. |
| Photography style | What Step 4 found — the shot type, lighting, composition, setting, casting, colour grading and mood, and what recurs across the set versus what is never in frame. |
| Assets | The logo (`logo_url`) and each hero photograph (`hero_reference_urls`): its path in `assets/`, the URL it came from, and what it shows. A download that fails keeps the URL and says the file is missing. Where the brand sets its name as plain text rather than a mark, say so rather than leaving the logo silently absent. |

New information goes **into** `brand.md` — don't add another file.

### Step 6: Save it and hand it over

**Where `save_brand_profile` is available, call it with the folder path.** It puts the brand somewhere
durable, so the next session starts from Step 1 instead of researching again. Where the tool isn't
installed, the file stays where it is and that is fine.

Give the path either way. **Skills that run after this one in the same session read `brand.md`
directly**, so pass the path on rather than repeating the contents.

In the reply give the palette, the typography, the voice, the tagline, the differentiators and the
proof — not the whole file. List every section you marked `unconfirmed`, so the gaps are visible rather than silent.

Where the site gave nothing usable at all — no palette, and no images — don't write the file. Say
what was tried and what came back, and ask whether to supply the brand's assets, try another URL, or
carry on without them.

## Edge cases

- **`error: "no_provider_configured"`** on any tool → relay the tool's `hint` (the user must set their key).
- **A product page URL** → `analyzing-products`. This skill reads brand websites.
- **The page won't extract but its pictures read fine** → Step 3's own fallback already covers this:
  ask the user for the palette, the typeface and the tagline. Step 4 still runs and gives the
  photography style. Say in `brand.md` that the page itself couldn't be read.
- **The page extracts as an empty shell** — a single-page app that renders nothing to the fetcher →
  say what came back and ask for the brand's colours and fonts directly. Don't write an empty palette
  as if it were the brand's palette.
- **`get_brand_details` returns a brand the user says is out of date** → research it again, and say
  which parts changed.

## Reference

- `references/reading-the-brand.md` — the extraction prompt, how to read what it returns, and the
  traps.
