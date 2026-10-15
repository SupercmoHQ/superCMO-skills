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

Read `brand.md` in `./supercmo-company`. Where it already holds this brand, hand it back and stop — re-researching bills again and tells the user nothing new. Carry on where it's missing, where it's a different brand, or where the user asked to re-analyze. A
request for a detailed run of a brand already saved is a re-analysis too: run Step 3 again for a
fresh screenshot (its link doesn't last), then Step 4 in detailed mode with the hero photos
from `brand.md`'s Assets, and patch only what they add.

### Step 2: Check what you were given

| What you have | What to do |
| --- | --- |
| A brand website | Carry on. |
| A product page — Amazon, Shopify, a single listing | Wrong skill. Hand it to `analyzing-products`, and say which you used. |
| Nothing, or a URL that won't load | Ask for the website. A brand described from memory is invented, not read. |
| No mode named, by the caller or the brief | Run quick mode. Don't ask: detailed mode runs only when the caller or the user asks for it. |

**When another skill runs this one** (onboarding, a campaign plan), ask the user nothing: report a
missing website or a site that couldn't be read back to that skill, and skip Step 6's hand-over — the
calling skill gives the one reply.

### Step 3: Read the site

Call `url_extraction` with the homepage as the `url` and **no `prompt` or `schema`**. It returns the
page's own text in `data.markdown`, and beside it `branding` — the colours, fonts and logo the page
actually renders — and `screenshot`, a picture of the page as a visitor first sees it. Read the
brand's identity off the text yourself, as `references/reading-the-brand.md` lays out: the brand's
name, what it sells, the logo, the tagline, how it writes, who it sells to, what sets it apart, and
the proof it offers for it. `metadata.title` and `metadata.description` are the brand's own words too:
use them where the text is thin. Keep `branding` and the screenshot for Step 4.

The read failed when the call returns `ok: false`, or when Step 4 finds the page is an error, login or
bot-check page rather than the brand's own site — never just because there is little text. Then say
the site couldn't be read, and handle it as Step 2's URL that won't load. Where the text is short or
empty but the screenshot shows the brand's site, carry on: take the name from `metadata.title`, add
"What does this screen show for sale?" to the screenshot's prompt, and don't ask the user.

### Step 4: Look at the pictures

Both modes run this step; they differ only in how many photographs they read. What the pictures give
you that the page's markup can't is the brand's **photography style** — the art direction other skills
need to generate something that looks like it belongs to this brand — and a check on `branding`.

- **Quick mode reads Step 3's `screenshot` alone** — one `image_analysis` call.
- **Detailed mode adds the hero photographs** Step 3 found: one `image_analysis` call with the
  screenshot and up to 9 photographs as entries in `requests`, so they are read at once rather than
  one after another. **Give every entry its own `prompt`** — with `requests`, a prompt beside them is
  ignored. Each picture is read on its own and billed on its own; put the style together from what
  they have in common.

The screenshot's prompt asks, in this order:

1. Is this an error, login or bot-check page rather than the brand's own site? Yes or no. A yes is a
   failed read (Step 3): stop, and use nothing from this call.
2. The photography style, in about 120 words: what kind of shots these are (product-only, lifestyle,
   on-model), how they're lit, framed and set, who's cast and how they're styled, the colour grading
   and mood, and what recurs versus what's never in frame.
3. The colours `branding` lists, given with their roles: which are the brand's own, and which belong to
   something embedded on the page, like a video player or a chat widget? A colour that doesn't show on
   this first screen still counts as the brand's — the page uses it further down. Where `branding` has
   none, or none are the brand's, the colours the page visibly uses, as hex codes. And what colour is
   the page's background?
4. The main headline and the body text: is the headline set inside a picture, and how does each look?

A photograph's prompt asks only question 2.

Where there is no screenshot and no photograph, there is no photography style to record; say so.

### Step 5: Write it down

Write `brand.md` into `./supercmo-company`, from what Step 3 extracted and what Step 4 saw, in the order below. Create the folder where it doesn't exist. **Where there is no evidence for a section, write `unconfirmed — needs user input` and move on — never invent a fact, a number, a colour or a claim.**

| Section | What goes in it |
| --- | --- |
| Name | The brand's own name (`brand_name`), spelled as the brand spells it. |
| What it sells | The category the business is in and what a customer actually buys (`what_it_sells`), plus how it is sold. |
| Source | The homepage this was read from, and the date it was read. |
| Palette | The colours Step 4 kept as the brand's own, read as `references/reading-the-brand.md` says. Colours Step 4 read off the screenshot itself are marked as read from it. An achromatic brand is a real palette, not a missing one. Unconfirmed only where there are none. |
| Typography | The heading and body faces from `branding`, read as `references/reading-the-brand.md` says, each with Step 4's description of how it looks beside it. Where the description plainly contradicts the name — a monospaced look for a face named as a sans, say — write what Step 4 saw and leave the name out. Type set inside a picture is art direction: it goes under Photography style. Where `branding` names no fonts, Step 4's descriptions. Unconfirmed only where neither has any. |
| Tagline | The line the brand leads with (`tagline`). |
| Target audience | Who the page says it sells to (`target_audience`), in the page's own terms — carried as it came back, never expanded beyond what the page evidenced. |
| Voice | How the brand writes (`voice_descriptor`), then its own sentences (`voice_examples`), quoted exactly rather than tidied. |
| Key differentiators | What the brand says sets it apart (`key_differentiators`). |
| Proof | The checkable claims the brand makes for itself (`proof_points`) — ratings, review and customer counts, named testimonials, awards, guarantees — each quoted exactly as the page wrote it, not paraphrased. |
| Photography style | Write what Step 4 found — the shot type, lighting, composition, setting, casting, colour grading and mood, any type set inside banner images, and what recurs across the set versus what is never in frame. |
| Assets | The logo (`logo_url`, or `branding.logo` where the page text gives none) and each hero photograph (`hero_reference_urls`) as links, with a line on what each shows. Keep the hosted URLs; don't download them. Where the brand sets its name as plain text rather than a mark, say so rather than leaving the logo silently absent. |

New information goes **into** this one document — don't add another file.

**Where `brand.md` already exists for this brand**, patch the sections that changed rather than
replacing the file, and leave every section you have no new evidence for untouched. Where it holds a
different brand, replace it.

Where the site gave nothing usable at all — no palette, and no images — don't write the file. Say
what was tried and what came back, and ask whether to supply the brand's assets, try another URL, or
carry on without them.

### Step 6: Hand it over

When another skill runs this one, skip this step: that skill gives the reply.

Give the path to `brand.md`.

In the reply, also give the palette, the typography, the voice, the tagline, the differentiators and the
proof — not the whole file. Where a section stayed `unconfirmed`, say in one line what the site
didn't show. Don't ask the user to fill it in: they can add it any time on the Brand page.

## Edge cases

- **`error: "no_provider_configured"`** on any tool → relay the tool's `hint` (the user must set their key).
- **A product page URL** → `analyzing-products`. This skill reads brand websites.
- **The page extracts as an empty shell** — a single-page app that renders no text to the reader →
  `branding` and the screenshot still read the rendered page, so take what they give, and say in
  `brand.md` that the page's text couldn't be read. Don't write an empty palette as if it were the
  brand's palette.
- **The saved brand is out of date, the user says** → re-analyze, and say which parts changed.

## Reference

- `references/reading-the-brand.md` — what to read off the page text, how to read `branding`, and the
  traps.
