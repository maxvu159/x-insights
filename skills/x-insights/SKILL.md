---
name: x-insights
description: >-
  Turn what a crypto community on X is talking about into data insight posts:
  one chart plus a short post with numbers nobody else has. USE when the user
  says "/x-insights <profile>", "make an insight post", "what is the community
  talking about, find an angle", "turn this tweet into a data post", or asks
  for a chart + post on a community topic. Argument: profile name and
  optionally a topic or angle ("/x-insights mychain yields"). Never posts to
  X; output goes to the workspace for the user to approve.
---

# x-insights

Answers one question with one image and one short post: **"what is the community talking about, and what number do
I have that they don't?"**

Scripts live in this skill's base directory (shown when the skill loads): `bin/trends.py`, `bin/lib.py`. The
workspace is `$INSIGHTS_HOME` (default `./insights/`):

```
insights/
  scans/      trends output: <profile>-DATE.json, -tweets.json, author_views.json
  scripts/    one fetch script per angle
  data/       <slug>.json, the locked numbers of one post, with "asof"
  specs/      chart specs (chart skill)
  outputs/    <slug>/final/FINAL-<n>-hook_<desc>.png|svg (chart skill)
  posts/      DATE-<profile>-posts.md, the batch file you hand to the user
```

Profiles: `profiles/<name>.json` (accounts by tier, filter, queries, topics, data map, stance) and
`profiles/<name>.md` (data sources, data traps). Start from `_template.*`. Voice: `reference/voice.md`.
Hard-won rules with the incident behind each: `reference/rules.md`. Read both before writing.

## Flow

```
1 profile → 2 scan → 3 pick angle → 3b image brief + data probe → 4 lock numbers
  → 6 write post → 6b number review (new agent) → 6c batch read → 5 chart (chart skill) → 7 fact check → 8 hand over
```

Steps are numbered by topic, not by order: the chart (5) is drawn **after** the post is final, because editing
usually changes line 1 and a chart drawn earlier tells a different story.

### 1. Read the profile
`profiles/<name>.md` then `<name>.json`. No profile yet: copy `_template.*`, fill the tiers with the user, and stop
there for review.

