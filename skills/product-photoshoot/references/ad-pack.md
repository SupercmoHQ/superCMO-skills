# Mode — ad-pack

A coordinated set of static ad creatives for paid social and A/B testing — different hooks, one
consistent brand identity, engineered to stop the scroll in under half a second.

- **Model:** `nano-banana-2` (`gpt-image-2` for variants with rendered headline copy).
- **One call per variant** — vary the orientation across variants for the placements you're testing.
  Higher contrast and saturation than organic — it has to fight a busy feed.

## Hook angles (the heart of ad testing)

problem-solution · curiosity-gap · lifestyle-aspiration · feature-zoom · transformation ·
social-proof · before-after · bold-claim · price-value · urgency · founder-story · comparison.
Each variant tests one hook.

## Step 1 — outline first (confirm before generating)

Draft the pack and confirm before any generation:
- Per variant: hook angle + visual scene + orientation
- Lock the fixed visual system: palette (2–3 brand tones + one high-saturation accent), backdrop
  surface, one set of anchors from `style-descriptors.md`.

## Per-variant prompt template

1. **[VISUAL SYSTEM]** — the locked block, copied verbatim into each variant.
2. `[VARIANT N]` — variant id, hook angle, orientation.
3. `[HOOK VISUAL]` — the composition that delivers this hook.
4. `[COMPOSITION]` — focal anchor on the rule of thirds.
5. `[LIGHTING]` — matched to the hook mood (dramatic shadow for problem-solution; bright clean for
   feature-zoom).
6. `[CONTRAST & SATURATION]` — explicit high contrast and vivid color to stop the scroll.
7. `[STYLE REFERENCE]` — the locked anchors.
8. `[TYPOGRAPHY]` — apply the `typography.md` rule; if copy is added later in ad manager, leave a
   natural calm area, not a flat band.
9. `[QUALITY MARKERS]` + `[AVOID]` — ban flat lighting, generic stock; Universal + Anti-stock-feel
   (+ Anti-text-warp / Anti-flat-band as needed).

## Aim for — across the whole set

1. Palette, surface, and brand identity consistent across all variants.
2. Each variant clearly delivers its assigned hook.
3. Each variant at its intended orientation.
4. Contrast / saturation high enough to stop the scroll.
5. Any reserved text area reads as part of the scene, not a flat band.
