"""
ranked_bars: ranked horizontal bars, value at the bar end, optional note column on the right.

Use when: "A is N times B", top N, who holds how much. Items without a number get a text note instead of a bar.

panel:
  items: [{label, value, role?, note?}]  or  rows + fields {label, value, note, role}
  opts: fmt (num|usd|pct|x), sort (desc|asc|none), highlight: [label...] -> accent, default_role (compare),
        note_width (0.26: share of the width for the note column), missing_text ("no data"),
        slots (minimum rows: a 2-bar side panel uses 6 so bars are not too thick)
"""

import numpy as np

from ._common import fmt_of, items_of, left_margin


YTICKS = False   # no numeric y tick labels, render gives ytick_pad back to the template


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    items = items_of(panel, data)
    if o.get("sort", "desc") != "none":
        items.sort(key=lambda d: (d.get("value") is None, -(d.get("value") or 0) if o.get("sort", "desc") == "desc" else (d.get("value") or 0)))
    f = fmt_of(o)
    hi = set(o.get("highlight", []))
    left_margin(ax, kit, [d['label'] for d in items])
    n = len(items)
    y = np.arange(n)[::-1]
    vals = [d.get("value") or 0 for d in items]
    vmax = max(vals) if vals else 1
    narrow = ax.figure.get_size_inches()[0] < 9          # 4x5 frame: no room for the note column
    if narrow:
        for d in items:
            d.pop("note", None)
    note_w = o.get("note_width", 0.26 if any("note" in d for d in items) else 0)
    ax.set_xlim(0, vmax * (1.18 + note_w * 1.6))
    for yi, d in zip(y, items):
        role = d.get("role") or ("accent" if d["label"] in hi else o.get("default_role", "compare"))
        if d.get("value") is None:
            ax.text(0, yi, o.get("missing_text", "no data"), color=kit.color("negative"), fontsize=kit.t["label"],
                    fontfamily=kit.body, va="center", ha="left")
        else:
            ax.barh(yi, d["value"], height=0.62, color=kit.color(role), linewidth=0)
            ax.text(d["value"] + vmax * 0.015, yi, f(d["value"]), color=kit.color(role) if role != "compare" else kit.c["text"],
                    fontsize=kit.t["label"], fontfamily=kit.body, fontweight=600, va="center", ha="left")
        if d.get("note"):
            ax.text(ax.get_xlim()[1], yi, str(d["note"]), color=kit.c["muted"], fontsize=kit.t["label"] - 0.5,
                    fontfamily=kit.body, va="center", ha="right")
    ax.set_yticks(y)
    ax.set_yticklabels([d["label"] for d in items], fontsize=kit.t["label"] + 1, color=kit.c["text"])
    for lab, d in zip(ax.get_yticklabels(), items):
        if d["label"] in hi:
            lab.set_fontweight(600)
    ax.set_xticks([])
    ax.grid(False)
    # slots: with few items (2 bars in a side panel) keep bar thickness like the main panel, centered vertically
    slots = max(n, int(o.get("slots", n)))
    pad = (slots - n) / 2
    ax.set_ylim(-0.6 - pad, n - 0.4 + pad)
    return {"legend": []}
