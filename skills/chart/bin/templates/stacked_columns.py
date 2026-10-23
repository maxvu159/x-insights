"""
stacked_columns: stacked columns per period.

Use when: there is a total and parts that add up to it, and the mix over time matters.
 - gap 0 + daily      -> looks like an area but every day stays readable (preferred over area).
 - period week/month  -> aggregated per week/month, each period's number is readable.
 - pct true           -> 100%: only when the point is the share and the total does not matter (or a total panel is added).

panel:
  x:       "rows[].d"                      ISO date or label
  series:  [{key, label, role}]            bottom to top
  opts:    gap (0..1, default style.bar_gap), pct (bool), period (null|week|month),
           yfmt (usd_b|usd_m|pct|num), ymax_pad (1.15), xticks (label count, default 5),
           labels ("none"|"total"|"segments"; segments only when period != null)
  overlay: {key, label, role, lw?}   line over the columns, SAME unit as the columns (no twin axis), bg halo to separate it
  layers:  see bin/layers.py (marks, spans, notes, points). With period, daily array variables in marks/notes
           are summed per period (template returns "bucket"); spans/points "at" use the period's first-day key (ISO)
  callouts: [{at: first|last|max|min|<index>, value: "p1+p2", text: "share {v:.0%}", role, dy, on_bar}]
    variables in value: t (total), s0..sN (values), p0..pN (shares)
"""

from collections import OrderedDict
from datetime import timedelta

import numpy as np

from chartkit import FMT, parse_date, resolve


