"""
line_compare: main line (accent) + comparison side (compare), legend, optional indexing.

Use when: comparing the trend of 2 to 4 series over time. With 'index_to' every series is rebased to 100 at one point
to compare speed (chain vs coin). Not for composition (use stacked_columns).

panel:
  x: "chain[].d"                            dates
  series: [{key, label, role, lw?}]         lw optional
  opts: index_to (null | "first" | "YYYY-MM-DD"), yfmt (usd_b|usd_m|pct|num|x), xticks (5),
        end_values (false): label the last value of each series, fill (true): light fill under the accent line,
        ymin (null): force the y-axis floor (e.g. 0 for a non-negative % series), xpad (0): extend the x axis N days on both ends so circled points are not clipped
  events: [{x: "YYYY-MM-DD", label}]        vertical rules
"""

from datetime import timedelta

import numpy as np
from matplotlib import dates as mdates

from chartkit import FMT, parse_date, resolve


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    xs = [parse_date(x) for x in resolve(data, panel["x"])]
    ser = panel["series"]
    ys = [np.array(resolve(data, s["key"]), dtype=float) for s in ser]
    idx = o.get("index_to")
    if idx:
        i0 = 0 if idx == "first" else xs.index(parse_date(idx))
        ys = [y / y[i0] * 100 for y in ys]
    for s, y in zip(ser, ys):
        role = s["role"]
        lw = s.get("lw", kit.s["lines"].get(role, 1.8))
        ax.plot(xs, y, color=kit.color(role), lw=lw, solid_capstyle="round", zorder=3 if role == "accent" else 2)
        if o.get("fill", True) and role == "accent":
            ax.fill_between(xs, y, np.nanmin([np.nanmin(v) for v in ys]) if idx else 0, color=kit.color(role), alpha=0.07, lw=0)
    if idx:
        ax.axhline(100, color=kit.c["muted"], lw=0.8, ls=(0, (3, 3)))
        kit.yfmt(ax, "raw")
    else:
        kit.yfmt(ax, o.get("yfmt", "usd_b"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=o.get("xticks", 6)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b"))
    pad = timedelta(days=o.get("xpad", 0))
    ax.set_xlim(xs[0] - pad, xs[-1] + pad)
    if o.get("ymin") is not None:
        ax.set_ylim(bottom=o["ymin"])
    for ev in panel.get("events", []):
        x = parse_date(ev["x"])
        ax.axvline(x, color=kit.c["muted"], lw=0.9, ls=(0, (2, 3)))
        if ev.get("label"):
            ax.text(x, ax.get_ylim()[1], " " + ev["label"], color=kit.c["muted"], fontsize=kit.t["label"] - 1,
                    fontfamily=kit.body, va="top", ha="left")
    if o.get("end_values"):
        f = FMT["raw" if idx else o.get("yfmt", "usd_b")]
        ends = kit.spread([y[-1] for y in ys], (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.045)
        for s, y, ye in zip(ser, ys, ends):
            kit.callout(ax, xs[-1], ye, (f"{y[-1]:.0f}" if idx else f(y[-1])), role=s["role"], dx=6, dy=0, va="center")
    return {"legend": [(s["label"], s["role"]) for s in ser], "x": xs, "xkeys": [d.strftime("%Y-%m-%d") for d in xs],
            "top": np.max(np.vstack(ys), axis=0), "series": [{"label": s["label"], "role": s["role"], "x": xs, "y": y} for s, y in zip(ser, ys)]}
