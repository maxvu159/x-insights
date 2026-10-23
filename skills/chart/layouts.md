# Layout: title, evidence, context

A good image has three tiers: the **title** is the conclusion, the **main panel** is the evidence, the **supporting
part** is context answering "compared with what", "why" or "where is the risk". The supporting part only explains
the main idea; it never opens a new one.

## Three combinations

| layout | when | approved example |
|---|---|---|
| `hero_top` / `hero_main_side`: big numbers + chart | the post has one shocking number, the chart explains why | staking yield: 56%, ~10%, 5.4% + segment bar + weekly payout columns |
| `main_side`: main chart + side panel | to separate the mix or show a risk next to a trend | weekly columns + the share of one venue still running a points program |
| `two_up`: two charts side by side | comparing two periods or two subjects; **must share axes and scale** | before and after an event |

Default is `single`. Add a panel only if covering it would make the title weaker.

## Panel rules

- **One panel with many layers first.** Bland charts usually come from snapshot totals (6 bars), not from a missing
  panel. If there is a series, draw it, then stack layers: dots on periods meeting a condition, shaded spans, number
  blocks inside the plot, circled points (`layers`), a same-unit line over the columns (`overlay`). Example: 30
  daily columns replacing 6 horizontal bars plus a side panel.
- **Two panels: the side panel must change the question** (compared with what, why, where is the risk). The same
  form is fine if the measure changes and labels say so ($ bars next to % bars). Same measure means same scale, and
  then it is `two_up`.
  Forbidden: panel 2 repeating panel 1's role (same measure, same subject, only a different period or token) on a
  different scale.
- **Three or more panels only as small multiples**: same form, same axes, same scale, one subject per panel, read as
  one idea with several cases. The dark style has no 3-panel layout; if needed, build a template, and only when the
  idea is "the same thing, in three places".
- **Dual axes: forbidden.** Two units on left and right y axes let you pick scales that fake "moving together".
  Instead rebase to 100 (`line_compare` `index_to`), move the other series into `layers.notes`, or use two panels
  sharing the x axis.

## Limits per style

| style | maximum panels | maximum big numbers | why |
|---|---|---|---|
| dark (X posts) | 2 | 3 | viewers scroll on phones, stop for 2 seconds, the image is shrunk |
| light (academic, reports) | 2 | 0 | paper convention, a table of numbers instead of big numbers |

Three or more charts in one image means the post has three ideas. Split into a thread, one image per post.

## Frame

- `16x9` by default. Time series need width.
- `4x5` for big-number images, horizontal bars, segment bars: on a phone it shows almost twice as large.
- Fixed frame, nothing tight to the edge. X rounds corners and crops edges, so text near the edge gets lost. Safe
  area: 6% horizontal, 8% vertical.

## Legend instead of end-of-line labels

The dark style uses a one-row legend under the subtitle. Direct labels are only for **highlight numbers** ("perps
53%", "$1.15B"), never to name a series. A single series needs no legend; the title already names it.
