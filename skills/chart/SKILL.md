---
name: chart
description: >-
  Turn one idea plus a data file into a styled chart (PNG + SVG) by writing a
  small JSON spec, rendering it with shared code, and having a separate agent
  review it before delivery. USE when the user asks for a chart for a post,
  thread, deck or research note ("/chart", "make a chart for this", "chart
  this number"), or when the x-insights skill reaches its chart step.
  Argument: style name (dark or light), then the idea sentence and the data
  file, optionally a template name. Never posts anything; output goes to the
  workspace outputs/ folder.
---

# chart

One idea, one data file, one style, one image. The agent **does not write matplotlib**; it writes a `spec.json`.
`bin/render.py` reads the spec plus the style and draws. An image is delivered only after **another agent reviews it**.

When this skill loads, Claude is told its base directory. Below, `<skill dir>` means that directory, so the renderer
is `<skill dir>/bin/render.py`.

Workspace: `$INSIGHTS_HOME` (default `./insights/`) holds `data/<slug>.json`, `specs/<slug>.json` and
`outputs/<slug>/final/`. Styles: `<skill dir>/styles/dark.json` (X posts) and `light.json` (academic, reports).
The handle printed on the image comes from the style's `handle` field or the env var `INSIGHTS_HANDLE`.
Chart chooser: `catalog.md`.

Fonts: Inter is recommended (free, OFL). Without it the renderer falls back to DejaVu Sans and prints a warning.

## Usage

```
/chart dark "Staked tokens that vote earn 56% a year because 400M of the 450M staked never vote" data/stake_yield.json
/chart dark segment_bar data/stake_yield.json "..."      # form already known, skip the suggestions
/chart light "..." data/x.json                           # other style
```
x-insights calls this at its chart step with the dark style and the edited post; step 2 then runs automatically and
takes option 1.

## Workflow

1. **Input.** Three things are required: the main idea in one sentence (line 1 of the post), a data file with
   `asof`, and a style. If the idea is missing, ask "what should the viewer believe after seeing this image?" and
   **do not draw**. Drawing before there is an idea is where bland charts come from.
   When called from x-insights, the input is the **4-line image brief** (idea, series, comparison point, numbers
   inside the plot area) written in that skill's step 3b, not just line 1. **If the brief asks for a series but the
   data file only has a one-time snapshot total, stop and report "series missing, the image would be a single
   snapshot"**; do not quietly draw horizontal bars. Fetch the series first, then draw.

2. **Image brief.** Write three lines: title (a conclusion with a number), evidence (main panel), context (side panel
   or big number, answering "compared with what" or "where is the risk"). Look up `catalog.md` by the kind of
   question the idea asks, and `layouts.md` for layout and frame. If the user has not picked a form, offer 2
   options, one line each (form, template, proposed title, side panel); the user picks, then write the spec. If the
   idea matches no catalog row, say plainly there is no template yet and propose `custom` or dropping it.
   **One panel with several layers first, two panels second.** If there is a daily or weekly series, draw it, then
   add layers with `layers` (period marks, shaded spans, number blocks inside the plot, circled points) and
   `overlay` (a same-unit line over columns). Add a side panel only when the second question really is different.

3. **Write the spec** per `spec.md` into `$INSIGHTS_HOME/specs/<slug>.json`. Numbers in the title and subtitle must
   come from the data of the same snapshot. The spec names color roles, never hex codes. `final.n` increases on
   each redraw.

4. **Render a preview.**
   ```bash
   python3 <skill dir>/bin/render.py $INSIGHTS_HOME/specs/<slug>.json --preview /tmp/<slug>.png
   ```
   Use `--preview` until review passes, so `outputs/<slug>/final/` only holds approved images. Open the PNG once
   with Read to catch obvious errors. A "template not found" or "layout needs N panels" error is a spec error.
   Code errors (text overflowing although the spec is right, labels overlapping on every spec) can be fixed in
   `bin/` if small, and noted in the final report; do not edit `styles/` (that is the user's decision). For large
   code errors, stop and tell the user.

5. **Review with a fresh agent** (Agent tool, general-purpose, no inherited context). The brief contains only: the
   PNG path, the spec, the data file, `checklist.md`, and a request to return PASS or a list of issues by item with
   the fix in the spec. If it fails: fix the spec, render again, review again. **At most 2 rounds.** If round 3
   still fails, give the user the best image with the remaining issues; never silently deliver a failing image.

6. **Deliver.** Only after review passes, render without `--preview` to write
   `outputs/<slug>/final/FINAL-<n>-hook_<desc>.png` (and .svg). `n` increases when redrawing an image delivered
   before; the old one stays. Report the path and add it to the post or summary file. Never post to X. Keep the
   spec so the image can be redrawn when the numbers change.

## Spec rules (summary; details in spec.md and layouts.md)

- The title is the conclusion, has a number, and matches the numbers on the image. Subtitle at most 2 lines. The
  source line states sources and assumptions.
- Legend instead of end-of-line labels. Direct labels only for highlight numbers.
- At most 2 panels + 1 row of big numbers (dark style). Supporting parts never open a new idea.
- Coral only for negative or risk, once per image. At most 4 data colors: `accent`, `compare`, `compare2`, `compare3`.
  `compare3` only in stacked columns with a legend and never next to `compare` (validator result, recorded in
  `styles/dark.json`).
- Shared layers for every template with a series: `layers.marks` (dots on periods meeting a condition, counts n/N),
  `layers.spans` (shaded range), `layers.notes` (text blocks with numbers inside the plot, raise the y ceiling and
  drop clashing ticks automatically), `layers.points` (circle a point, or `top_gains` finds the k biggest gains).
  `stacked_columns` has `overlay` for a same-unit line. Syntax: `bin/layers.py` and `spec.md`. Layered
  examples: `examples/specs/stacked_layers.json` and `examples/specs/days_since_launch_labels.json` (images in
  `examples/img/`).
- Gapless daily stacked columns instead of area. 100% only when the total is not the story.
- Fixed frame 16:9 or 4:5, nothing tight to the edge, safe area 6% horizontal and 8% vertical. Title and source are
  placed by the renderer inside the safe area; 4:5 drops the note column of `ranked_bars` for lack of room.
- Numbers on the image should come from the data via a path or `{"expr": "a / b"}`; avoid hardcoding. Numbers in
  the title must be rounded the same way as on the bars (`pct` 0 decimals, `pct1` 1 decimal).

## When templates are not enough

Try `layers` and `overlay` first: layered images that once needed their own module came out identical as plain
template specs once `layers` existed. Paired bars went the same way: a one-off module that became the
`paired_bars` template. If still not enough, write a module `$INSIGHTS_HOME/custom/<name>.py` with
`draw(ax, panel, data, kit, ctx)`, using `kit.color(role)`, `kit.callout`, `kit.t` (font sizes), with no hardcoded
colors or fonts. The spec sets `"custom": "custom/<name>.py"` and a one-line `"why"` explaining why no template
fits. It still goes through render, review and delivery. If the same form comes up a second time, turn it into a
template.

## Adding a style

Copy `styles/dark.json`, change `name`, `handle`, `colors`, `fonts`, `max_panels`. Keep the color role names.
Run a contrast and color-distance validator (for example the dataviz skill's) on the new palette and record the
result in `validated`. Render `examples/specs/stacked_weekly.json --style <name>` to check it.

## General image rules

No 3D, no dual axes, no pie with more than 4 parts.
