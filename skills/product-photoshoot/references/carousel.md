# Mode — carousel

A multi-slide social post built as **one design problem**, not unrelated images. Every slide shares an
identical visual system and the set follows a narrative arc (hook → body → payoff/CTA).

- **Model:** `nano-banana-2` (`nano-banana-pro` if people feature; `gpt-image-2` for text-heavy covers).
- **One call per slide — the same orientation on every slide.**

## Carousel presets

product-launch · before-during-after · feature-deep-dive · how-to-steps · myth-vs-fact ·
testimonial-series · collection-showcase · tips-list.

## Step 1 — outline first (confirm before generating)

Draft the slide-by-slide outline and present it for approval before any generation:
- Preset + slide count + per-slide role.
- Per-slide copy and which typography Case applies (`typography.md`).

## Step 2 — lock the fixed visual system

Define once, copy **verbatim** into every slide prompt:
- **Palette** — 2–3 brand tones (hex if given).
- **Surface / backdrop** — one texture for every slide (linen / marble / smooth gradient paper).
- **Lighting** — exact Kelvin, direction, highlight softness.
- **Camera** — fixed height and angle (e.g. strict top-down, or 45°).
- **Style** — one set of anchors from `style-descriptors.md` for the whole deck.

## Per-slide prompt template

1. **[VISUAL SYSTEM]** — the locked block above, copied verbatim.
2. `[SLIDE N of TOTAL]` — slide position + outline title.
3. `[CONTENT]` — the product angle / action / feature this slide emphasizes.
4. `[COMPOSITION VARIATION]` — how framing varies (wide reveal → macro detail) within the master rules.
5. `[QUALITY MARKERS]` + `[AVOID]` — ban color / backdrop drift; Universal (+ Anti-flat-band if text
   space reserved).

## Aim for — across the whole deck, not single slides

1. Identical palette across all slides.
2. Consistent backdrop / surface across all slides.
3. Consistent lighting direction and quality.
4. Correct, identical aspect ratio on every slide.
5. Clear narrative arc reads in order.
