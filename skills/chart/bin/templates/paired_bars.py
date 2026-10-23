"""
paired_bars: two horizontal bars per item (A = ours, B = comparison) side by side so the eye compares directly.

Use when: "A beats B on 4 of 5 items", the same measure for each pair (e.g. APR of venue A vs venue B for the same
asset, fees on chain A vs chain B for the same protocol).
Not for A and B on different measures, or for daily series (draw a line chart then).

panel:
  rows:    "compare[]"                       list of dicts
  fields:  {label: "label", a: "a_apr_7d", b: "b_apr_7d"}   missing b (None) -> missing_text instead of a bar
  opts:    a_label, b_label (legend), fmt (pct|pct1|usd|num|x), sort (desc|asc|none, by a),
           missing_text ("no comparable pool"), note_width (0.5: share of the x axis for the text block; 0 = no block)
  note:    [{text, value?, fmt?, role?, bold?}]   text block right of the plot, same line syntax as layers.notes
           ({v} = value; "" = empty line). Usually "A ahead on {v} of N" plus a caveat.
"""

import numpy as np

from chartkit import resolve
from layers import note_line

from ._common import fmt_of, left_margin


YTICKS = False


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    f = panel.get("fields", {})
    rows = [dict(r) for r in resolve(data, panel["rows"])]
    ka, kb, kl = f.get("a", "a"), f.get("b", "b"), f.get("label", "label")
    sort = o.get("sort", "desc")
    if sort != "none":
        rows.sort(key=lambda r: -(r.get(ka) or 0) if sort == "desc" else (r.get(ka) or 0))
    fmt = fmt_of(o, "pct")
    left_margin(ax, kit, [r[kl] for r in rows])
    n = len(rows)
    y = np.arange(n)[::-1] * 1.0
    h = 0.36
    vmax = max(max(r.get(ka) or 0, r.get(kb) or 0) for r in rows) or 1
    note = panel.get("note") or []
    note_w = o.get("note_width", 0.5 if note else 0)
    for yi, r in zip(y, rows):
        a, b = r.get(ka), r.get(kb)
        ax.barh(yi + h / 2, a, h * 0.92, color=kit.color("accent"), linewidth=0)
        ax.text(a + vmax * 0.012, yi + h / 2, fmt(a), va="center", ha="left", fontsize=kit.t["label"],
                fontfamily=kit.body, fontweight=600, color=kit.color("accent"))
        if b is not None:
            ax.barh(yi - h / 2, b, h * 0.92, color=kit.color("compare"), linewidth=0)
            ax.text(b + vmax * 0.012, yi - h / 2, fmt(b), va="center", ha="left", fontsize=kit.t["label"],
                    fontfamily=kit.body, color=kit.c["muted"])
        else:
            ax.text(0, yi - h / 2, o.get("missing_text", "no comparable pool"), va="center", ha="left",
                    fontsize=kit.t["label"] - 0.5, fontfamily=kit.body, color=kit.c["muted"])
    ax.set_yticks(y)
    ax.set_yticklabels([r[kl] for r in rows], fontsize=kit.t["label"] + 1, color=kit.c["text"])
    ax.set_xticks([])
    ax.grid(False)  # the text block sits on the plot, gridlines would cut through it
    ax.set_xlim(0, vmax * (1.18 + note_w * 1.34))
    ax.set_ylim(-0.75, n - 0.35)
    if note:
        x0 = vmax * (1.18 + note_w * 0.28)
        yy = n - 0.6
        for ln in note:
            if ln.get("text"):
                txt, col, wt = note_line(ln, data, kit, {}, None)
                ax.text(x0, yy, txt, ha="left", va="top", fontsize=kit.t["callout"], fontfamily=kit.body,
                        fontweight=wt, color=col)
            yy -= 0.42
    return {"legend": [(o.get("a_label", "A"), "accent"), (o.get("b_label", "B"), "compare")]}
