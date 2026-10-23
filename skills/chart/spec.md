# spec.json: describing one image

The agent writes the spec, `bin/render.py` draws it. A spec never contains hex codes, only color **roles**.
Save it as `$INSIGHTS_HOME/specs/<slug>.json`. Runnable examples: `<skill dir>/examples/specs/`.

## Top level

```json
{
  "slug": "stake_yield",                // folder outputs/<slug>/final/
  "style": "dark",                      // styles/<name>.json: dark | light
  "frame": "16x9",                      // 16x9 (default) | 4x5 (big numbers, horizontal bars, for phones)
  "layout": "single",                   // single | hero_top | main_side | two_up | hero_main_side
  "title": "Staked tokens that vote earn about 56% a year",   // a conclusion, with a number
  "subtitle": "400M of the 450M staked tokens never vote ...", // context, 1 to 2 lines
  "source": "On-chain staking contract, project docs, CoinGecko", // sources, assumptions; asof date is appended
  "asof_in_source": true,               // false if the date is already in source
  "handle": true,                       // print the style's handle top right
  "legend": true,                       // one-row legend under the subtitle (hidden when < 2 entries). false: plot area moves up 0.05
  "data": {"file": "data/stake_yield.json", "snapshot": "v3"},   // snapshot: a sub-block with its own asof
  "hero": [ {"value": "56%", "label": "now, on the 43.3M staked that votes", "role": "accent"} ],
  "panels": [ { ...panel... } ],
  "final": {"n": 2, "desc": "segment-hero"}   // FINAL-<n>-hook_<desc>.png, increase n on redraw
}
```

The handle text comes from the style's `handle` field or the env var `INSIGHTS_HANDLE`.

## Layouts and panel counts

| layout | panels | use when |
|---|---|---|
| `single` | 1 | one chart, default |
| `hero_top` | 1 | row of big numbers (`hero`) on top, chart below |
| `main_side` | 2 | main chart 60% + side panel 30% on the right |
| `two_up` | 2 | two charts side by side, same axes |
| `hero_main_side` | 2 | big-number row + main chart + side panel |

The style caps panels with `max_panels` (dark: 2). `hero` is the big-number row, not a panel, at most 3 numbers.

## Panel

```json
{
  "template": "stacked_columns",       // name in bin/templates/
  "title": "Weekly payout to stakers", // small text above the panel, optional
  "legend": true,                      // false: this panel's entries stay out of the shared legend
  "x": "rows[].d",                     // data path
  "series": [{"key": "rows[].spot", "label": "Spot DEX", "role": "compare"}],
  "opts": {...},                        // template specific, see the docstring at the top of each template
  "callouts": [...],                    // only for highlight numbers, never to name a series
  "custom": "custom/x.py"              // exception: module with draw(ax, panel, data, kit, ctx)
}
```

**Data paths**: `a.b` reads a key; `rows[].spot` maps over a list; `series[].1` takes element 1 of each pair.
Values in `items` also accept an expression `{"expr": "early_hold_now / supply"}` (names are top-level data keys
and must be numbers), so ratios trace back to the data instead of being hardcoded.
List templates (`ranked_bars`, `diverging`, `segment_bar`, `hero`) take hand-written `items` (values may be numbers
or paths) or `rows` + a `fields` mapping.

**Color roles**: `accent` (ours, main series), `compare` (the comparison side, background), `compare2` (second
layer), `compare3` (third layer, when 4 data layers are needed; validator result: next to `compare2` passes, next to
`compare` fails (dE 9.0), contrast 2.8:1, so use it only in stacked columns with a legend and put `compare2` between
it and `compare`), `negative` (negative, risk, at most once per image), `muted` (unimportant parts; it is the
secondary text color, avoid it for data), `warn` (self-reported number, rare).

**Units**: formatters (`usd`, `usd_b`, `usd2`...) take **raw dollars** (4,471,960,651), not numbers already divided
by a billion. Templates and custom modules plot raw values so axes and labels format themselves.

## Shared layers: `layers`

Available on panels of `stacked_columns`, `line_compare`, `days_since_launch` (templates that return `x`, `xkeys`,
`top`, `series`). Full syntax at the top of `bin/layers.py`.

