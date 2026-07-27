# Creator portrait — the identity-anchor prompt

Generate the AI creator once as a single photoreal person, then reuse that image as the identity
reference in every board and clip.

**Model:** `nano-banana-pro`. **Aspect:** `9:16` (vertical head-and-shoulders frame).

```
image_generate(requests=[{"prompt": "<the prompt you assemble here>", "model": "nano-banana-pro", "aspect_ratio": "9:16"}])
```

## Mandatory prompt elements

Every prompt must contain all of these:

1. **Beauty floor — four phrases** (lock editorial-grade facial structure, prevent the plastic /
   obviously-AI look, at every tier): `top model-grade facial structure`, `balanced, even features`,
   `a naturally proportioned build`, `real skin texture`.

2. **The selfie look** — the image must read as a real creator's front-camera selfie, not a portrait
   shoot, editorial, or studio session. Bake these phrases in:
   - `a front-camera phone selfie taken at arm's length`
   - `head and shoulders filling the frame, loose handheld framing with a slight natural tilt`
   - `a little off-center and imperfectly framed — unposed, not studio-centered`
   - `phone-sensor grain with real pores and texture kept — no retouching, no skin-smoothing filter`
   - `subject sharp, background drifting softly out of focus like any phone shot`

   Hard-ban these editorial tells: `centered composition`, `minimal / shallow depth of field` as an
   art choice, `glowing skin`, `studio lighting`, `fashion editorial`, `magazine portrait`, and
   posed-smile language like `warm smile at the camera`. End every prompt with this closing block,
   verbatim:

   ```
   Front-camera phone selfie taken at arm's length — head and shoulders filling the frame, loose handheld
   framing with a slight natural tilt, a little off-center and imperfect, unposed. Sensor grain and true
   skin texture kept, no retouching, no skin-smoothing. A genuine creator phone selfie, NOT an editorial
   portrait, NOT a fashion magazine shot.
   ```

3. **No products** — describe only the person (appearance, expression, hair, build, wardrobe, pose,
   the room). Never a product, prop, held object, or anything they interact with; products enter later
   as separate reference images. A portrait with a product in it is a rewrite.

4. **Age and gender** — minimum age 20; if the user asks for a child, minor, or teenager, silently age
   the subject up to an adult. Gender comes from the request; default to a woman if unspecified.

## Build the prompt

### 1. Roll the look

Left to itself the model keeps generating the same face. Draw eight random numbers up front and map
each through `roll % pool_size` to pick one option per axis:

```
python3 -c "import secrets; print(' '.join(str(secrets.randbelow(100)) for _ in range(8)))"
```

| # | Axis | Pool |
| - | ---- | ---- |
| 1 | Age band | early 20s · mid 20s · late 20s · early 30s |
| 2 | Hair color | buttery blonde · icy ash-blonde · warm caramel brown · dark cocoa · mousy light brown · blue-black · rich mahogany red · strawberry copper · silver-white · sun-kissed ombré · bleached face-framing streaks · emerald green · hot magenta · dusty lilac |
| 3 | Hair length & style | collarbone loose waves · waist-length poker-straight · long tousled curls · mid-length with wispy fringe · sharp chin-length bob · cropped pixie · shaggy mullet-lite · clawed-up twist · undone top-knot · loosely pinned half-up · tight cornrows · slicked high pony · freeform locs · close-cropped fade |
| 4 | Build / vibe | lean and sporty · softly curvy · mid-range everyday · small-framed petite · long-limbed tall |
| 5 | Distinctive feature | none (bare) · scattered freckles · tiny nose stud · hoop lip ring · brow-bar piercing · septum hoop · cheek dimples · tooth gap · single beauty spot |
| 6 | Makeup register | no-makeup skin · everyday minimal · lashes-only glow · muted taupe smoke · flirty flicked liner · bright graphic liner · sparkle inner corners · draped cream blush · high-shine lip |
| 7 | Ethnicity / face read | pale Northern-European · olive Mediterranean · East Asian · South Asian · Latin-American · mixed-heritage · Levantine · Eastern-European — convey through facial structure, don't state the ethnicity in words |
| 8 | Wardrobe aesthetic register | oversized-skater · collegiate-equestrian · 2000s-revival · understated-luxe · seaside-neutral · gymwear-jersey · tailored-editorial · soft-bohemian · moto-leather · pared-back-basic |

