"""Template registry. Each template is a module with draw(ax, panel, data, kit, ctx) -> dict
with 'legend': [(label, role)] and optional 'note'. ctx is a shared dict (fig, spec)."""

import importlib

NAMES = ["stacked_columns", "line_compare", "days_since_launch", "ranked_bars", "paired_bars",
         "diverging", "segment_bar", "hero", "step_event"]


def get(name):
    if name not in NAMES:
        raise KeyError(f"unknown template: {name}. Available: {NAMES}")
    return importlib.import_module(f"templates.{name}")
