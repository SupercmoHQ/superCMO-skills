# Helper — negative prompts (the `[AVOID]` block)

Visual suppressors that block common generative defects. Select the groups the shot needs, merge them,
de-duplicate, and append as one `[AVOID]` block at the end of the prompt.

## Suppressor groups

**Universal — always include**
warped text, fake words, melted geometry, doubled subjects, watermarks, signatures, cartoonish
rendering, plastic waxy surfaces, doll-like skin, airbrushed "AI sheen", flat fluorescent lighting,
harsh on-camera flash, over-sharpened HDR halos, flat empty solid-color background rectangles.

**Anti-uncanny — when hands, faces, or bodies are present** (closeup-shot, lifestyle-shot with people,
on-model-shot)
warped fingers, extra or missing limbs, misaligned facial features, asymmetric eyes, extra teeth,
orange-tan rubbery skin, over-smoothed retouching, stiff unnatural posture.

**Anti-text-warp — when the product shows a label, branding, or logo**
warped label text, garbled letters, fake brand names, melted typography, double labels, fictional
logos.

**Anti-stock-feel — for ads, banners, and lifestyle**
flat clipart, obviously composited backdrops, perfect symmetrical staging, over-clean over-staged
stock-photo environments.

**Anti-aesthetic-mixing — for makeover**
half-applied transformation, mixed conflicting styles, original background or palette bleeding into the
new render.

**Anti-flat-band — when copy space is reserved for later text overlay**
hard-edged flat solid-color rectangle, cropped empty block, dull banding where text will go — the calm
area must read as part of the scene (sky, blurred background, surface).

## How to assemble

1. Read the mode file and the brief.
2. Start with **Universal**. Add **Anti-text-warp** if a label is visible · **Anti-uncanny** if people
   are present · **Anti-stock-feel** for ad/banner/lifestyle · **Anti-aesthetic-mixing** for makeover ·
   **Anti-flat-band** if copy space is reserved.
3. Merge into one `[AVOID]` block and drop duplicate phrases.
