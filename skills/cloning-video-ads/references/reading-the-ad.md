# Reading the reference ad

The read has one job: capture the ad completely enough that it could be rebuilt from the notes alone, without the video. Everything the clone keeps is decided here, so an incomplete read is the one failure that can't be recovered later. Capture it as a **timed breakdown** — a line naming the ad's style, then one line per shot tagged with its time span, then a line naming the production qualities. That shape forces every shot and its timing to be written down.

## The whole-ad fields

Named once, at the top and bottom of the breakdown, because they hold across every shot:

- **Format / genre** — what kind of ad it is: a presenter talking to camera, a voiceover over a demo, a product-only montage, a lifestyle scene, motion-graphics, a single unbroken take. The clone is the same kind of ad.
- **Pacing** — how fast it cuts overall, and where the motion holds or accelerates. A three-cut slow burn and a twenty-cut hype reel are different ads even at the same length.
- **Light, colour and mood** — the register the whole thing sits in: warm or cool, bright or shadowed, muted or saturated, calm or frantic.
- **Audio register** — whether it runs on a voiceover, on dialogue between people, or on music and effects with no words; and the genre, tempo and energy of the music or sound. The clone matches the kind, not the exact track.
- **Edit and finish** — recurring transition style (hard cuts, whip pans, match cuts), any on-screen-text treatment, and the overall polish (raw and handheld, or clean and graded).

## The per-shot fields

For **each shot**, on its own timed line, capture:

- **Time span** — the seconds it runs, as `[start-end]`. Spans are contiguous and sum to the ad's full length: `[0-3s]`, then `[3-7s]`, then `[7-15s]`. The number of shots is the number of real cuts in the ad — a single continuous take is one span from start to finish; a fast-cut ad is one span per cut. Don't invent cuts the ad doesn't have, and don't merge cuts it does.
- **Shot type and framing** — wide, medium, close, macro; and how the subject sits in frame (centred, off to one side).
- **Camera move** — locked, push-in, pull-back, track, orbit, tilt, handheld.
- **What happens** — the action in the shot, in a phrase.
- **The product** — whether it is in this shot at all, where it sits, and exactly what is done to or with it (held up, set down, opened, poured, worn, tapped). This is what later gets re-fitted to the user's product, so it has to be specific.
- **Any person** — that someone is on screen and their role in the shot (presenting, using the product, in the background). Who they are is replaced later, so capture the role, not a fixed identity.
- **On-screen text** — any words that appear, where, and how they are set.
- **Spoken line** — the words said over this shot, quoted, so the rewrite can match their length and rhythm. Roughly is fine; word-perfect isn't needed.

## The breakdown format

Ask `video_analysis` to return the read in this shape — a style line, the timed shot lines, a production line:

```
{One line: the ad's style and format.}
[0-Xs] {shot type, camera move, what happens, the product and what's done to it, on-screen text; spoken line quoted inline}
[Xs-Ys] {the next shot}
…
{One line: light, colour, palette, music/sound register, edit feel.}
```

A single-take ad is one span, `[0-{length}s]`. Keep the spans contiguous and summing to the length.
