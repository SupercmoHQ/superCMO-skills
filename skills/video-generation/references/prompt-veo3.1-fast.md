# Prompt guide — veo3.1-fast

Image-to-video with native audio. The default. Best for turning a product or scene image into a short
clip. With a start frame supplied, the frame fixes the look — the prompt carries the **motion**.

## Prompt structure

Describe the clip in this order:

1. **Subject and starting state** — what's in frame and how it begins (matches the start frame, if
   supplied).
2. **Motion** — how the subject moves or animates over the clip ("steam rises", "the model turns to
   camera", "petals drift down").
3. **Camera** — the camera move: "slow push-in", "orbit left", "static locked-off", "handheld drift".
4. **Audio** — what's heard, when `generate_audio` is on ("soft ambient cafe noise", "a single
   whoosh on the reveal"). Omit if no audio.
5. **Pacing / mood** — tempo and tone ("calm and unhurried", "energetic, quick beats").

## Tips

- One continuous action reads best in a short clip — don't pack several cuts into 8 seconds.
- Name the camera move explicitly; "cinematic" alone is vague.
- With a start frame, don't re-describe the look in detail — spend the words on what changes.
