---
name: writing-ad-copy
description: Writes the words of an ad — the headline, primary text, description and call to action that go into the ad platform's own fields, shaped to the channel it runs on. Handles one channel or several, returning copy sized to each platform's limits. Nothing is generated here — text only. Use when the user wants ad copy, ad text, headlines, primary text, a description or captions written for a paid ad.
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: creative
  summary: "Writes the text that runs alongside your ad — headline, primary text, description and call to action — tuned to the fields and best practices of each platform it runs on: Facebook and Instagram, Google Search, LinkedIn, TikTok, X and Reddit. It works one angle several ways and sizes each field so nothing gets cut off in the feed."
---

# Ad copy

Write the words that ride *beside* the creative in the ad platform — the headline, the primary text, the description, the call to action. **Text only — nothing is generated here.** Not the text drawn on the image, and not a spoken voiceover.

**Ad copy may run on one channel or several.** The same product, written for each channel it runs on — because the fields and the limits differ, and the register does too. Write each channel's set, then hand them all back.

## Workflow

### Step 1: Read what's fixed

Ask only for what would change the copy and can't be defaulted.

- **The product and the offer** — what it is, what it does for the buyer, and any promotion (a price, a discount, a launch).
- **Who it's for, and how aware they are** — a buyer who already knows the category reads differently from one meeting the problem for the first time.
- **Which channel(s)** the copy runs on — this decides the fields, the limits and the register.
- **The grounding** — the claims the user will stand behind, and any raw material: reviews, a winning ad, ad comments, the words real customers use. **This is what the copy is built from.**

**Feature claims vs proof claims.** What the product *is* and *does* — its features, how it works, the offer — the user can simply assert, and you write from that. A **proof** claim — a number, a rating, a testimonial, a "better than X" result — needs real backing; where there is none the claim doesn't get made, and you ask rather than invent one. Where the proof is only a paraphrase (*"reviewers keep saying it's less bitter"*), attribute it — *reviewers say…* — rather than stating it as fact; a supplied review's own words are stronger still.

**What to default, and what to ask.** Audience and awareness can be defaulted to the broad buyer where unstated. The channel and the grounding cannot: **no channel named → ask which; no grounding at all → ask for it and don't write yet.** A *partial* gap — a missing offer, a single thin claim — is different: write the angles the material supports and name the gap.

### Step 2: Pick the angles

An ad tests a few different **arguments**, not one argument reworded. Pick a handful of distinct angles from what the product and the grounding actually support — these recur, as a starting range rather than a closed list:

- **the pain** — name the problem the buyer lives with.
- **the outcome** — the after, the result they get.
- **the proof** — a real number, review or result, relayed not claimed.
- **curiosity** — point at something they don't know yet.
- **the comparison** — against the old way or the alternative.
- **urgency** — a real deadline or scarcity, never a fake one.
- **identity** — speak to who the buyer already is.
- **the contrarian** — contradict what the category assumes.

Each angle becomes one variant. **Vary the angle, not the words** — a set of the same line with synonyms swapped tests nothing. **A thin brief supports only a few real angles; don't manufacture more** — two honest arguments written well beat eight that are one argument in disguise.

### Step 3: Read the channel's guide

Read the guide for each channel the copy runs on. It owns that channel's fields, character limits, where the feed cuts the text off, the calls to action it offers, and the register that reads as native there.

| Channel | Guide |
| --- | --- |
| Meta — Facebook & Instagram ads | `references/channel-copy-meta.md` |
| Google — Search / Responsive Search Ads | `references/channel-copy-google.md` |
| LinkedIn — Sponsored Content | `references/channel-copy-linkedin.md` |
| TikTok — In-Feed ads | `references/channel-copy-tiktok.md` |
| X (Twitter) — Promoted ads | `references/channel-copy-x.md` |
| Reddit — Promoted posts | `references/channel-copy-reddit.md` |

Where the user names a channel with no guide here, write to the closest one and say which you used.

### Step 4: Write the core copy

