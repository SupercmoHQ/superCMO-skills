# Helper — typography (on-image text)

Image models render empty "reserved zones" as flat color bands or dull gradients. Never force them.
Handle on-image text by one of three cases.

## Case 1 — the user gave exact text to render

Trigger: the user supplies the wording (eg. "the headline should say 'New Drop'", "add 'Sale ends
Friday'"). Treat the text as an **integrated element of the scene**, not a sticker. Put the verbatim
copy in quotes in the `[TEXT]` slot with weight, size hierarchy, and a placement zone (top, bottom,
overlay, sidebar). Use a typography descriptor (eg. "bold condensed sans-serif"); don't name an exact font
family — most are unrenderable. Keep on-image text short. Add **Anti-text-warp** negatives.

## Case 2 — the user will add text themselves later (Figma, Canva, Photoshop)

Trigger: "I'll add the headline in Figma", "leave space for typography", "need a clear area for
overlay". Append a composition block asking for a calm, **tonally-uniform area within the scene**:

```
[COMPOSITION FOR TEXT OVERLAY]
Leave one area of the frame visually calm and tonally uniform — natural soft gradient, atmospheric
blur, or smooth surface — so the user can overlay typography in post. This area must still feel like
part of the scene, NOT a hard-edged empty rectangle.
```
Never use the phrases "clean negative space" or "reserved white space" — they trigger a flat band.
Add the **Anti-flat-band** negatives.

## Case 3 — the brief says nothing about text (default)

Don't mention text, typography, or overlay zones at all. Let the model compose the whole frame freely
for maximum visual quality.
