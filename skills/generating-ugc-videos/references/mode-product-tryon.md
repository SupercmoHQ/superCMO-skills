# Mode: try-on (OOTD / fit-check)

**Use when:** all three are true — (a) try-on / wearing / OOTD / fit-check intent, (b) UGC framing,
(c) a specific **wearable** product (top, dress, outerwear, pants, skirt, shoes, bag, jewelry). Miss
any one and it is a different format.

## Models

- **Slots:** four vertical slots in one wide (`landscape`) sheet — a fixed four-slot arc (not three).
- **Board:** `image_generate(requests=[{"model": "gpt-image-2", "aspect_ratio": "16:9", "reference_images": […]}])`.
  References in supply order: `image_0.png` = product, `image_1.png` = creator, `image_2.png` =
  previous board (K > 1). Boards run sequentially so each conditions on the last.
- **Clip:** `video_generate(model="veo3.1-fast", start_image=<board>, aspect_ratio="portrait", generate_audio=true)`
  — one per board, run in parallel, then stitched in board order with hard cuts.

Carry two values through every board and clip:

- **tone** — the emotional register the expression progression follows. Default to a natural, engaged
  register; step up to hyped, or shift cool / playful / posh, only when the brief signals it. Infer it
  from the brief — it isn't a fixed menu to ask about.
- **location tier** — `luxury` · `premium` · `drugstore`, read from the garment's register (never a
  looked-up price). Chooses the home aesthetic.

## Build the board

1. **Lay out board 1's fixed four-slot arc** (do not reorder or drop a slot):

   | Slot | Role            | What it shows                                                                                         |
   | ---- | --------------- | ----------------------------------------------------------------------------------------------------- |
   | 1    | pre-wear        | Creator dressed in a low-key at-home base look, a kraft shopping bag in hand. The item stays **inside, not visible**. |
   | 2    | wearing         | The product is now **worn** — shot full-body or three-quarter on a locked-off tripod, bag no longer in frame.          |
   | 3    | texture close-up| A tight macro reading the fabric, cut, or detail — **hands-free**, with no contact against the garment.                |
   | 4    | styled pose     | Creator has moved to a **different room of the same home** and holds a styled pose that presents the full look.               |

   - The four framings span the distance bands — at least one tight (macro / close-up), one mid
     (waist-up / medium), one wide (three-quarter / full-body). Canonical cadence: waist-up →
     full-body → macro → medium-wide. Four different poses, four different distances (`board-craft.md`).
   - POV cadence: slot 1 selfie (one hand on the phone, one on the bag); slots 2–4 tripod (both hands
     free, phone not in frame). Every POV change lands on a hard cut.

2. **Lay out boards 2..N** — pose / location continuations, no bag, no pre-wear, no twirl:

   | Board | Role         | What it does                                                                                  |
   | ----- | ------------ | --------------------------------------------------------------------------------------------- |
   | 1     | canonical    | The fixed four-slot arc given above.                                                          |
   | 2     | home-tour    | Slot 1 picks up where board 1's final location left off; slots 2–4 travel across other rooms. |
   | 3     | outdoor      | Every slot is set outside; a light rain begins at **slot 2 onward** — hair stays dry, and slot 3's macro catches wet droplets. Avoid any puddle or wet-glass reflection that reveals the creator. |
   | 4     | home-reflect | Indoors again, relaxed in a seated or lounging pose; slot 1 can start as a narration-heavy selfie talking-head. |
   | ≥5    | loop         | Cycle through other indoor rooms or outdoor locations with new pose variations.                |

   For boards 2..N the outfit is the product throughout — never the pre-wear, never the bag.

3. **Map the garment onto the body (worn, not held)** — shoulder seams on the shoulders, waist at the
   natural waist, fabric wrapping the 3D volume of torso, arms, and legs, with folds at the joints.
   Feed product + creator as references (add the prior board as `image_2.png` for K > 1). Primary
   2D→3D mapping happens in slot 2; slot 3 renders a zoomed region of that same garment; slot 4
   re-drapes it in a new pose. Never on a hanger, laid on a bed, or over a chair in the worn slots — it
   is on the body.