Two overrides on the roll:

- **User wins.** Any trait the user already specified (hair color, ethnicity, age) skips its roll — use
  what they asked for.
- **Anti-clone.** If this portrait would match the previous creator in the same session on age + hair +
  build, re-roll the clashing axes so the two people look distinct.

### 2. Choose location, tier, and wardrobe

The scene and outfit come from the product's **category** and **tier**, unless the user named a
location. Resolve in this order: (1) user gave a location → use exactly that; (2) otherwise → look up
`(category, tier)` in the matrix; (3) no product context → cozy home (bedroom or living room), casual
everyday outfit.

Read tier from packaging, never price: **luxury** — weighty glass, raised or embossed branding,
restrained mono / gold / black palettes with serif lettering, established houses; **premium** — sleek
contemporary packaging, deliberate typography, good-quality plastic or frosted glass; **drugstore /
mass-market** — vivid colored plastic, punchy type, loud claims; when in doubt, treat as **premium**.

| Category | Tier | Location | Wardrobe base |
| -------- | ---- | -------- | ------------- |
| Cosmetics / makeup / fragrance | Luxury | Upscale contemporary bedroom or dressing nook, designer pieces, wall panelling, feature mirror | Satin / silk robe in deep or muted premium shades, sashed at the waist with the neckline closed; OR designer sleepwear set; OR "dressed to head out, adding the last touch" styled look |
| Cosmetics / makeup / fragrance | Premium | Crisp airy modern bathroom or bedroom | Good cotton robe sashed shut at the waist with closed neckline, smart-casual top, or neutral lounge set |
| Cosmetics / makeup / fragrance | Drugstore | Cheerful everyday bathroom or bedroom, lived-in | Snug oversized cotton robe sashed shut at the waist with closed neckline / soft hoodie / simple fitted top |
| Skincare / haircare / body / shower | Luxury | Spa-style bathroom — stone surfaces, brass fittings, overhead shower, greenery | Silk robe or plush bathrobe in soft muted shades, sashed at the waist with closed neckline |
| Skincare / haircare / body / shower | Premium | Airy modern bathroom, clean tiling, mirror lighting | Oatmeal / cream cotton robe sashed shut at the waist with closed neckline, relaxed loungewear |
| Skincare / haircare / body / shower | Drugstore | Ordinary bright bathroom, lived-in | Cozy oversized robe sashed shut at the waist with closed neckline, casual tee |
| Food / beverage / kitchen | Any | Modern kitchen dressed to tier (luxury: stone counters + brass; premium: pale cabinetry + steel; mass: bright welcoming) | Smart-casual — fitted blouse + jeans, knit top, or activewear if health-themed |
| Protein / supplements / sports nutrition | Any | Home gym (free weights, mat, mirror, plants) OR bright kitchen (post-session) — whichever suits | Activewear / fitted training top, joggers or leggings, just-worked-out |
| Clothing / accessories / jewelry / watches | Luxury | Bedroom or dressing room — clothing rail, feature mirror | Pulled-together "already dressed, this is the final accent" — silk cami + tailored trousers, or refined knit + slip skirt |
| Clothing / accessories / jewelry / watches | Premium | Bedroom / living room, styled up | Smart-casual — easy fitted top, high-rise trousers, a few minimal layered pieces |
| Clothing / accessories / jewelry / watches | Drugstore | Bedroom / living room, everyday cozy | Relaxed casual outfit, comfortable layers |
| Fitness / sports / training gear | Any | Home gym, living-room mat space, or yoga nook with mat + plants + daylight | Training gear suited to the activity (compression top + leggings, sports bra + shorts, running kit, yoga set) |
| Outdoor gear / sunglasses / summer / sunscreen | Any | Outdoor café terrace, park, or sun-lit street, people softly blurred behind | Season- and tier-appropriate — linen shirt, sundress, light set |
| Cars / vehicles | Any | Outside beside the car — driveway, sun-lit street, open garage, walk-around angle, daylight | Sharp casual outerwear — light jacket, well-cut denim/trousers, trainers/boots; tier lifts it (luxury: tailored coat, designer sunglasses) |
| Tech / electronics / audio | Any | Home desk, living room, or studio corner, tier lifts the desk | Smart-casual — fitted knit, button-down, or easy activewear |
| Home / decor / candles | Any | Living room or bedroom with fitting mood, tier lifts materials | Elevated lounge — soft knit, relaxed trousers, cozy set |
| Everything else | Any | Cozy home — bedroom or living room | Everyday casual outfit |