```json
"overlay": {"key": "rows[].spot", "label": "spot DEX", "role": "compare"},      // stacked_columns: same-unit line over the columns
"layers": {
  "marks":  {"when": {"expr": "a > b", "vars": {"a": "rows[].stocks", "b": "rows[].majors"}}, "role": "accent"},
  "spans":  [{"last": 7, "label": "last 7 days"}],
  "notes":  [{"pos": "tl", "lines": [{"text": "Majors: {v} of volume", "value": "share_30d.majors", "fmt": "pct", "role": "compare2", "bold": true}]},
             {"pos": "tr", "x": "span", "lines": [{"text": "beat on {n} of {N} days", "role": "accent", "dot": true}]}],
  "points": [{"top_gains": {"series": "accent", "k": 3, "fmt": "usd_m", "text": "+{g}", "suffix": " (day {k})"}}]
}
```
- `marks`: a dot on top of each period where `expr` holds (variables are data paths, numpy arrays) or `at: [key]`;
  counts `{n}`/`{N}` for `notes`.
- `spans`: shaded range by `last: k` or `from`/`to` (ISO date keys or day numbers). `last` counts axis periods:
  with weekly columns `last: 1` is the last week.
- `notes`: text block in corner `tl`/`tr`/`bl`/`br` of the plot area. Each line has `{v}` (a path or
  `{"expr", "vars"}`, optional `fmt`), `role`, `bold`, `dot`. With notes, the y ceiling rises with the line count of
  the top block (2 lines 28%, 3 lines 42%) so text never touches the column tops or the 100% line; ticks that fall
  in the text rows are dropped. `"x": "span"` places the block at the left edge of the shaded span.
  `"notes_raise": false` (inside `layers`) keeps the ceiling: use it when the series declines and the block sits in a
  low corner, otherwise raising leaves an empty strip above the tall columns.
- `stacked_columns` with `period` (week, month) still accepts `layers`: daily array variables in `marks`/`notes` are
  summed per period, `overlay` is summed per period too; `from`/`to`/`at` use the period's first-day key.
- `points`: circle one period (`at` + `text`) or `top_gains` to find the k biggest gains of a series; labels of
  close periods (≤ 5 apart) merge into one.
- `days_since_launch` adds `end_labels` (end labels with names) and `short` (short names).

## Templates and main opts

| template | the idea | opts worth knowing |
|---|---|---|
| `stacked_columns` | composition over time, with a total | `gap` (0 = daily style, replaces area), `period` (week/month, groups 7 days from the first day), `pct` (100%), `labels` (segments when period), `from`/`to`; `overlay` same-unit line; `layers` |
| `line_compare` | trend of 2 to 4 series | `index_to` (rebase to 100), `end_values`, `events` |
| `days_since_launch` | at the same age, who is ahead | `pair`, `max_day`, `end_values`, `end_labels`, `short`; `layers` |
| `ranked_bars` | A is how many times B, who holds how much | `fmt` (`pct` 0 decimals, `pct1` 1 decimal, `x` 1 decimal), `sort`, `highlight`, `note` per item (dropped at 4:5), `missing_text` |
| `paired_bars` | two bars per item on the same measure, "A beats B on 4 of 5 items" | `rows` + `fields {label, a, b}`, `a_label`/`b_label` (legend), `fmt`, `sort` by a, `missing_text` when b is missing; `note` = text block on the right, line syntax as in `layers.notes` (`{v}`, `value`, `fmt`, `role`, `bold`) |
| a single column series (weekly payout, daily volume) | no dedicated template | `stacked_columns` with one `series`; `hero` as a small side panel |
| `diverging` | gains and losses around 0 | `pos`/`neg` per item, `pos_label`/`neg_label` for the legend |
| `segment_bar` | one total split by who holds how much | `caption` per segment, `min_label` |
| `hero` | small columns as a side panel next to big numbers | `highlight_last` |
| `step_event` | a token's move after an event, hourly | `events`, `hours` |

Full examples: `<skill dir>/examples/specs/` (line_compare_indexed, step_event_hourly, stacked_daily, stacked_weekly,
ranked_multiple, diverging, ranked_holders, ranked_holders_4x5, days_since_launch, days_since_launch_labels, stacked_layers, hero_segment, paired_bars), with
matching images in `<skill dir>/examples/img/`.

## Running

```bash
python3 <skill dir>/bin/render.py $INSIGHTS_HOME/specs/<slug>.json
python3 <skill dir>/bin/render.py spec.json --style light          # switch style
python3 <skill dir>/bin/render.py spec.json --preview /tmp/x.png   # preview, does not write outputs/
```
The last line printed is the PNG path. The SVG sits next to it, with text converted to outlines.
The title is anchored from the top of the safe area down, the source from the bottom up; a multi-line title or
subtitle pushes the legend and plot area down. A title longer than 2 lines leaves too little plot area: shorten it.
