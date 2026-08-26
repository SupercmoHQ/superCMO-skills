# Reading the set

**Identify the strategies the ads are actually using — don't sort them into buckets decided before
the ads were seen.** Name the tactics you find, define them, and only then count them. The set is
read twice over: once across every ad the ledger holds, and once across the teardowns of the ads that
were watched.

**Write it to `ad-set-analysis.md`, in the run's folder alongside `ledger.md`, as you go.** The sections below are the file's
sections, in that order. Cite ads by `ref` and never re-describe one — `per-ad-teardowns.md` holds
the descriptions.

## Two populations, two kinds of evidence

The ledger holds every ad pulled. Only some of them were watched, and both groups are analysed.

- **Every ad in the ledger** carries metadata — run length, live or stopped, format, campaign,
  call-to-action, platforms, when it launched — **and the copy the platform ran around it**: the
  headline, the primary text, the link description, and the panel copy where a carousel spreads its
  argument across cards. These are the whole-set findings, and they run over all of it: the shape of
  the run-length distribution, the format mix, how big the campaigns are and how many, how often a
  competitor launches, what proportion has been dropped, and what the copy claims across the set.
- **The watched ads** carry a teardown as well. These are the findings about how ads are built, and
  they run over the ads actually read — each competitor's longest-running, live and stopped taken
  separately. That is a sample of the long end, so a claim about what a competitor is trying *now*
  comes from the ledger and the copy, not from the teardowns.

**Never quote one as a share of the other.** "Nine of the sixty ads open on a price comparison" is
false where only twelve were watched; it is nine of twelve. Every count says which population it came
from and how many that population holds.

The unwatched ads are not spare. They are what makes a run-length distribution or a format mix mean
anything, and a finding that could have used the whole ledger but was drawn from twelve teardowns is
a weaker finding than it needed to be.

## Finding the patterns

Don't work through the ads one at a time, end to end. Isolate one component across the whole set.

- **Component isolation.** Read every opening together, then every core argument, then every call to
  action — in the teardowns for the ads that were watched, and in the ledger's copy for all of them.
  The copy and the creative are two arguments, sometimes the same one and sometimes not; where they
  diverge, say so. What matters in video — pacing, retention, what carries with the sound off — is not what
  matters in a still — composition, hierarchy, how much of the frame is type. Keep the two analyses
  distinct, and where a pattern holds in only one of them, say which.
- **Bottom-up grouping.** Let the ads dictate the categories. Where several rely on the same trigger
  or the same visual move, name that group for what it *does*. Don't force ads into a standard
  marketing taxonomy they don't fit.
- **Define before counting.** Once a tactic repeats, write its definition down, tight enough that
  another reader would sort the same ads the same way. Count only after the group is defined.
- **The outliers matter.** An ad fitting no group is not a failure of the grouping — it is the raw
  material for the white space. An ad can also sit in more than one group; say which overlap rather
  than forcing a single home.

## The lines of inquiry

Four lenses, rather than a list to work through.

- **Performance proxies.** What do the longest-running ads share? Start on the whole ledger — how run
  length is distributed, which formats and campaigns hold longest, what proportion has been dropped —
  then cross-reference the groups you named from the teardowns against run length, to deduce what the
  market currently rewards. Then the same against the stopped ads, to find the tests that failed and
  the angles that are exhausted.
- **What is being varied.** Ads the platform groups as variants of one another differ deliberately —
  one line, one image, one offer. Read a variant group side by side and the difference is the test
  that competitor is running. Copy repeated verbatim across many ads is the opposite signal: settled,
  not under test.
- **Baselines against bets.** Separate table stakes — what every competitor does to be in the category
  at all — from bets, the structural, casting or messaging choices isolated to one competitor.
- **Creative mechanics.** How is attention won and held? What dominates the first three seconds, or the
  primary visual frame? How is proof established, how are offers framed, who gets cast and where are
  they shot, and what does the ending ask for?
- **The white space.** What is distinctly missing. Separate an **avoided space** — present among the
  stopped ads, absent from the live ones, so it was tried and dropped — from an **untried space**, a
  logical angle absent from the set entirely. Look for absence in the teardowns, not only in the
  counts: the thing nobody says, the shot nobody uses, the objection nobody answers.

## Weighing the evidence

Spend, reach and results are private, so run length is the only performance proxy — and it is named
as a proxy every time it is used.

**Read run length in bands, never precisely.** Under about two weeks is still being tested or already
failed, and carries no information alone. Two to six weeks is holding its place. Beyond about six
weeks and still running is almost certainly earning money.

**The counter-signal.** A single ad running for months with no variants around it is weaker evidence
than it looks — it may only mean nobody has made anything new. A long run *with* several near-matching
ads beside it in the same campaign is the strong case.

**A retired ad is evidence too.** Something that ran three weeks and was pulled is a test that failed.
But outside Europe most ads leave the library once they stop, so the stopped set is a sample and never
a full history — something missing from it is not evidence that it never failed.

**How much is enough:**

- **Five or more ads behind any pattern.** One ad doing something unusual is one ad.
- **At least 25 live ads for that competitor before quoting a share.** Below that, name the patterns
  and say which dominate; give no percentages.
- **More than one competitor** before calling anything a category norm.
- **Say what each count is out of**, and which population it came from — the whole ledger, or the ads
  actually read.

Where the evidence is thin, say so inside the finding, not in a footnote.

## Closing the analysis

**Answer what the user asked**, where they said what they wanted to learn — a few sentences, in the
terms they asked it, drawing on everything above. Where they didn't, say so. This is the last thing
written, and nothing above it is cut to serve it.

**What to make next is not decided here.** The analysis carries the patterns, the counts and the
space nobody runs; turning them into concepts is `planning-campaigns`' job, which reads this
alongside the brand, the product and the account's own ads.

## The evidence rules

- **Separate what was seen from what was worked out.** What an ad shows is observed. Why it works, who
  it targets and what it cost are inferred, and are written as inference.
- **Never present spend, reach, impressions or results as fact.** None of it is published for
  commercial ads.
- **Describe patterns, don't copy words.** Record what the ads do — how they open, what they argue,
  where the offer lands — not the sentences they use.
- **Every count traces to `ref`s**, and every named group to its written definition.
- **Confidence is stated separately from the claim**, and tied to what stands behind it — how many
  ads, how long they ran, how many competitors. Never a bare "strong signal".
- **A load-bearing claim carries its alternative explanation.** A pattern among long-running ads may
  mean it converts, or may mean nobody has made anything new. Say which readings the evidence allows
  and which it rules out.
- **Cite an ad, don't retell it.** Where a group needs an example, give its `ref` and one line. The
  full description stays in `per-ad-teardowns.md`.
- **A `ref` on its own resolves to nothing.** The first time each one appears in the file, give the
  path to the local copy of its creative and its ad-library link beside it, so a reader who has only
  this file can still view and open the ad.

## The reference index

**Close the file with a table of every `ref` it cited** — the `ref`, the advertiser, how long the ad
ran, its ad-library link, and the path to the local copy of its creative. Whoever reads this
analysis later, or plans from it, resolves any citation from this table alone.