Write each field the channel calls for:

- **The headline** — specific and benefit-led, in the active voice, one clear idea. A number or a concrete detail beats a general claim.
- **The primary text / body** — leads on the angle and **front-loads the hook**, since the feed cuts it off (Step 5). Carries the proof and answers the obvious objection.
- **The description** — *complements* the headline, never repeats it: a proof point, an objection handled, the offer reinforced.
- **The call to action** — where the channel takes one, the single action the ad asks for, chosen from its own set. Some channels assemble the ad and take no manual CTA — the guide says which.

Say what the picture can't, in the buyer's own language. No filler to reach a limit; no hype the grounding doesn't earn.

### Step 5: Fit each field to the channel

- **Front-load.** The first words of the primary text (and the headline) carry the message, because the feed truncates the rest behind a "… more". Everything load-bearing sits before the fold the channel's guide names.
- **Write to the field's budget.** Take each field's limit from the channel guide and write inside it. Where the platform assembles or randomises the fields it's given, each one has to **stand alone** and make sense in any combination — the guide flags where.

### Step 6: Make the variants

One variant per angle from Step 2, each a genuinely different argument — a different reason to buy, not the same reason reworded. Drop any two that have collapsed into near-duplicates and replace one with a fresh angle. Hold the offer and the product identical across them; vary only the argument.

**Where a channel assembles many assets from what you supply** — taking a large set of headlines and combining them — give it distinct phrasings and lengths of the angles you have, since the machine, not a reader, sees the whole set. But **don't pad to the channel's maximum**: a thin brief yields fewer genuinely distinct assets, and a handful that avoid repeating the same word beat a full set that all lean on it. Fewer distinct assets beat near-duplicates. Everywhere else it stays one variant per argument.

### Step 7: Check every field against its limit

Take each field beside its channel's limit and test it. A field over its limit is a **rewrite, not a trim at the end** — a headline cut mid-word reads worse than a shorter one written whole.

- **Does it fit?** Count the characters against the guide's number for that field.
- **Is it grounded?** Every claim traces back to Step 1's material. No invented stat, rating or testimonial survives.
- **Is it compliant?** Flag anything the channel restricts — an unsupported claim, personal-attribute phrasing ("are *you* struggling with…"), a before/after in a restricted category — and offer the compliant version rather than shipping it.

### Step 8: Hand the copy back

Grouped by channel, then by angle. For each field: the text and its character count. Where the channel takes a bulk set of fields, lay them out in that shape.

Text only — nothing here is posted, generated or spent.

## Edge cases

- **No grounding supplied** — ask for the claims, reviews or comments the copy should be built from before writing. Copy invented from nothing is worse than a held cursor; don't fabricate proof to fill the fields.
- **The user wants the text drawn *on* the image** — the headline or hook rendered into the creative → `generating-image-ads`. This skill writes the platform's own copy fields, not the picture.
- **The user wants a spoken voiceover or a video script** → `writing-video-scripts`. Any words heard over a video belong there.
- **Long-form — a blog post, an email, landing-page copy** — is out of scope; this skill writes short paid-ad fields.
- **A channel with no guide here** — write to the closest guide, say which, and keep to its limits; call out where the real channel likely differs.
- **The offer or a claim is missing** — write the angles the material supports and name the gap.

## Reference

**Channel guides — read the one for each channel the copy runs on:**

- `references/channel-copy-meta.md` — Facebook & Instagram: primary text, headline, description, the fold, CTA set.
- `references/channel-copy-google.md` — Search / RSA: the headline and description sets, headline independence, no-hype rules.
- `references/channel-copy-linkedin.md` — Sponsored Content: intro text, headline, description, the professional register.
- `references/channel-copy-tiktok.md` — In-Feed: the ad text, the native non-ad tone, UI-safe placement.
- `references/channel-copy-x.md` — Promoted ads: post text and headline, brevity.
- `references/channel-copy-reddit.md` — Promoted posts: title and body, the community-native, non-salesy register.
