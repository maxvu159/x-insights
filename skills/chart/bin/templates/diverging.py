"""
diverging: horizontal bars diverging around 0. Positive = accent, negative = negative. Each item may have 2 parts
(pos and neg) to show the net, e.g. LP fees (+) and price change (-) on $10K.

panel:
  items: [{label, pos, neg, note?}]  or rows + fields {label, pos, neg}
  opts: fmt (usd|pct|num), sort (net desc), net_label (true), pos_label, neg_label (legend names)
"""

import numpy as np

from ._common import fmt_of, items_of, left_margin


YTICKS = False   # no numeric y tick labels, render gives ytick_pad back to the template


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    items = items_of(panel, data)
    for d in items:
        d["pos"] = float(d.get("pos") or (d.get("value") if (d.get("value") or 0) > 0 else 0) or 0)
        d["neg"] = float(d.get("neg") or (d.get("value") if (d.get("value") or 0) < 0 else 0) or 0)
        d["net"] = d["pos"] + d["neg"]
    if o.get("sort", "net") == "net":
        items.sort(key=lambda d: -d["net"])
    f = fmt_of(o, "usd")
    left_margin(ax, kit, [d['label'] for d in items])
    n = len(items)
    y = np.arange(n)[::-1]
    lim = max(max(abs(d["pos"]), abs(d["neg"])) for d in items) * 1.25
    for yi, d in zip(y, items):
        ax.barh(yi, d["pos"], height=0.62, color=kit.color("accent"), linewidth=0)
        ax.barh(yi, d["neg"], height=0.62, color=kit.color("negative"), linewidth=0)
        if o.get("net_label", True):
            x = max(d["pos"], 0) + lim * 0.015
            ax.text(x, yi, f"net {f(d['net'])}", color=kit.c["text"], fontsize=kit.t["label"], fontfamily=kit.body,
                    fontweight=600, va="center", ha="left")
    ax.axvline(0, color=kit.c["muted"], lw=0.8)
    ax.set_xlim(-lim, lim)
    ax.set_yticks(y)
    ax.set_yticklabels([d["label"] for d in items], fontsize=kit.t["label"] + 1, color=kit.c["text"])
    kit.xfmt(ax, o.get("fmt", "usd"))
    ax.grid(axis="x", color=kit.c["grid"], lw=0.6)
    ax.grid(axis="y", visible=False)
    ax.set_ylim(-0.6, n - 0.4)
    leg = []
    if o.get("pos_label"):
        leg.append((o["pos_label"], "accent"))
    if o.get("neg_label"):
        leg.append((o["neg_label"], "negative"))
    return {"legend": leg}
