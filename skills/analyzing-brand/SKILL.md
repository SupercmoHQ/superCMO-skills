---
name: analyzing-brand
description: Analyzes a brand from its own website — its colours and fonts, the logo and imagery it uses, how it sounds, who it sells to, the claims it makes, and what it sells. Reads the site and its pictures with a vision model, and marks anything the site doesn't evidence as unconfirmed rather than guessing. Facts only — nothing is generated, planned or judged here. Use when a brand's guidelines, palette, typography, voice, tone or positioning need establishing, or when another skill needs the brand before it plans or generates.
license: Apache-2.0
metadata:
  version: "0.4.0"
  category: creative
  summary: "Works out your brand from your website — your colours, fonts and logo, how you sound, who you sell to, what you sell, and the claims you stand behind. Anything your site doesn't actually say is written down as unconfirmed rather than invented, so the skills that plan and make your ads work from your real brand."
---

# Brand

Analyze what a brand is from its **website**.  Not for analyzing a single product's facts — that is `analyzing-products` skill.

## Workflow

### Step 1: Check whether the brand is already known

Read `brand.md` in `./supercmo-company`. Where it already holds this brand, hand it back and stop — re-researching bills again and tells the user nothing new. Carry on where it's missing, where it's a different brand, or where the user asked to re-analyze.

### Step 2: Check what you were given

| What you have | What to do |
| --- | --- |
| A brand website | Carry on. |
| A product page — Amazon, Shopify, a single listing | Wrong skill. Hand it to `analyzing-products`, and say which you used. |
| Nothing, or a URL that won't load | Ask for the website. A brand described from memory is invented, not read. |
| No mode named, by the caller or the brief | Ask whether the user wants to run the analysis in quick mode or detailed mode. Offer quick first and recommend it. Say a detailed mode run also reads the site's photographs with a vision model, which is what gives the photography style, and costs and takes longer for it. |

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

**Quick mode skips this step entirely** — no vision call.

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

Where the page has no photographs at all, there is no photography style to record; say so.

### Step 5: Write it down

Write `brand.md` into `./supercmo-company`, from what Step 3 extracted and what Step 4 saw, in the order below. Create the folder where it doesn't exist. **Where there is no evidence for a section, write `unconfirmed — needs user input` and move on — never invent a fact, a number, a colour or a claim.**

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
| Photography style | **Detailed runs only** — a quick run leaves the row out; a later detailed run appends it. Write what Step 4 found — the shot type, lighting, composition, setting, casting, colour grading and mood, and what recurs across the set versus what is never in frame. |
| Assets | The logo (`logo_url`) and each hero photograph (`hero_reference_urls`) as links, with a line on what each shows. Keep the hosted URLs; don't download them. Where the brand sets its name as plain text rather than a mark, say so rather than leaving the logo silently absent. |

New information goes **into** this one document — don't add another file.

**Where `brand.md` already exists**, patch the sections that changed rather than replacing the file.
Leave every section you have no new evidence for untouched.

Where the site gave nothing usable at all — no palette, and no images — don't write the file. Say
what was tried and what came back, and ask whether to supply the brand's assets, try another URL, or
carry on without them.

### Step 6: Hand it over

Give the path to `brand.md`.

In the reply, also give the palette, the typography, the voice, the tagline, the differentiators and the
proof — not the whole file. List every section you marked `unconfirmed`, so the gaps are visible rather than silent.

## Edge cases

- **`error: "no_provider_configured"`** on any tool → relay the tool's `hint` (the user must set their key).
- **A product page URL** → `analyzing-products`. This skill reads brand websites.
- **The page won't extract but its pictures read fine** → Step 3's own fallback already covers this:
  ask the user for the palette, the typeface and the tagline. Step 4 still runs and gives the
  photography style. Say in `brand.md` that the page itself couldn't be read.
- **The page extracts as an empty shell** — a single-page app that renders nothing to the fetcher →
  say what came back and ask for the brand's colours and fonts directly. Don't write an empty palette
  as if it were the brand's palette.
- **The saved brand is out of date, the user says** → re-analyze, and say which parts changed.

## Reference

- `references/reading-the-brand.md` — the extraction prompt, how to read what it returns, and the
  traps.
