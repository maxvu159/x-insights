# Catalog: what the idea says, which chart to use

Use this table in step 2 (image brief). Choose by **the question the idea asks**, not by the data you happen to have.
Example specs are in `examples/specs/`, rendered images (dark style) in `examples/img/`.

## Rule before using the table

**If there is a daily or weekly series, do not draw a one-time snapshot.** "A is N times B" is almost always line 1
of a post, but if A and B have daily numbers, draw the series (stacked columns, lines) and put the total in the
title or in `layers.notes`. Ranked horizontal bars only when the data really is a single snapshot (holders,
wallets, multiples). If the brief asks for a series the data does not have yet, fetch it first; do not fall back to
horizontal bars.

## Quick chooser

| What the idea says | Form | template | suggested layout | example |
|---|---|---|---|---|
| A beats B day by day, with the inner mix | daily stacked columns + dots on days A > B + number block | `stacked_columns` + `layers.marks`, `notes` | single | `stacked_daily` |
| Two volume types in the same unit, which periods exceed | stacked columns + overlay line + shaded last 7 days | `stacked_columns` `overlay` + `layers.spans`, `marks` | single | |
| Steady growth or a few jumps | line + circles on the k biggest daily gains + number block | `days_since_launch` + `layers.points.top_gains`, `notes` | single | `days_since_launch` |
| Total holds steady, the mix shifts | stacked columns by period | `stacked_columns` period week/month | single, or main_side with a risk panel | `stacked_weekly` |
| Mix shifts gradually day by day (instead of area) | gapless daily stacked columns | `stacked_columns` gap 0 | single | `stacked_daily` |
| At the same age, who is ahead | lines by days since launch | `days_since_launch` | single | `days_since_launch` |
| One goes up, the other down, from the same start | lines rebased to 100 | `line_compare` index_to | single | `line_compare_indexed` |
| Trend of 2 to 3 series in real values | lines | `line_compare` | single | |
| A is N times B; who holds how much; top N (only without a series) | ranked horizontal bars | `ranked_bars` | single, 4x5 if ≤ 5 items | `ranked_multiple`, `ranked_holders` |
| Which items in a group have no number | horizontal bars + text in place of a bar | `ranked_bars` + `missing_text` | single | `ranked_multiple` |
| A beats B on how many of N items, same measure (APR on venue A vs venue B for the same assets) | paired horizontal bars per item + number block on the right | `paired_bars` + `note` | single | `paired_bars` |
| A single column series (weekly payout, daily volume) | single columns | `stacked_columns` with one series (no dedicated template) | single | `hero_segment` (right panel) |
| Only the shares matter, not the total | 100% stacked columns | `stacked_columns` pct true | single, total in the subtitle | |
| One shocking number, and why it is high | big numbers + segment bar | `segment_bar` + hero | hero_top / hero_main_side | `hero_segment` |
| One total split by who holds how much | 100% horizontal segment bar | `segment_bar` | single | `hero_segment` |
| Gains and losses around 0, what is the net | diverging bars | `diverging` | single | `diverging` |
| A token's move after an event | hourly step line + event marks | `step_event` | single | `step_event_hourly` |
| Payouts per period, rising or falling (side panel) | small columns with numbers | `hero` | side of main_side | `hero_segment` |
| Group X had A, now has B (before and after of the same group) | two bars for the same group, labels state each time | `ranked_bars` with 2 items (sort none) or `hero` with 2 columns | single | |
| Horizontal bars for phones (≤ 5 items, no notes needed) | horizontal bars, portrait frame | `ranked_bars`, frame 4x5 | single | `ranked_holders_4x5` |
| How much wallets keep as price falls | % of supply area + price panel | no template yet, use `custom` | | |
| A table with many columns | not a chart | write a table in the post or use `ranked_bars` + note | | |

## Composition over time: 4 modes

| The idea | Meaningful periods, under 40 | Long series, telling a trend |
|---|---|---|
| Needs both total and shares | `stacked_columns` period | `stacked_columns` gap 0 |
| Only shares | `stacked_columns` period, pct | `stacked_columns` gap 0, pct |

Gapless daily stacked columns **replace area charts**. There is no area template.
Mixing historical numbers (bought at launch) with current numbers (pool, burned) on one axis is fine only when each
bar's label states its time; otherwise split into two bars "then / now".
100% only when the total is not the story; if the total matters too, put it in the subtitle or add a panel.

## Forms not to use

- Cumulative area: it always goes up and hides drops.
- Ranked columns when the post says "the ranking means nothing".
- Donut with more than 4 parts, dual axes, 3D, pie.
- Candles: only when the story is intraday volatility. For price with event marks, `step_event` is clearer.
- Maps: almost never in DeFi, except for user distribution.

## Lessons from replaced images: one panel, many layers

| Old image | Why it was bland | Replacement |
|---|---|---|
| 6 horizontal bars + % side panel | data was only a 30-day total, half the frame was background | 30 daily columns in 4 groups, dots on days one group won, number block 25% / 69% |
| Line by days since launch + 8-bar side panel | the side panel made up for an empty plot area | line + circles on the 3 biggest daily gains + number block 92/111, 13% |
| Two lines for two volume types | the title just read numbers out | stacked columns for two venues, spot line on top, last-7-days span, dots 11/30 |

## Lessons from replaced images: failures

| Old image | Why it failed | Replacement |
|---|---|---|
| Cumulative total vs a target line | two thirds of the frame empty, cumulative hid a 95% drop | angle dropped |
| Ranked columns by TVL at day 112 | the image said the opposite of the post ("the ranking means nothing") | daily line, compared with a peer chain |
| Two noisy lines | the title read numbers instead of telling a story | weekly columns, total steady, mix shifting |
| 5-color bar + text block | too many parts, the risk was not on the image | big numbers 56% / ~10% / 5.4% + segment bar |
| Stacked bar + 3 lines of text | 4 ideas in one image | ranked bars, new wallets compared with the pool |
