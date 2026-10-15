# Reading the brand

What to read off the homepage's text — what the brand sells, its logo, tagline, audience, how it
writes, what it says sets it apart, and the proof it offers for it. The extraction call returns the
page's text (`data.markdown`); read each field below off it yourself. The names are the fields
`brand.md` is written from. The palette and the type are not among them: the call's `branding` result
reads them from the rendered page (below).

The text is markdown made from the page, so separate elements are sometimes run together
("4.9/5from5264customers"). Restore the spaces the page plainly shows, and drop the markdown itself —
a link's brackets and URL, `**`, a backslash before punctuation — keeping the words. Change nothing
else in a quote.
Where `data.truncated` is true, the end of the page was cut: say so rather than reading the cut as the
page having nothing more.

## The fields

```

brand_name — the brand's own name, spelled and capitalised as the brand writes it, not as the domain
spells it.

what_it_sells — what the business actually offers, said plainly: the category it is in and the kind of
thing a customer ends up buying. Be specific enough that someone who had not seen the page would know
what this business is — a phrase that would fit any company in the sector says nothing. Say how it is
sold where the page makes that clear. Read it from what the page puts on sale and shows, not from the
tagline, which is usually a slogan rather than a description.

logo_url — the URL of the brand's own logo or wordmark, as it appears in the header or the footer.
Take the brand's own mark and nothing else: not a partner's logo, a payment or certification badge,
an app-store button, or a social icon. Prefer the header's mark, and prefer a vector or transparent
file where the page offers one. Where the brand sets its name as plain text rather than an image,
leave it out.

hero_reference_urls — the URLs of the large images the page leads with, whatever they show: people,
products, environments, or any mix of them. These are the images carrying the brand's own art
direction, so judge them by prominence on the page rather than by subject. Leave out what is not one
of them: an icon, a partner's or payment provider's logo, a plain gradient or texture with no
subject, or artwork from the footer. Where you cannot tell what an image is, leave it out.

tagline — the line the brand leads with, where the page has one. Omit otherwise.

target_audience — who the page says this is sold to, in the page's own terms. Omit where the page does not say.

voice_descriptor — one or two lines of ordinary language describing how the brand writes: how formal
it is, how warm, how plain or technical, whether it addresses the reader directly, how long its
sentences run, and any habit of phrasing or punctuation that recurs across the page.

voice_examples — up to six of the brand's own sentences, copied exactly, chosen because they sound the
way the brand sounds. Take them from body copy and headings, not from navigation, buttons, legal text
or anything written by someone else. Reproduce them word for word, including the punctuation and
capitalisation — a tidied-up sentence is no longer an example of the voice. Take fewer where the
page has little writing on it, and omit where it has none.

key_differentiators — what the brand says sets it apart, as separate points in its own words. Take
as many as the page makes and no more. Omit where it makes none.

proof_points — the specific, checkable claims the brand makes about itself on this page, each quoted
exactly as written: star ratings and review counts, how many customers or units it claims, named
testimonials and the person they are attributed to, awards, certifications, press mentions, and
guarantees. Take only what the page states outright. Do not total, round, convert or combine a
number, and do not carry over a boast with nothing behind it — "loved by thousands" is not a proof
point unless the page says how many. Omit where the page makes no such claim.

Report only what this page evidences. Where you cannot evidence a field, leave it out rather than
filling it with a guess or a placeholder — a missing field is a usable answer, an invented one is not.
Do not fill any field from what is conventional for this kind of business.
```

A field the page doesn't evidence is unconfirmed — never zero-fill it. Read every field before
writing: the page text is long, and a field skipped is a gap that was never really there.

## The palette and the type

Take them from the call's `branding` result, which reads them off the rendered page — never from the
page's text, which carries no styles. The values are real; the role names are the
reader's best guess, so write each one with the role it came with.

- **Palette** — `branding.colors`, each key (`primary`, `secondary`, `accent`, `background`,
  `textPrimary`, `link`) with its hex. Leave out a text colour that barely contrasts with the
  background: that is a misread, not the brand's text. An achromatic brand really is black, white and
  grey; that is a palette, not a missing one.
- **Typography** — the heading face is the first name in `branding.typography.fontStacks.heading`, the
  body face the first in `fontStacks.body`, copied exactly; where there are no stacks, take
  `typography.fontFamilies.heading` and `.primary`. `branding.fonts` gives each family's role
  where the stacks don't (a `monospace` face is for labels and code, not the body). A stack that starts
  with a generic or system font (`system-ui`, `ui-sans-serif`, `-apple-system`, `sans-serif`, `serif`)
  names no brand face: write it as the system font. Where nothing names a heading face, the heading is
  unconfirmed.

- **Logo** — `branding.logo` is the mark the page renders in its header. Use it where the page
  text gives no `logo_url`. Where neither gives a link, the page may draw its logo inline: say the
  logo isn't available as a link, not that the brand has none.

Where `branding` is missing or carries no colours or fonts, the skill's Step 4 reads them off the
screenshot and the photographs instead. Only where those show none either is that part unconfirmed.

## Traps

- **A logo or an icon taken as a hero image.** `hero_reference_urls` excludes them; drop any that slip
  in. Hero images are the ones the page leads with, not marks on white.
- **Every call is billed, including one that returns nothing.** A misspelled domain costs the same as
  a good pull.