Only go **outdoors** when the product clearly belongs there (cars, summer wear, sunglasses, outdoor /
café lifestyle) — otherwise stay indoors.

The rolled register (axis 8) sets the *style vocabulary*; the tier sets the *material quality*. Apply
both:

| Register | Anchors |
| -------- | ------- |
| oversized-skater | loose graphic tee/hoodie + wide-leg or baggy denim + bulky trainers + stacked chain necklaces |
| collegiate-equestrian | structured blazer + silk neckerchief or cream blouse + leather trims + boxy top-handle bag |
| 2000s-revival | micro skirt or slip dress + snap hair clips + thick choker + tiny shoulder bag |
| understated-luxe | fine merino/cashmere knit + sharp tailored trousers + slim gold pieces + quiet leather goods |
| seaside-neutral | airy linen shirt + off-white wide trousers + plain gold hoops + woven leather sandals |
| gymwear-jersey | loose sports jersey or polo + relaxed shorts/trackpants + headscarf or clip + trainers |
| tailored-editorial | pinstripe/sharp blazer over a base layer + heavy chain choker + oversized sunglasses |
| soft-bohemian | slip dress or silk cami + draped open cardigan + stacked pendants + suede sandals |
| moto-leather | biker jacket over knit/tee + inky denim/trousers + branded cap + ankle boots |
| pared-back-basic | crisp white shirt or plain knit + straight denim/trousers + fine minimal jewelry |

Material tier: **luxury** → silk / cashmere / designer / fine gold; **premium** → good cotton /
branded / careful finishing; **drugstore** → everyday cotton / basic chains / plastic clips. If a
rolled register feels physically wrong for the product (e.g. gymwear-jersey for a high-end fragrance),
re-roll axis 8 once. **Palette agreement:** at least one dominant room color should be picked up
somewhere in the wardrobe.

### 3. Apply modesty

Wardrobe language must be explicitly modest, or the model drifts to plunging necklines that trip
downstream content filters. Wrap **every** outfit with this triplet:

```
front fully done up, the fabric meeting high at the collarbone, cut for full coverage
```

Then layer per-garment specifics:

| Garment | Add |
| ------- | --- |
| Button-down / shirt | done up to at least the second button from the top |
| Knit / sweater / fitted top | a modest crew or scoop neck, nothing V-cut |
| Blouse | a modest closed neck, no deep V or open décolletage |
| Robe / kimono / silk wrap | firmly sashed at the waist with the tie showing, both panels crossing fully over the chest |
| T-shirt | fitted, but with a modest crew neck |
| Tank / camisole / spaghetti strap | **not allowed on its own** — only worn under a button-down, cardigan, or blazer that itself meets these rules |
| Athletic / compression top | a high crew or modest scoop neck fully covering the chest |

Bottoms (jeans, trousers, leggings, skirts) need no extra rule beyond the matrix phrasing. Modesty
always wins over the register × tier styling. **Phrase it positively** — `done up to the collar`,
`crew neck sitting at the collarbone`, `firmly sashed with the tie visible` — not negations like
`no V-neck`; text encoders latch onto negation trigger words (`chest`, `neckline`, `exposure`) and
render exactly the thing you tried to negate.

