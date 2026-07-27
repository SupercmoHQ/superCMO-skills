# Clip craft — writing the video prompt for one board

Turn **one storyboard board** into **one vertical clip with spoken audio**. Rules are
format-agnostic; the mode pack adds per-format cut beats and audio. You build a single `prompt` string
and hand it to the video tool.

**Model:** `veo3.1-fast`. **Aspect:** `portrait` (gives the vertical clip). **Audio:** `generate_audio=true`.

```
video_generate(
    prompt=<the string you build here>,
    model="veo3.1-fast",
    start_image=<the board image>,
    reference_images=[<creator reference>, <product reference>],
    aspect_ratio="portrait",
    duration=<int seconds>,
    generate_audio=true,
)
```

The spoken monologue is produced **in the same pass** by `generate_audio=true` — no separate
voiceover step. The words you place in the audio section are what gets spoken.

## What you get and what you produce

You are handed:

- The **board image** — a strip holding the board's vertical slots side by side (standard board has three).
- The **creator reference** and, when the product appears, the **product reference**.
- Metadata: this board's index `K`, total board count `N`, clip `duration` in whole seconds, the
  board's arc role, and the **monologue segment** — the exact spoken lines for this one clip.

You produce a single prompt string in the six-section structure below. Nothing else.

## The six sections, in this order

1. **Style & mood** — the lighting read plus the camera-POV cadence language.
2. **Narrative summary** — one sentence stating what happens in the clip.
3. **Dynamic description** — the per-cut action, one cut per board slot.
4. **Static description** — the setting and ambient detail.
5. **Audio** — the monologue segment distributed across the cuts.
6. **Quality suffix** — the fixed closing line, tuned to the POV cadence.

## Read the board as beats to animate — never transcribe it

Pull each slot's POV (selfie vs tripod), framing distance, action, product placement, and expression.
Use these to stay **consistent** with the board — but do not put the still panel into words. Render
the story **beat** in motion: the breath, the micro-expression, the small physical change between one
instant and the next.

Rule of thumb: if a sentence in a cut would read as a **caption** for the static panel, you are
transcribing — rewrite it as movement, change, or kinetic detail.

## Each slot becomes one cut

Map the board's slots left-to-right onto cuts: slot 1 → Cut 1, slot 2 → Cut 2, slot 3 → Cut 3. Each
cut header carries its framing distance and POV, taken from that slot. The cut then describes the
action, hand allocation, micro-beats, evolving expression, and product placement for that segment.

### The cut marker

Place the literal token `Hard cut to.` at the **end of every cut except the last** — written verbatim,
ending Cut 1's description and Cut 2's description. Put **no** marker after the final cut. Without these
markers the cuts blend into one continuous move instead of snapping apart.

### Time-slicing the cuts

Split the clip `duration` across the cuts, weighted slightly toward the payoff at the end:

| duration | Cut 1 / Cut 2 / Cut 3 |
|----------|-----------------------|
| 4s       | 1.5 / 1.5 / 1         |
| 6s       | 2 / 2 / 2             |
| 10s      | 3 / 3.5 / 3.5         |
| 12s      | 3.5 / 4 / 4.5         |
| 15s      | 4.5 / 5 / 5.5         |

Label each cut with its time window, e.g. `Cut 1 (0-4.5s)`.

## POV cadence → the style & mood line

Set the camera language on the style & mood line from the board's per-slot POVs:

- **All slots selfie** → front-facing camera, intimate handheld feel.
- **All slots tripod** → locked-off on a tripod, completely static, frozen frame.
- **Mixed** → name the alternation explicitly, e.g. "starts SELFIE, hard-cuts to TRIPOD, hard-cuts
  back to SELFIE — POV alternates per cut."

Prefix the style line with the everyday-phone look; end it with the vertical-format note.

## Action language per cut

### Tripod cuts are locked off

Camera is absolutely frozen — zero movement of any kind. Only the person's hands and face shift inside
the fixed frame. **Never** use these words for a tripod cut: `handheld`, `shake`, `drift`, `wobble`,
`sway`. State plainly that the frame does not move.

### Selfie cuts are handheld, and the phone is never an object

A selfie cut has a natural handheld micro-shake — the camera **is** the phone. The phone itself is
**never** a visible object: no phone in hand, no phone held up to the face, no screen. Show only an arm
or forearm at the frame edge holding the camera off-frame. **Never** use these phrasings in a selfie
cut: `mirror selfie`, `looking at her phone`, `phone in her hand`, `holding phone up to face`,
`reflection`.

### Hand allocation

- Selfie cut → one hand is free (the other is off-frame holding the camera).
- Tripod cut → both hands are free.

Allocate the product interaction to hands actually free in that cut.

### One product action per cut

Each cut depicts **at most one** physical product interaction — no repeated actions, no back-and-forth
within a cut.

- Spell out the concrete hand mechanics step by step instead of "opens it / uses it." A spray, say,
  might run grip the body → thumb the cap off → depress the pump → fine mist on the wrist; a wind-up
  balm → uncap → twist the base up → drag it across; a dropper serum → loosen the top → draw the
  pipette out → pinch the bulb. Use whatever sequence the actual product demands.
- **Cap or lid removal is its own distinct motion** — call it out clearly before the action it
  precedes; it counts as that cut's one state change.
