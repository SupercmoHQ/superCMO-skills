# Pipeline — from length to boards, story, and script

The duration split is universal. The arc roles in the table are defaults for the **review** format only
— the try-on, tutorial, and unboxing packs set their own fixed arcs, so use the mode pack's arc when it
gives one.

## Step 1: Split the length into boards

- One board becomes one clip.
- A single clip caps at ~15 seconds; longer videos split across more boards.
- Every clip is at least 4 seconds.

| Total length | Boards (N) | Per-clip lengths        | Default arc roles (review)      |
| ------------ | ---------- | ----------------------- | ------------------------------- |
| 4–15s        | 1          | the full length         | one full arc                    |
| 16–19s       | 2          | split evenly, ≥4s each  | hook+setup · apply+closer       |
| 20–30s       | 2          | 15, remainder           | hook+setup · apply+closer       |
| 31–45s       | 3          | 15, 15, remainder       | hook · main · closer            |
| 46–60s       | 4          | 15, 15, 15, remainder   | hook · reveal · apply · closer  |
| > 60s        | ceil(D/15) | 15 each, last ≥4s       | hook · …middle beats… · closer  |

The mode pack maps each arc role onto the slots inside a board.

## Step 2: Shape the story and pick the hook

**Default: one story spans the whole video.**

- Lead with a human stake — a pain, an embarrassment, money on the line, a plan about to be ruined.
- The product enters as a **supporting actor at 40–60% of the total runtime**, mapped onto the arc: the
  stake lives in the hook, a single "but then" turn opens the middle, and the call-to-action rides
  **inside** the closer's resolution, never as a tacked-on outro.
- Test: the story should still make sense if the product were deleted from it.

Drop to a plain review structure (straight "here's the product, here's why it's good") **only when the
user explicitly asks** for it. Two formats override this: **tutorial** replaces the story with its step
spine (see `mode-product-tutorial.md`); **unboxing** adapts it — the package is the premise and the
surprise is a physical reaction at the reveal (see `mode-product-unboxing.md`).

Pick **one** hook pattern per video — never blend two. Some are text-led (the opening *line* carries
it); some are visual-led (the line lands mid-event and the staging carries it). Write the chosen pattern
into the first board as one plain staging sentence.

| Pattern | Lead | What the opener is |
| ------- | ---- | ------------------ |
| Mid-collision   | visual | Begin already inside a physical moment at its peak — a package tearing, something caught before it drops, a near-trip — with the first word arriving while the motion is still under way. |
| Dropped-in      | text | Start as though the camera cut in several words deep, catching the speaker already confiding something at low, private volume. |
| One-thing-off   | visual | An ordinary scene where a single element is plainly wrong, played completely straight; the oddity is only ever shown, and the voice behaves as if it isn't there. |
| Held face       | visual | The very first frame is a face already locked into a reaction; hold it a short beat (≤0.7s), then let the opening line arrive. |
| Direct callout  | text | The first line comes at the viewer as a dare or accusation, paired with a small lean toward the lens. |
| Quirk-up-front  | visual | The quirk is literally the first thing that happens, before any context — available only when a quirk was opted in. |
| Ending-first    | text | The finished outcome is already on screen, unexplained, and the first line reaches back at it ("Six days later my inbox is finally empty — let me back up."). For multi-board videos the visible outcome is the **human** result, never the product. |
| Borrowed clip   | visual | *(advanced, story mode, needs a product image)* Slot 1 of board 1 poses as found, re-shared product-only footage (grainier light, no face); one hard cut into slot 2 where the creator is already mid-reaction, product in hand. The creator shows up one slot later than usual. |

## Step 3: Write the monologue

Write the script yourself, before building boards, matching the word count to each clip's length so it
can be said naturally:

| Clip length | Spoken words |
| ----------- | ------------ |
| ≤ 10s       | 12–20        |
| 11–12s      | 20–28        |
| 13–15s      | 28–35        |

Split it into one segment per board, in order. The segment for each board is passed into that board's
video prompt (Step 8) as the spoken line — the video model voices it in the same pass that renders the
motion.

**Rules across all formats:**

- **First word is hook content.** The literal first word of every board's segment must land on
  something worth hearing — never a filler opener: OK, Okay, Okay so, Alright, So, Yeah so, Right so,
  Um, Well, Like, Wait, Wait what, Hold on. (Positional — these are fine mid-sentence, only banned as
  the first word.)
- **Greet and introduce the product in board 1 only.** Later boards continue mid-thought — no
  re-greeting, no re-introducing who they are or what the product is.
- **One peak reaction per clip, at most**, in the written monologue.
- **Every claim carries one concrete** — a number, a time, a named comparison. Praise with no concrete
  gets cut. Friction openers beat enthusiasm ("I was one click from sending it back" outperforms "I
  love this").
- **Cut echoes and repeats first** — they carry no information and still spend the word budget. No
  phrase repeats across boards.

**Anti-slop — never let these through:**

- Banned openers: "Okay wait", "Okay so", "OMG", "Hey guys", "So basically", "Stop scrolling", "You
  NEED this", "Story time".
- Banned anywhere: "literally", "obsessed", "game-changer", "holy grail", "changed my life", "hits
  different", and corporate words — "elevate", "seamless", "effortless".
