"""
days_since_launch: lines by days since launch, to compare chains/assets at the same age.

Use when: "at the same age, who is ahead". Each series is a list of [day_n, value] or a list of values (day = 1..n).
The legend names series; direct labels only for today's value if wanted (opts.end_values).

panel:
  series: [{key: "series.chain_a", label, role, lw?}]
  opts: pair (true: elements are [day, value]), max_day (112), yfmt (usd_b), mark_day (112), mark_label,
        end_values (false), end_labels (false: end label with name "A $1.14B"), short (short names for end_labels: {"Chain A": "A"})
  layers: see bin/layers.py
"""

import numpy as np

from chartkit import FMT, resolve


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    max_day = o.get("max_day")
    ends, out = [], []
    for s in panel["series"]:
        raw = resolve(data, s["key"])
        if o.get("pair", True) and raw and isinstance(raw[0], (list, tuple)):
            x = np.array([p[0] for p in raw], dtype=float)
            y = np.array([p[1] for p in raw], dtype=float)
        else:
            y = np.array(raw, dtype=float)
            x = np.arange(1, len(y) + 1)
        if max_day:
            m = x <= max_day
            x, y = x[m], y[m]
        role = s["role"]
        lw = s.get("lw", kit.s["lines"].get(role, 1.6))
        ax.plot(x, y, color=kit.color(role), lw=lw, zorder=3 if role == "accent" else 2)
        out.append({"label": s["label"], "role": role, "x": x, "y": y})
        if o.get("end_values") and len(y):
            ends.append((x[-1], y[-1], role, s["label"]))
    if max_day:
        ax.set_xlim(0, max_day * (1.09 if o.get("end_labels") else 1.02))  # end_labels need room for "A $1.14B" on the right
        ticks = [1] + [t for t in range(28, max_day + 1, 28)]
        ax.set_xticks(ticks)
        ax.set_xticklabels([str(t) for t in ticks])  # "day 1" would collide with the y-axis $0 label; put "days since launch" in the panel title
    if o.get("mark_day"):
        ax.axvline(o["mark_day"], color=kit.c["muted"], lw=0.9, ls=(0, (2, 3)))
        if o.get("mark_label"):
            ax.text(o["mark_day"], ax.get_ylim()[1], " " + o["mark_label"], color=kit.c["muted"],
                    fontsize=kit.t["label"] - 1, fontfamily=kit.body, va="top")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.05)
    if ends:
        ys = kit.spread([e[1] for e in ends], ax.get_ylim()[1] * 0.045)
        short = o.get("short", {})
        for (x1, y1, role, lab), ye in zip(ends, ys):
            txt = FMT[o.get("yfmt", "usd_b")](y1)
            if o.get("end_labels"):
                txt = f"{short.get(lab, lab)} {txt}"
            kit.callout(ax, x1, ye, txt, role=role, dx=6, dy=0, va="center")
    kit.yfmt(ax, o.get("yfmt", "usd_b"))
    # shared x axis for layers: use the longest series
    ref = max(out, key=lambda e: len(e["x"])) if out else None
    top = None
    if ref is not None:
        top = np.zeros(len(ref["x"]))
        for e in out:
            m = min(len(e["y"]), len(top))
            top[:m] = np.maximum(top[:m], e["y"][:m])
    return {"legend": [(s["label"], s["role"]) for s in panel["series"]],
            "x": ref["x"] if ref else [], "xkeys": [int(v) for v in ref["x"]] if ref else [], "top": top, "series": out}
