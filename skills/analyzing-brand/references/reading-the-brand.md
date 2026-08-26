# Reading the brand

The prompt that reads a brand off its homepage — what it sells, its palette, typography, logo,
tagline, audience, how it writes, what it says sets it apart, and the proof it offers for it. Send it
verbatim as the extraction call's `prompt`, with the homepage as the `url`.

## The prompt

```
Read this homepage and return the brand's identity as strict JSON, using exactly these keys.

palette_hex — the brand's colours, as lowercase six-digit hex strings beginning with '#'. Take the
colours the page declares first: custom properties, inline styles, any colour tokens it defines.
Where it declares none, read them off what is rendered — the dominant tones of the main imagery, the
fill behind the header and the buttons, and any colour in the wordmark itself. Return the colours the
brand actually uses and no others: a brand built on two colours has two, and one that is entirely
black, white and grey is an achromatic brand rather than a missing palette. Where the page gives you
nothing to read a colour from, return an empty array.

palette_source — how you arrived at palette_hex: "declared" where the codes came from the page's own
tokens or styles, "observed" where you read them off what is rendered, "none" where the page gave you
nothing.

brand_name — the brand's own name, spelled and capitalised as the brand writes it, not as the domain
spells it.

what_it_sells — what the business actually offers, said plainly: the category it is in and the kind of
thing a customer ends up buying. Be specific enough that someone who had not seen the page would know
what this business is — a phrase that would fit any company in the sector says nothing. Say how it is
sold where the page makes that clear. Read it from what the page puts on sale and shows, not from the
tagline, which is usually a slogan rather than a description.

typography_font_family — the font-family as the page declares it, copied exactly, including names
that look proprietary or unfamiliar. Omit where the page declares none.

typography_descriptor — one line of ordinary language describing how the type looks: its weight, its
style, its character. Omit where you cannot see the type well enough to describe it.

typography_reference_url — a URL showing the type in use, where the page offers one. The homepage
itself is not a specimen — omit this key rather than pointing back at the page being read.

logo_url — the URL of the brand's own logo or wordmark, as it appears in the header or the footer.
Take the brand's own mark and nothing else: not a partner's logo, a payment or certification badge,
an app-store button, or a social icon. Prefer the header's mark, and prefer a vector or transparent
file where the page offers one. Where the brand sets its name as plain text rather than an image,
omit this key.

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
capitalisation — a tidied-up sentence is no longer an example of the voice. Return fewer where the
page has little writing on it, and omit where it has none.

key_differentiators — what the brand says sets it apart, as separate points in its own words. Return
as many as the page makes and no more. Omit where it makes none.

proof_points — the specific, checkable claims the brand makes about itself on this page, each quoted
exactly as written: star ratings and review counts, how many customers or units it claims, named
testimonials and the person they are attributed to, awards, certifications, press mentions, and
guarantees. Take only what the page states outright. Do not total, round, convert or combine a
number, and do not carry over a boast with nothing behind it — "loved by thousands" is not a proof
point unless the page says how many. Omit where the page makes no such claim.

Report only what this page evidences. Where you cannot evidence a key, omit it rather than filling it
with a guess, an empty string or a placeholder — an omitted key is a usable answer, an invented one
is not. Do not fill any field from what is conventional for this kind of business.
```

A key that comes back absent or empty is unconfirmed — read it that way, never as the brand's real
answer, and never zero-fill it.

**`palette_source` is what separates a real palette from a missing one.** `declared` and `observed`
are both genuine readings — an achromatic brand really is black, white and grey. Only `none` means no
palette was found.

## Traps

- **A logo or an icon returned as a hero image.** The prompt excludes them; drop any that come back
  anyway. Hero images are the ones the page leads with, not marks on white.
- **Every call is billed, including one that returns nothing.** A misspelled domain costs the same as
  a good pull.