def _period_key(d, period, anchor):
    if period == "week":
        # 7-day windows from the first day (anchor); week_anchor="monday" uses calendar weeks
        if anchor == "monday":
            return d - timedelta(days=d.weekday())
        return anchor + timedelta(days=((d - anchor).days // 7) * 7)
    if period == "month":
        return d.replace(day=1)
    return d


def _aggregate(dates, cols, period, anchor_mode="first"):
    """Aggregate by period. Also returns bucket: the period index of each day, so layers can sum daily arrays."""
    if not period:
        return dates, cols, None
    anchor = "monday" if anchor_mode == "monday" else dates[0]
    buckets = OrderedDict()
    bucket = []
    for i, d in enumerate(dates):
        k = _period_key(d, period, anchor)
        buckets.setdefault(k, np.zeros(len(cols)))
        buckets[k] += np.array([c[i] for c in cols])
        bucket.append(list(buckets).index(k))
    keys = list(buckets)
    arr = np.array([buckets[k] for k in keys]).T
    return keys, [arr[j] for j in range(len(cols))], bucket


def _xlabel(d, period, n=99):
    if period == "week":
        e = d + timedelta(days=6)
        if n > 6:
            return f"{d.day} {d:%b}"
        return f"{d.day} to {e.day} {e:%b}" if d.month == e.month else f"{d.day} {d:%b} to {e.day} {e:%b}"
    if period == "month":
        return d.strftime("%b %Y") if d.month == 1 else d.strftime("%b")
    return d.strftime("%-d %b")


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    raw_x = resolve(data, panel["x"])
    is_date = True
    try:
        dates = [parse_date(x) for x in raw_x]
    except Exception:  # noqa: BLE001
        is_date = False
        dates = list(raw_x)
    series = panel["series"]
    cols = [np.array(resolve(data, s["key"]), dtype=float) for s in series]
    keep = None
    ov = panel.get("overlay")
    ov_y = np.array(resolve(data, ov["key"]), dtype=float) if ov else None
    if is_date and (o.get("from") or o.get("to")):
        lo = parse_date(o["from"]) if o.get("from") else None
        hi = parse_date(o["to"]) if o.get("to") else None
        keep = [i for i, d in enumerate(dates) if (lo is None or d >= lo) and (hi is None or d <= hi)]
        dates = [dates[i] for i in keep]
        cols = [c[keep] for c in cols]
        if ov_y is not None:
            ov_y = ov_y[keep]
    period = o.get("period")
    bucket = None
    if is_date and period:
        dates, cols, bucket = _aggregate(dates, cols, period, o.get("week_anchor", "first"))
        if ov_y is not None:
            ov_y = np.bincount(np.asarray(bucket), weights=ov_y, minlength=len(dates))
    n = len(dates)
    tot = np.sum(cols, axis=0)
    pct = bool(o.get("pct"))
    vals = [c / np.where(tot == 0, 1, tot) for c in cols] if pct else cols
    gap = o.get("gap", kit.s["bar_gap"])
    w = 1 - gap
    x = np.arange(n)
    bottom = np.zeros(n)
    for s, v in zip(series, vals):
        ax.bar(x, v, w, bottom=bottom, color=kit.color(s["role"]), linewidth=0, zorder=2)
        bottom = bottom + v
    top = tot.copy()
    if ov is not None and not pct:
        ax.plot(x, ov_y, color=kit.c["bg"], linewidth=ov.get("lw", 2.4) + 2.6, zorder=3)
        ax.plot(x, ov_y, color=kit.color(ov["role"]), linewidth=ov.get("lw", 2.4), zorder=4)
        top = np.maximum(top, ov_y)
    # axes
    if pct:
        ax.set_ylim(0, 1)
        ax.set_yticks([.25, .5, .75, 1])
        kit.yfmt(ax, "pct")
    else:
        ax.set_ylim(0, top.max() * o.get("ymax_pad", 1.15))
        kit.yfmt(ax, o.get("yfmt", "usd_b"))
        ax.yaxis.set_major_locator(__import__("matplotlib.ticker", fromlist=["MaxNLocator"]).MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10]))
    k = o.get("xticks", 5 if n > 8 else n)
    idx = sorted(set(np.linspace(0, n - 1, k).round().astype(int).tolist()))
    ax.set_xticks(idx)
    ax.set_xticklabels([_xlabel(dates[i], period, n) if is_date else str(dates[i]) for i in idx])
    ax.set_xlim(-0.5 - gap / 2, n - 0.5 + gap / 2)
    # labels on columns
    labels = o.get("labels", "none")
    fmt = FMT["pct" if pct else o.get("yfmt", "usd_b")]
    if labels == "total" and not pct:
        for i in range(n):
            kit.callout(ax, x[i], tot[i], FMT["usd"](tot[i]) if o.get("yfmt", "usd_b").startswith("usd") else fmt(tot[i]),
                        dy=5, ha="center")
    if labels == "segments" and period:
        for s, v, b in zip(series, vals, _bottoms(vals)):
            for i in range(n):
                if v[i] / (1 if pct else tot.max()) < 0.06:
                    continue
                txt = fmt(v[i]) if pct else FMT["usd"](v[i])
                ax.text(x[i], b[i] + v[i] / 2, txt, ha="center", va="center", fontsize=kit.t["label"],
                        fontfamily=kit.body, color=kit.on(s["role"]))
    # callouts
    for c in panel.get("callouts", []):
        at = c.get("at", "last")
        i = {"first": 0, "last": n - 1, "max": int(tot.argmax()), "min": int(tot.argmin())}.get(at, at)
        i = int(i)
        env = {"t": tot[i]}
        for j, col in enumerate(cols):
            env[f"s{j}"] = col[i]
            env[f"p{j}"] = col[i] / tot[i] if tot[i] else 0
        v = eval(c.get("value", "t"), {"__builtins__": {}}, env)  # noqa: S307  (local spec, not external input)
        text = c["text"].format(v=v, **env)
        ytop = 1 if pct else tot[i]
        ha = "left" if i < n / 2 else "right"
        if c.get("on_bar"):
            kit.callout(ax, x[i], (1 - v) if pct else tot[i], text, dy=-14, ha=ha, va="top", on_dark=True)
        else:
            kit.callout(ax, x[i], ytop, text, role=c.get("role", "text"), dy=c.get("dy", 8), ha=ha)
    leg = [(s["label"], s["role"]) for s in series] + ([(ov["label"], ov["role"])] if ov else [])
    ser_out = [{"label": s["label"], "role": s["role"], "x": x, "y": v} for s, v in zip(series, vals)]
    if ov:
        ser_out.append({"label": ov["label"], "role": ov["role"], "x": x, "y": ov_y})
    return {"legend": leg, "x": x, "xkeys": [d.strftime("%Y-%m-%d") if is_date else d for d in dates], "top": top,
            "series": ser_out, "keep": keep, "bucket": bucket}


def _bottoms(vals):
    out, acc = [], np.zeros_like(vals[0])
    for v in vals:
        out.append(acc.copy())
        acc = acc + v
    return out
