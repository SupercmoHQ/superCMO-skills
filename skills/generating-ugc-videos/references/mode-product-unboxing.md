# Mode: unboxing

**Use when:** UGC, and the creator opens a delivery package on camera with the product reveal as the
peak beat.

## Models

- **Slots:** four per board, side by side in one wide `landscape` sheet — four sequential moments of
  one clip.
- **Board:** `image_generate(requests=[{"model": "gpt-image-2", "aspect_ratio": "16:9", "reference_images": […]}])` —
  four vertical slots in one landscape sheet.
- **Clip:** `video_generate(model="veo3.1-fast", start_image=<board>, aspect_ratio="portrait", generate_audio=true)`
  — one clip per board; the model voices the monologue in the same pass. Hard cuts between slots are
  carried by the `Hard cut to.` markers in the prompt (see `clip-craft.md`).
- **Reference supply order** (so slot text names them consistently — `image_0.png`, `image_1.png`, …):
  product first, then the creator portrait, then the real package photo **if supplied**, then the
  previous board **if K > 1**. Skip the ones that don't apply and the indices shift up.

## Step 1: Handle the package photo

Unboxing takes one input the other formats don't — a photo of the actual delivery box.

1. If the brief already includes a box photo, use it (it becomes one of the `reference_images`, in
   supply order).
