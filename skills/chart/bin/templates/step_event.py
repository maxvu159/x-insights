"""
step_event: hourly step series with event markers. Use for "an asset moved after an event".

panel:
  x: "rows[].t"      epoch seconds or ISO
  series: [{key: "rows[].mc", label, role}]  (usually 1 accent series, legend hides itself)
  opts: yfmt (usd_m), fill (true), tz_label ("UTC")
  events: [{x: epoch|ISO, label}]
"""

from datetime import datetime, timezone

import numpy as np
from matplotlib import dates as mdates

from chartkit import FMT, parse_date, resolve


def _t(v):
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, tz=timezone.utc)
    return parse_date(v)


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    xs = [_t(v) for v in resolve(data, panel["x"])]
    for s in panel["series"]:
        y = np.array(resolve(data, s["key"]), dtype=float)
        role = s["role"]
        ax.step(xs, y, where="post", color=kit.color(role), lw=kit.s["lines"].get(role, 2.0), zorder=3)
        if o.get("fill", True) and role == "accent":
            ax.fill_between(xs, y, 0, step="post", color=kit.color(role), alpha=0.07, lw=0)
        i = int(y.argmax())
        kit.callout(ax, xs[i], y[i], FMT[o.get("yfmt", "usd_m")](y[i]) + " high", dy=6, ha="center")
    for ev in panel.get("events", []):
        x = _t(ev["x"])
        ax.axvline(x, color=kit.color("negative"), lw=1.2, ls=(0, (3, 3)))
        if ev.get("label"):
            ax.text(x, ax.get_ylim()[1] * 0.97, " " + ev["label"], color=kit.color("negative"),
                    fontsize=kit.t["label"], fontfamily=kit.body, va="top", ha="left")
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=o.get("hours", 4)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=timezone.utc))
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(0, ax.get_ylim()[1] * 1.1)
    kit.yfmt(ax, o.get("yfmt", "usd_m"))
    return {"legend": [(s["label"], s["role"]) for s in panel["series"]] if len(panel["series"]) > 1 else []}