### 2. See what the community is saying
Skip when the user already gave an angle.
```bash
TWITTER_CHROME_PROFILE="<chrome profile>" python3 <skill dir>/bin/trends.py --profile <name> --hours 48
```
- Output: posts by tier, ranked by lift (views / the author's usual), tickers named by several authors, emerging
  @handles, **quote chains**, regex topics.
- Regexes only group roughly. Read the 3 top posts of a topic to know what people actually say.
- Read the quote chains section: a root post quoted by several community posts is part of the conversation even
  when its own text never names the topic. `--expand-quotes 10` fetches views of the top roots.
- Run `twitter whoami` first if the user has several X accounts in Chrome.

### 3. Pick the angle
Match topics to data with the profile's `data_map`. A good angle has all three:
- It is about what is hot right now.
- It has a number the original poster does not have (a wallet balance, APR after price, holder yield vs mcap).
- It can answer or correct a claim that is spreading ("12x" was one day; over 30 days it is 6.6x).

Two or more angles: let the user choose unless told to do all.

**Propose dropping an angle** when the numbers bring nothing new; say why. When told to do all, drop it anyway and
list it in the report so the user can bring it back.

**When the numbers do not support the planned stance, follow the numbers.** Change the tone (supportive → neutral →
honest check) and say so in the report. If the result would be attacking someone inside the community, make it a
friendly reply or drop it. Never write a post just to fill a quota. Angles that came out flat in practice:
- Defending a project's self-reported number nobody is disputing.
- Grading the calls of insiders (founders, projects). Give them the number in a short friendly reply instead.
- Repeating a published angle (keep a list of published posts in `reference/voice.md`).

**Who does what.** Separate machine work from writing.
- An agent per angle (parallel is fine) does 3b and 4 and returns a **number card**: the idea in one sentence, 3 to 5
  locked numbers with source and method, the weak points of the numbers, the image brief adjusted to real data, the
  data file path. **Agents do not write the post**: an agent that has just loaded 30 numbers stuffs them all in.
- The main session writes posts from the number cards (step 6), **one at a time**, shows the user, edits on their
  reaction, then moves on. Feedback on post 1 applies to post 2.
- The chart (step 5) is drawn after the post is final. The chart skill calls its own reviewer agent; a forked agent
  cannot spawn agents, so do not hand step 5 to a fork.

### 3b. Image brief, written BEFORE pulling numbers
First a **5-minute data probe**: which series really exist (daily or weekly, how many periods, which numbers are
snapshot-only like a pool APR). The brief only asks for series you confirmed. Four lines in the batch file:
- **Image idea:** one sentence the viewer believes after 3 seconds (usually line 1 of the post).
- **Series to pull:** daily or weekly, how many periods, split by what. If a series exists, a one-off total is not acceptable.
- **Comparison:** what the other side is (main venue, a chain of the same age, spot).
- **Numbers inside the plot:** "days A beat B", "3 biggest jumps", "share on the main venue".
Pick the chart form in the chart skill's `catalog.md`. This brief is the input of steps 4 and 5.

### 4. Lock the numbers
- Pull exactly the series the brief asks for, store them as `rows` per period in the data file, plus totals.
  Storing only totals is how flat images happen.
- One fetch script per angle in `$INSIGHTS_HOME/scripts/<slug>.py`; reuse `bin/lib.py` (`http_json`, `rpc`,
  `get_logs`, `balance_of`, `erc20_meta`).
- Locked numbers go to `$INSIGHTS_HOME/data/<slug>.json` so every number in the post traces back.
- **One snapshot per post.** The data file has `asof` at the top; a rerun overwrites the file or adds a new block
  with its own `asof`. Never mix two snapshots in one post. Note which snapshot the post uses.

### 5. Draw the chart with the `chart` skill
- Input: the 3b brief (updated if line 1 changed), the data file, the style (`dark` for X by default). Called from
  here, the chart skill writes the spec without asking. If the brief needs a series the data lacks, go back to step 4;
  do not fall back to a bar of totals.
- Default to one panel with layers; a side panel only when the second question is really different.
- The chart skill renders, has an independent agent review against its checklist (max 2 rounds), and saves
  `outputs/<slug>/final/FINAL-<n>-hook_<desc>.png`. The current version is the highest `<n>`; the batch file must
  point at it.

### 6. Write the post
Main session, from the number card, one post at a time. Voice and length come from `reference/voice.md`.
- **3-line post brief first:** who reads it and what they want to know; the idea in one sentence; at most 3 numbers.
  Cannot write line 1? Propose dropping the angle.
- **At most 4 lines**, short sentences, conversational. **At most 2 of those lines are caveats or risks**, and a
  caveat goes in only if it changes the reader's decision. Everything else goes to "Notes before posting" for the
  user. Readers and reviewers need different things; a post serving both is hard to read.
- **One post, one idea.** Drop every line that does not serve it, even a nice number.
- **Line 1 is the most surprising number**, not the background number.
- Order: surprising number, why, weak point or risk, take. About 5 numbers total at most.
- **Do not narrate the work** ("I pulled X myself", "I rebuilt every transfer"). Readers want the result.
- No math homework for the reader. If the reasoning needs three steps, the angle is not tight enough.
- Only claim what the number proves. Volume is not liquidity; fresh wallets are not a bundle without a shared funder.
  Give the benign explanation when there is one.
- Familiar measures: "pays holders 32% of mcap a year" beats "3.1x value to payout".
- The biggest risk must be in the post, not only in the notes.
- Name the weak point of your own numbers in the post. Being called out after posting is much worse.
- Slang (tbh, imo, ngl, fwiw...) is seasoning: at most one per post, many posts need none, never the same one in two
  posts of a batch.
- No em dashes, no emoji, no hashtags unless the voice file says otherwise. Tickers with `$`.

### 6b. Number review by a new agent
Give a fresh agent only: the post, the post brief, the data file (say which snapshot), and the rules of step 6. It
returns: is there exactly one idea, which numbers do not match the data, which comparisons are not same period or
same method, which lines are extra.
**Handle each finding one of three ways, never by default adding a warning line:** make the comparison right (same
method, or say only "ahead on 4 of 5" and keep the details in the notes), drop the claim, or keep one caveat if it
changes the reader's decision.
When the user is editing post by post, the user is the editor and 6b only checks numbers.

### 6c. Read the whole batch (main session, 2+ posts)
- Count slang across the batch; at most one per post, no repeats.
- Find numbers that disagree between posts because of different methods. Pick one method or drop the number.
- Find two posts with the same idea or ticker; merge or drop one.
Then draw the charts (step 5), then step 7.

### 7. Fact check before showing the user
- Every number in the post is in the data file or script output.
- No dates or claims you did not check ("last month" when you do not know the day; someone else's number you did not verify).
- Comparisons are same period, same method.
- **Numbers are what the reader sees when they open the app.** An unlisted market, a project's private pool or a
  one-user vault is not "the borrow rate" or "the APR" of a protocol. A stablecoin rate far above the usual 5 to 7% is
  a sign to check who is borrowing.
- Compare against peers of the same kind, then check the counter-example in your own table (if a dead peer also
  looked like this at the same age, you cannot call it a good sign).
- Time-sensitive numbers (holders, price, votes) are re-run right before handing over, with the time noted.

### 8. Save and hand over
- Write `$INSIGHTS_HOME/posts/DATE-<profile>-posts.md`; per angle: the idea in one sentence, the community angle (who
  said what), the image path, the post, a "Numbers:" section (source, method, snapshot), notes before posting.
  Dropped angles get a section with the reason. A changed stance is stated.
- Open the final images for the user.
- **Never post to X.** If the user asks to post: `twitter whoami`, confirm the account, show the exact text, measure
  its length with `len()` (over 280 characters needs a long-post capable client), and post only on an explicit yes.
- After posting, add the post to the published list in `reference/voice.md` so later angles do not repeat it.

## New profile

Copy `profiles/_template.json` and `_template.md`, then with the user: fill the three tiers (score candidates by
views per post, share of on-topic posts, how often others quote them), write the filter with the community's
nicknames, add queries, map topics to data in `data_map`, write the stance rules. Run step 2 once and read the output
together: missing accounts and missing nicknames show up in the quote chains and emerging names.
