# Ratios and safe zones

Which shapes each channel takes, and where the platform draws its own interface over the ad.

## The ratios per channel

| Channel | Ratios | Notes |
| --- | --- | --- |
| Meta ads — Facebook & Instagram | `4:5`, `9:16`, `1:1` | `4:5` and `9:16` carry most delivery; `1:1` where square placements are in the plan |
| Instagram | `4:5`, `9:16` | `4:5` feed, `9:16` Reels and Stories |
| Facebook | `4:5`, `9:16`, `1:1` | add `16:9` only where the material is genuinely landscape |
| LinkedIn | `1:1`, `16:9` | `1:1` is the default; vertical reaches mobile only, never desktop |
| YouTube | `9:16`, `16:9` | `9:16` Shorts, `16:9` the watch page |
| Reddit | `4:5`, `1:1` | `4:5` is strongest in the mobile feed |

Where the user names a channel not listed here, work to the closest one and say which you used.

## The safe zones

The margin the platform paints its own furniture over. Anything that has to be read — the headline, the
price, the offer, the call to action — stays inside the area left over.

**Vertical `9:16` — the one that matters.** Facebook and Instagram Stories and Reels have shared a
single safe zone since March 2026, built around Reels as the tightest, so one set of margins clears all
four:

- **top ~14%** — account name, follow button, progress bar
- **bottom ~35%** — caption, audio attribution, and the platform's own call-to-action button
- **~6% each side** — the like, comment and share rail

That leaves roughly the middle half of the frame. Build to the Reels number rather than the looser
Stories one; an ad that clears Reels clears everything.

**YouTube Shorts**, also `9:16`, is shaped differently: the title and channel name run along the
**bottom fifth** and the like, comment, share and remix column runs up the **right-hand edge**.

**Feed shapes — `4:5`, `1:1`, `16:9`.** Very little is drawn over the image itself, but the platform
sets the headline and button directly beneath it, so a call to action drawn at the bottom edge of the
frame collides with the real one. Keep the lower strip clear.

## What this means for a resize

The commonest failure is a square ad whose copy sat comfortably in the lower half being rebuilt at
`9:16` with that copy still low — where it lands under the caption and the button. **A vertical rebuild
is a rearrangement, not a scaling**: something has to move out of the covered band, and what moves
depends on the ad. Lifting the headline and letting the product take the space below it is one way that
often works; a different ad may want the product high and the offer in the middle instead.

State the margins in the prompt as regions of the frame. They cannot be applied after the image exists.

## Before handing back

- Every drawn string sits inside the safe area for its shape.
- No call to action where the platform paints its own button.
- The vertical built to the Reels margins, not the Stories ones.
- Specs move: confirm anything load-bearing in the channel's own ads manager.