4. **Lock the garment identical** across every worn slot — same silhouette, primary color,
   print/pattern, recognizable details (collar, hem, neckline, sleeve, hardware, stitching). It rotates
   with the body but never changes color or print and never gains or loses details; invent nothing not
   visible in the reference. Outdoor-board exception: rain droplets, sheen, or slight temporary
   darkening are allowed — silhouette, color, print, and details stay identical to the dry cuts.

5. **Render a realistic fit** — real-world proportions on the creator's actual body type, natural fit
   and drape, not slimmed, lengthened, or exaggerated. Fabric falls by weight: silk crinkles finely,
   knit in broad folds, denim holds sharp creases, leather catches a sheen. Drape changes with pose (a
   skirt fans out when seated, a jacket creases at the elbow when leaning) while staying the same item.

6. **Place the kraft shopping bag (slot 1 only)** — one plain brown kraft paper shopping bag, present in
   board 1 / slot 1 and nowhere else. Keep it generic — bare kraft, free of any logo, branding, or
   shipping stickers; it is never a delivery box, packing tape, or tissue paper (this is try-on, not
   unboxing — the product already belongs to her). It stays sealed: she doesn't open it, pull the item
   out, look inside, or narrate it to camera. She simply carries it by a single handle at her side, or
   it rests upright on a nearby surface. From slot 2 onward, and throughout every later board, it is
   absent and never comes back.

7. **Keep outfit continuity** — slot 1 of board 1 is the plain pre-wear base outfit: an understated,
   comfortable at-home combination (for example a relaxed top over soft loungewear, or a casual sweater
   with joggers); product not worn. Slot 2 onward and
   all of boards 2..N are the product outfit only. The pre-wear → product switch is implicit across the
   hard cut — never depict the creator changing clothes, never return to the pre-wear look. Hairstyle
   stays locked across every slot and board (`creator-portrait.md`).

## Build the clip

1. **Twirl (board 1, cut 2 only)** — a single unforced rotation that shows the garment's back before
   she comes to rest facing forward. Just the one spin — not repeated, not a continuous rotation.
   Video-level only: the slot-2 board is still a static front-facing full-body pose; put the twirl in
   the clip prompt, never on the board.
2. **Hands-free texture macro (cut 3)** — a tight fabric macro with zero hand contact (no touching,
   skimming, pulling, brushing, or pinching by the creator or any off-frame "operator" hand). Texture
   reads through framing, drape, the light across the fabric, and a natural settling breath; hands stay
   at sides or off-frame. Choose one passive movement cue that suits the garment — for example:
   - Top / blouse / tee — the chest brightens on an inhale and the fabric drifts with a small sway.
   - Dress / skirt — the hem settles as her weight resettles, letting the waist seam show.
   - Pants / shorts — the cloth drops down the leg and the cuff comes to rest on its own.
   - Outerwear — the lapel hangs open, the collar sits, and light rolls across the surface.
   - Knit / denim / leather — the weave surfaces under shifting light, the wash and seam lines register,
     the grain and its sheen answer the direction of the light.
3. **Split the audio by cut, not by POV** — the creator lip-syncs even on a locked-off tripod: cuts 1,
   2, and 4 are lip-synced (the creator speaks on camera, selfie or tripod); cut 3 (the hands-free
   macro) is voiceover (no face in frame); during the twirl in cut 2 the lip-sync briefly pauses as she
   turns away, then resumes. Distribute the board's monologue segment (`pipeline.md`) across the four
   cuts; set `generate_audio=true`.

## Monologue — the personal-want frame

Try-on's default frame is a personal want, not a review:

- Board 1 opens on having wanted / waited for the piece and it finally arriving ("I've wanted this for
  weeks").
- The wearing beat lands the verdict ("okay — it actually fits").
- By the last board the register settles into a lived-in glow ("been in it all day").

The first-word rule, hook menu, and anti-slop are the shared `pipeline.md` monologue.

## Strict rules

- **No mirrors, no reflections** — no bathroom or full-length mirror, no shop-window or phone-screen
  reflection.
- **No end call-to-action** — the video ends on the final cut's spoken line (no "link in bio",
  "follow", "subscribe", no downward gesture at the close).
- **No on-image text** — no captions, headers, badges, numbers, subtitles, or watermarks on the board.
- Outfit continuity, the bag-in-slot-1-only rule, and the mirror ban override any user-supplied scenario.