### 4. Set lighting and expression

- **Lighting:** neutral cool daylight only — phrase it as `cool neutral daylight`, `soft even white
  light`, `plain midday light`, or `flat overcast light`, always with a direction (e.g. from a window on
  the left); state the skin has no warm cast and no retouched glow. Hard-ban warm light (golden hour,
  warm sunset, orange / amber / honey cast, late-afternoon wash) unless the user asks and the story
  needs it.
- **Expression:** never a posed "warm smile at the camera" — use caught-mid-moment expressions:
  `mid-sentence with a small half-smile and eyes drifting just off-lens`, `caught mid-laugh`, or a
  `relaxed, unguarded look`.

### 5. Assemble

Fill this skeleton with the choices above, then append the closing selfie block:

```
A [age band] [man/woman], [caught-mid-moment expression], with [hair color + length/style], [build],
with top model-grade facial structure, balanced even features, a naturally proportioned build, real skin
texture, in a [specific location with architectural detail].
[Cool/neutral daylight, direction + quality] falls across [his/her] face — neutral, clean, no warm cast,
no retouched glow. Skin texture is real, with visible pores and natural unevenness.
[He/She] wears [matrix wardrobe base + modesty triplet + per-garment coverage + register vocabulary at
tier-appropriate material, palette echoing the room].
The background features [specific materials, colors, furniture].
Color palette dominated by [room tones — neutrals, no amber/orange dominance].
Front-camera phone selfie held at arm's length — head and shoulders fill the frame, slight natural tilt,
a little off-center, caught mid-moment. Subject sharp, background drifting softly out of focus like any
phone shot.
[closing selfie block, verbatim]
```

## Worked example

Category = skincare, tier = premium, woman; rolls landed on late 20s / dark cocoa / sharp chin-length
bob / softly curvy / scattered freckles / everyday minimal / East Asian face read / seaside-neutral
register:

```
A woman in her late 20s, mid-sentence with a small half-smile and eyes drifting just off-lens, with dark
cocoa hair in a sharp chin-length bob, a softly curvy build, scattered freckles, everyday-minimal makeup,
with top model-grade facial structure, balanced even features, a naturally proportioned build, real skin
texture, in a bright modern bathroom with clean tiling and soft mirror lighting. Cool neutral daylight
spills in from a window on the right, sitting evenly across her face — neutral cool, no warm cast, no
retouched glow. Skin texture is real, with visible pores and natural unevenness. She wears an oatmeal
cotton robe sashed shut at the waist, front fully done up with the fabric meeting high at the collarbone,
both panels crossing fully over the chest, in a seaside-neutral register — airy linen layered underneath,
plain gold hoops — in good cotton consistent with the premium tier. The bathroom background features pale
stone counters, a folded linen towel, a single potted plant, and a slim brass tap. The color palette is
soft and light — warm off-whites, oatmeal, pale sand. Front-camera phone selfie held at arm's length —
head and shoulders fill the frame, slight natural tilt, a little off-center, caught mid-moment. Subject
sharp, background drifting softly out of focus like any phone shot. Front-camera phone selfie taken at
arm's length — head and shoulders filling the frame, loose handheld framing with a slight natural tilt, a
little off-center and imperfect, unposed. Sensor grain and true skin texture kept, no retouching, no
skin-smoothing. A genuine creator phone selfie, NOT an editorial portrait, NOT a fashion magazine shot.
```

Read the example for *level and structure*, not to copy — every axis is re-rolled per creator, and the
location / wardrobe follow the product's category and tier.

## Reuse

- Once generated, that single image is the creator's identity for the whole video.
- Pass it as the character reference into every board and every clip so the same face, hair, build, and
  wardrobe carry across the storyboard.
- The outfit stays fixed across boards unless the story explicitly changes scene.