2. If the brief never mentions a box and none is attached, **ask** the user: yes (they'll attach one)
   / no (use a generic box) / other.
3. If they say **yes but attach nothing**, ask a second time for the photo and **wait** — do not build
   boards until it arrives.
4. If they say **no** (or never wanted one), use a **generic plain brown cardboard delivery box**:
   sealed with packing tape, no logos, no branding, slightly larger than the product. Never a white
   gift box, never a branded retail box.

When a real box photo is supplied, board 1 must depict *that exact package* — same shape, same
closure, any visible printing preserved.

## Build the board

The four slots must show four different actions at four different camera distances
(`board-craft.md`); identical poses across slots = rewrite.

1. **Lay out board 1's fixed, non-negotiable arc:**

   | Slot | Beat | Content |
   | ---- | ---- | ------- |
   | 1 | **sealed box** | Creator seated behind the shut, tape-sealed, unopened box. Product **NOT visible**. |
   | 2 | **reveal** | Product freshly lifted clear of the box, in hand or set down. Peak surprise. Box shoved to the edge or already gone. |
   | 3 | **product hero** | Product carried alone as the hero — cradled close or pushed toward the lens. Box gone. |
   | 4 | **satisfaction** | Creator at ease with the product in hand — easy, pleased, warm grin. Box gone. |

   Slot 1 of board 1 **must** show the sealed box with the product hidden; the reveal is a slot-2 beat
   — never let slot 1 default to "show the product." **Boards 2..N** are post-reveal continuations:
   keep exploring, using, or demonstrating the product across their own four slots, conditioned on the
   previous board's final slot; no re-introducing the box, no greetings, no re-announcing the product.

2. **Script the box lifecycle** (one box, ever):

   | Slot | Box state |
   | ---- | --------- |
   | 1 | shut, taped, sealed — the focal object |
   | 2 | just-emptied: pushed to the frame edge with its flaps open, **or** already gone |
   | 3 | **gone** |
   | 4 | **gone** |

   After slot 2 the box ceases to exist — never re-introduce, re-close, re-tape, or carry it. It
   **rests on a surface** in slot 1; never held in the air, lifted, or moved. Choose the surface by
   product size: tiny / small (cosmetics, phone, jewelry) → a **table** only; large parcel → table or
   floor; oversized (bicycle, furniture) → **floor** only, creator kneeling or standing beside it. The
   surface matches the room aesthetic and defaults premium/clean (marble or light-wood table, vanity,
   kitchen counter). **Forbidden surfaces:** workbench, garage, industrial or plastic folding tables,
   distressed dark wood, cluttered surfaces.

3. **Apply weight & grip** — classify the product before writing any lift or hold, then match hands
   and face:

   | Class | Examples | Hands | Face |
   | ----- | -------- | ----- | ---- |
   | **Heavy** | appliance, 1L-plus bottle, toolbox-grade | both hands, weight leaned into | evident effort — clenched jaw, knit brow |
   | **Bulky but light** | big carton, large soft toy, tall hollow container | both hands to steady it | at ease, no effort shown |
   | **Light** | small bottle, handset, compact cosmetic | single hand, easy hold | calm / content |
   | **Tiny** | stud earring, capsule, contact lens | gripped between thumb and forefinger | intent / inquisitive |

   One-handed lifts of heavy items are forbidden (they read as AI-fake), as is two-handed strain on
   light items. Never balance a paired / set product on a single palm — one per hand, or one shown and
   one set down. When the class is ambiguous, default to the heavier one.

4. **Add packing paper** — the open box shows crumpled, loosely-folded tissue paper color-matched to
   the product (empty boxes read as unfinished). Atmospheric backdrop only, appearing only while the
   flaps are open — **slot 2 only** (sealed in slot 1, box gone in slots 3–4).

   | Product color | Tissue |
   | ------------- | ------ |
   | pink / red / rose | blush, rose, soft pink |
   | blue / aqua | sky blue, pale blue, aqua |
   | black / dark | ivory, sand, warm grey for contrast |
   | white / light / pastel | muted pastels — lilac, peach, mint |
   | multicolor / brand-led | the leading brand colour |
   | uncertain | ivory or sand (safe premium neutral) |

5. **Set expression + framing** — feelings evolve across the four beats: **anticipation → peak
   surprise → focused admiration → settled satisfaction** (the same expression twice = rewrite).
   Default board-1 POV: **tripod → tripod → tripod-close → selfie** — the sealed box and reveal stay
   tripod so both hands are free; the product hero stays tripod-close, phone out of frame; satisfaction
   lands on selfie for an intimate close (override only for a director-tier brief or a very small
   product; keep POV changes minimal). Distances span the bands — e.g. **medium → medium-close-up →
   macro → three-quarter / wide** — with at least one tight, one mid, and one wide; all in one band =
   rewrite.

## Build the clip

The board is a narrative map, not a frame to trace: it says *which* beat each slot is, not the pose to
copy. Render each beat in motion — weight shifts, breath, micro-expressions, kinetic hand detail. If a
sentence could caption the static panel, rewrite it as movement.

1. **The reveal mechanic (cut 1 → cut 2)** — the signature beat. Closing **cut 1**, the creator
   reaches for a small box-cutter / utility knife lying beside the box, draws it through the tape in
   **one clean stroke** (no dwelling on the blade, no zoom, no studying the knife), and lays it back
   down on the surface. That knife then just sits there — never named, never the focus, never brought
   up again. With the flaps falling open, the color-matched tissue flashes into view for a moment.
   **Hard cut to** cut 2: the product is rising out of the tissue inside the open box, and the box —
   flaps open at the frame edge — is dropping out of focus. Let the hard cut do the box→product
   handoff — don't spell out a slow opening inside cut 2 unless the user asks.

2. **Box presence per cut** — each cut inherits the box state from the lifecycle table above: sealed →
   at-edge / gone → gone → gone. Once the box has left frame it never comes back — no re-taping,
   closing, carrying, or setting it back down. If a real package photo was supplied, cut 1 must show
   that exact package.

3. **Time-slice toward the reveal** — bias the split to the reveal; the product hero is brief;
   satisfaction lands the closer. Each cut ≥0.5s.

   | Clip length | Cut 1 packed | Cut 2 reveal | Cut 3 hero | Cut 4 satisfaction |
   | ----------- | ------------ | ------------ | ---------- | ------------------ |
   | 4s | 1 | 1.5 | 0.5 | 1 |
   | 6s | 1.5 | 2 | 1 | 1.5 |
   | 8s | 2 | 2.5 | 1.5 | 2 |
   | 10s | 2.5 | 3 | 2 | 2.5 |
   | 12s | 3 | 3.5 | 2.5 | 3 |
   | 15s | 3.5 | 4.5 | 3 | 4 |

4. **Audio branching** —
   - **Board 1 (K=1):** you may prepend **1–3 bracketed non-verbal reaction sounds** before the spoken
     line — for instance `[*quick gasp*] [*soft delighted giggle*] [*playful "no way"*]`. Use sparingly, at most three,
     and skip them if the tone is calm. Board 1 may greet and introduce the product.
   - **Boards 2..N:** open **mid-thought** — no greetings, no product re-introductions ("hey", "so this
     is the…", "today I'm showing you…"). It should feel like one continuous take cut into pieces. **No**
     bracketed non-verbals on later boards.
   - Shared: distribute the monologue across the cuts at natural phrase boundaries, no repeated phrases
     across cuts, and avoid the hype tells in `clip-craft.md`.

5. **Cap / lid logic** — if the product is closed and a cut is its application moment, describe the cap
   coming off as a distinct motion *before* the action (even if the board still shows it capped). Once
   removed, the cap is gone for the rest of the clip, and for every later board too.

## Monologue — the reveal frame

Unboxing keeps the shared story shape (`pipeline.md`) with two changes:

- The **package is the premise** — no delayed product entry; the stake is the anticipation of what's
  inside.
- The genuine surprise is scripted as a **physical reaction at the reveal** — a quick catch of breath,
  a small jolt back, a palm flying to the mouth — with one "but then" turn and the call-to-action
  riding inside the closing satisfaction.

For the hook, **Mid-collision is the natural default** (the box mid-open); Dropped-in, Held face,
Direct callout, and Ending-first also fit — **not** Borrowed clip. At most one peak reaction per clip.
