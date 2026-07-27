# Mode — makeover

Take an existing image and transform its aesthetic, mood, or season while preserving the subject,
composition, and identity. A styling overlay, not a new scene — image-to-image only.

- **Model:** `nano-banana-2`, or `seedream-4.5` / `gpt-image-2` for reference-faithful edits.
- **Requires a source image** in `reference_images` (a prior result or a supplied photo).
- **One image per restyled variant**; the output keeps the source's orientation.

## What to shift

Shift the **aesthetic** (e.g. Japandi, old-money) and/or the **season** (e.g. festive winter, autumn
harvest) — either alone or combined. Describe the target as surfaces, palette, and light, not just a
label.

## Prompt template

- `[SOURCE]` — restyle the referenced image; preserve subject identity, composition, product details.
- `[TRANSFORMATION]` — the full shift into the chosen aesthetic + seasonal presets.
- `[AESTHETIC SHIFT]` — specific surfaces, textures, mood of the new style.
- `[SEASONAL SHIFT]` — holiday elements, color changes, atmospheric tone (if Axis 2 used).
- `[PALETTE]` — shift toward the preset's colors while keeping product branding recognizable.
- `[LIGHTING]` — new direction, Kelvin, highlights matching the aesthetic.
- `[TEXTURE & SURFACE]` — tactile surface changes (concrete → marble, or rustic linen).
- `[STYLE REFERENCE]` — anchors for the target aesthetic from `style-descriptors.md`.
- `[PRESERVATION DIRECTIVE]` — subject structure, framing, and camera angle stay unchanged.
- `[QUALITY MARKERS]` + `[AVOID]` — ban altering the core product or mixing conflicting aesthetics;
  Universal + Anti-aesthetic-mixing.

## Composition rules

- Subject, framing, and camera angle stay locked — only styling, palette, lighting, and season change.
- Commit fully — no original background or color scheme bleeding through.

## Aim for

1. Subject, packaging, and composition preserved from the source.
2. New style fully realized — no original-aesthetic bleed-through.
3. Colors match the target preset.
4. Orientation matches the source.
