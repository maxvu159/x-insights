# Examples

One runnable spec per template, all on synthetic data. Names such as "Chain A", "Token X" or
"Venue A" are placeholders and the numbers describe no real market.

| spec | template | what it shows |
|---|---|---|
| `line_compare_indexed` | line_compare | three series indexed to 100 at an event, end values |
| `step_event_hourly` | step_event | hourly step series with an event marker |
| `stacked_daily` | stacked_columns | daily stack with `from` filter and share callouts |
| `stacked_weekly` | stacked_columns | weekly aggregation with segment labels |
| `stacked_layers` | stacked_columns | `overlay` plus `layers`: marks, spans, notes |
| `ranked_multiple` | ranked_bars | rows + fields, ascending sort, highlights, missing values |
| `diverging` | diverging | positive / negative parts per item, net labels |
| `ranked_holders` | ranked_bars | hand-written items with a note column |
| `ranked_holders_4x5` | ranked_bars | same chart in the 4x5 frame (note column dropped) |
| `days_since_launch` | days_since_launch | series by age, `snapshot` asof, end values |
| `days_since_launch_labels` | days_since_launch | `end_labels`, `short`, `layers.points` top gains |
| `hero_segment` | segment_bar + hero | `hero_main_side` layout with big numbers |
| `paired_bars` | paired_bars | A vs B per item, missing B, side text block |

Run from the skill root so the `examples/data/...` paths in the specs resolve:

```bash
python3 examples/make_data.py                      # regenerate examples/data/*.json (seeded, deterministic)
INSIGHTS_HOME=examples/out python3 bin/render.py examples/specs/paired_bars.json
python3 bin/render.py examples/specs/paired_bars.json --preview /tmp/paired_bars.png   # no outputs/ folder
```

Rendered PNGs (3600x2025 for 16x9, 2160x2700 for 4x5) are in `examples/img/`.