- **Body-part target lock** — application lands on the correct target and only that target: perfume →
  wrist or neck; lipstick → lips only; a drink → mouth; cream/serum → fingertip then face. If a request
  implies the wrong target, silently correct it.
- Optional quirk beat for products that leave a residue (a milk-foam lip line, a gloss smear, a smudge
  of sauce): at most one per clip, landing after the main action.

### Micro-beats and expression

- Give each cut **several** micro-beats (aim for around five), including **at least one** within-cut
  motion beat — something that physically changes mid-cut.
- **The expression evolves every cut** — never the same expression twice across the clip.
- Slip in at least one unguarded micro-beat per clip: an eye-flick, a mid-thought stumble, a quick
  self-correction.
- Add one small playful, goofy moment per clip (tongue-out, mock face, eyebrow waggle) — skip this for
  refined or clinical tones.

### Never write these

Avoid the flat, dead-giveaway actions: "smiles at camera", "looks at camera", "holds the product and
talks", or the same expression repeated across cuts.

## Audio

The monologue segment is spoken by `generate_audio=true`, so what you write here is what is heard.

- **Distribute** the monologue segment across the cuts, breaking at natural phrase boundaries so each
  cut carries its own chunk.
- **No phrase repeats across cuts** — each cut's audio is a distinct piece of the monologue.
- **First board (`K = 1`)** may open with one to three bracketed non-verbal sounds before the words,
  e.g. `[*explosive gasp*]`, `[*hyped yelp*]` — skip these for a calm-tone brief.
- **Later boards (`K > 1`)** open **mid-thought**: no greetings, no re-introducing the product, no
  bracketed sounds. Drop straight into the next beat of speech.
- The monologue itself is written in `pipeline.md` (story shape, hook, word count). Here you only
  place it — keep its first-word and anti-slop constraints intact.
- **Forbidden opening words** (never the first spoken word): OK, Okay, Alright, So, Um, Well, Like,
  Wait, Hold on.
- **Forbidden AI-tell phrases** — replace with specific, sensory language: "I'm obsessed", "you have to
  try this", "game changer", "10/10", "it's amazing", "literally", "holy grail", "hits different", and
  corporate words ("elevate", "seamless", "effortless").

## Static description

One or two sentences on the setting, matching the board: the room, its materials and ambient details,
and the light direction. Keep the light **neutral daylight** — never golden hour, never a warm sunset
cast.

## Quality suffix

Close with a fixed final block, adjusting only the movement language to match the POV cadence:

> Facial features clear and undistorted, consistent clothing throughout. Shot on iPhone, natural
> lighting, social media aesthetic, [POV-matched movement language]. No on-screen text, no subtitles,
> no captions, no watermarks.

For a mixed clip the movement language reads like "handheld micro-shake during selfie cuts, locked-off
frozen frame during tripod cuts."

## Universal guardrails

- **Product angle lock** — the product only ever shows its front-facing side; it never rotates, spins,
  or reveals an unseen face.
- **One product instance** — exactly one of the product, never duplicated or multiplied.
- **State-change budget** — at most one product state change per cut; anything removed (a cap)
  disappears and does not reappear.
- No extra background people; age-blind casting; no mirrors or reflections; no visible phone in any frame.
- If the person exits the frame, they are gone for the rest of the clip.
- Keep it simple: at most three people in a shot, at most a handful of visual beats per shot.

## Self-check before you finish

Run this list against the prompt string before handing it to the tool:

- [ ] Six sections present and in order (style & mood → narrative → dynamic → static → audio → quality
      suffix).
- [ ] Each board slot became one cut, each cut labeled with its framing distance, POV, and time window.
- [ ] `Hard cut to.` verbatim ends every cut except the last; none after the last.
- [ ] Tripod cuts read as frozen — none of `handheld`/`shake`/`drift`/`wobble`/`sway`.
- [ ] Selfie cuts have handheld micro-shake and never show the phone as an object.
- [ ] Hands allocated to what's actually free; at most one product action per cut; cap/lid removal is
      its own motion; application hits the locked body-part target.
- [ ] Several micro-beats per cut incl. at least one motion beat; expression changes every cut.
- [ ] Monologue distributed at phrase boundaries, no phrase repeated; `K=1` may add bracketed sounds,
      `K>1` opens mid-thought with no greetings/sounds.
- [ ] No forbidden opening word, no AI-tell phrases, no forbidden flat actions.
- [ ] Static description is neutral daylight; quality suffix present with POV-matched movement language.
- [ ] Product angle locked, one instance only, no mirrors/reflections/visible phone.

## After it renders — frozen-frame QA

The list above checks the prompt. Once the clip is back, inspect the **rendered frames** by eye before
it's stitched — evenly spaced stills plus every product close-up and a few mid-word frames:

- [ ] Exactly one hero product — no clones or duplicates.
- [ ] No more than two hands per person; check frame edges and any reflection.
- [ ] Features sold as absent stayed absent (no invented cord, button, or port).
- [ ] Prop states consistent — a cap is on or off across the cut, never both.
- [ ] The label isn't gibberish, mirrored, or a real other brand.
- [ ] Product scale matches the holding hand.
- [ ] Lips aren't doubled or smeared on mid-word frames.
- [ ] Faces match the creator reference.
- [ ] No baked-in text, captions, or subtitles.

A staging failure → fix the prompt and re-render **that one clip**. Lip slippage → trim the spoken
words. This pass is by eye — the generator won't catch these.
