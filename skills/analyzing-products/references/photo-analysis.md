# Photo analysis — reading a product from its picture

When the input is a product photo with no URL and no description, **call `image_analysis` on the photo**
to pull the four facts below **before writing any prompt** — this step is mandatory, and getting the
details right keeps the product true to life. Always route the image through `image_analysis`; don't
rely on reading it yourself, so the analysis is consistent no matter which model is driving.

Prompt to pass to `image_analysis` (asks for all four at once):

> *Look at this product and report: (1) exactly what it is — the precise product type, not a vague
> category; (2) how a person actually uses it — worn, held and operated, applied, sprayed, poured,
> ridden, plugged in, or whatever fits this product; (3) any parts that open, move, or operate — a cap,
> lid, hinge, zip, buttons, or controls — and how they work, or none if there are none; (4) the key
> visual details to keep identical — color, shape, material, size, labels, and the distinctive features
> that make it recognizable.*

## 1. Category — name it precisely

Say exactly what the product is, down to its form — a matte liquid lipstick, a roll-on deodorant, a
scented soy candle, a pair of wireless earbuds — not a broad bucket. "Audio gear" is not an answer;
"over-ear noise-cancelling headphones" is.

## 2. How it's used

How a person actually uses or handles the product — worn, held and operated, applied, sprayed, poured,
ridden, plugged in, consumed — whatever fits what it actually is. Name the specific real action, not a
vague "uses it"; the wrong action makes the depicted use look fake.

## 3. Moving or opening parts

Any parts that open, move, or operate — a cap or lid, a hinge, a zip, buttons, a switch, a clasp — and
how they work. Where something opens before use (a cap before spraying, a lid before scooping), the
opening comes first. Skip this if the product has no such parts.

## 4. Key visual details

What must stay identical everywhere the product appears: color, shape, material, size, and any labels —
plus the distinctive features that make it recognizable (logo placement, silhouette, texture, hardware,
stitching, finish).

## Hand off

These four facts feed the generation prompt. Photo mode produces no new files — the caller uses the
user's attached photo directly as the reference.
