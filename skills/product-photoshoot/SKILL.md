---
name: product-photoshoot
description: Produces commercial product photography from a brief and an optional product photo — studio packshots, lifestyle scenes, in-use closeups, Pinterest pins, website banners, social carousels, paid-ad packs, on-model shots, surreal concept shots, and seasonal makeovers. Use when the user asks for a product shot, packshot, lifestyle image, hero/banner, pin, ad creative, carousel, model try-on, or to restyle an existing product photo. Routes the brief to the right mode, assembles a professional photography prompt, and generates the image(s).
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: creative
---

# Product Photoshoot

Turn a product brief — text, optionally with a product photo — into commercial-grade imagery via the
`image_generate` tool.

## Workflow

### Step 1: Route to a mode

Pick by **intent, not keyword-matching** — the signals below are cues, not a literal router. Read the
chosen mode's reference file before assembling the prompt.

| Mode | Route when the brief is about… | Reference |
|------|-------------------------------|-----------|
| `studio-shot` | a product on a neutral / clean / white / studio / catalog / packshot background | `references/studio-shot.md` |
| `lifestyle-shot` | a product in a real-world scene — kitchen, outdoor, cafe, gym, "in use" | `references/lifestyle-shot.md` |
| `closeup-shot` | hands holding, a face-with-product, beauty application, demonstrating | `references/closeup-shot.md` |
| `pin-graphic` | Pinterest, a pin, pinnable, a vertical 2:3 pin | `references/pin-graphic.md` |
| `web-banner` | a hero, banner, website / landing / email header, wide format | `references/web-banner.md` |
| `carousel` | a carousel, slide post, multi-slide, swipeable, "X slides" | `references/carousel.md` |
| `ad-pack` | ads, an ad pack, ad creatives, paid social, Meta / TikTok / Pinterest ads | `references/ad-pack.md` |
| `on-model-shot` | a model wearing it, virtual try-on, on-body, fashion shoot, lookbook | `references/on-model-shot.md` |
| `concept-shot` | levitating, floating, splash, frozen motion, surreal, CGI-style, sculptural | `references/concept-shot.md` |
| `makeover` | changing an **existing** image's aesthetic, mood, or season without changing the subject | `references/makeover.md` |

When two modes could apply, prefer the **more specific** one:

1. **Platform over scene** — "a Pinterest pin of my product on a kitchen counter" → `pin-graphic`.
2. **Layout over scene** — "a hero banner of my product in use" → `web-banner`.
3. **Deliverable structure over scene** — "a carousel of my product in different scenes" → `carousel`.
4. **Interaction over general context** — "a closeup of someone applying my serum" → `closeup-shot`.

`makeover` is image-to-image only — it needs a source image (a prior result or a supplied photo).

### Step 2: Get any missing inputs

Don't generate with a load-bearing detail missing — but ask only for what the brief needs, and
**bundle up to 4 questions into one ask**: variant count, style direction, aspect ratio, and brand
colors.

If the user signals they don't want to be asked (e.g. "just do it", "no questions") and a product is
described or supplied, skip the questions and use defaults — **1 image, the mode's default look,
`square`, neutral palette** — then state the chosen settings in one line before generating.

If the mode needs a product photo for fidelity (closeup, on-model, makeover) and none was supplied,
ask for one.

### Step 3: Assemble the prompt

The mode file lists the parts to write — product, composition, lighting, camera, style, what to avoid,
and so on. Be specific — avoid vague words like "nice" or "professional". Use the helpers for these:

- `references/style-descriptors.md` — the style direction.
- `references/negative-prompts.md` — what to avoid.
- `references/typography.md` — read when you need to render any text on the image.

Inject brand colors as exact hex codes when given. With a supplied product photo, state what stays
fixed (packaging, label, proportions) and what the scene changes.

### Step 4: Generate

Call `image_generate` with a `requests` list — one object per image, each carrying the prompt, the
`model` the mode file names, an `aspect_ratio`, and `reference_images` for a supplied product photo or
the `makeover` source. `aspect_ratio` is one of `1:1`, `16:9`, `9:16`, `4:3`, `3:4` — choose it from
where the image will run (a feed post, a story, a wide banner), unless the mode fixes it. Batch several
variants (different prompts or ratios) as more objects in the one `requests` list.

## Edge cases

- **Fits no mode** → default to `studio-shot`; if the brief isn't about a product at all, say so
  rather than forcing a product mode.
- **`makeover` with no source image** → ask for the image first; it cannot run text-to-image.
- **Multi-output with no confirmed outline** → draft and confirm before spending any generation.
- **Safety/NSFW rejection** → remove the sensitive wording and retry once.
- **`reference_images` rejected on count** → the error states the model's limit; drop to it.
- **`error: "no_provider_configured"`** → relay the tool's `hint` (the user must set their key).
