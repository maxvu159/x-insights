"""
hero: small labelled columns, used as a side panel next to a big number, e.g. weekly distributions.
The big number itself lives in spec["hero"] (kit.hero), not here.

panel:
  items: [{label, value, role?}]  or rows + fields
  opts: fmt (usd), highlight_last (true: last column accent, the rest compare), title (small text above the panel)
"""

import numpy as np

from ._common import fmt_of, items_of


YTICKS = False   # no numeric y tick labels, render gives ytick_pad back to the template


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    items = items_of(panel, data)
    f = fmt_of(o, "usd")
    n = len(items)
    x = np.arange(n)
    vals = [float(d["value"] or 0) for d in items]
    for i, d in enumerate(items):
        role = d.get("role") or ("accent" if (o.get("highlight_last", True) and i == n - 1) else "compare")
        ax.bar(i, vals[i], 0.62, color=kit.color(role), linewidth=0)
        ax.text(i, vals[i] + max(vals) * 0.03, f(vals[i]), ha="center", va="bottom", fontsize=kit.t["label"],
                fontfamily=kit.body, fontweight=600, color=kit.c["text"])
    ax.set_xticks(x)
    ax.set_xticklabels([d["label"] for d in items], fontsize=kit.t["tick"], color=kit.c["muted"])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_ylim(0, max(vals) * 1.3)
    return {"legend": []}
