"""Shared layers for every template (several layers on one panel).

panel["layers"] = {
  "marks":  {"when": {"expr": "a > b", "vars": {"a": "rows[].x", "b": "rows[].y"}}, "role": "accent"}
            # dot above the bar/line top at periods matching the condition; or "at": [key, ...]. Counts n/N for notes.
  "spans":  [{"last": 7, "label": "last 7 days"} | {"from": key, "to": key, "label": "..."}]   # shaded band; last counts axis periods
  "notes":  [{"pos": "tl"|"tr"|"bl"|"br", "lines": [
               {"text": "Top two: {v} of volume", "value": "share.top2", "fmt": "pct", "role": "compare2", "bold": true, "dot": false}]}]
            # text block inside the plot. {v} = value (data path or {"expr": ...}, optional fmt), {n}/{N} = matching marks / total periods.
  "points": [{"at": key, "series": "Chain A", "text": "...", "role": "accent"},
             {"top_gains": {"series": "Chain A", "k": 3, "text": "+${g}M (day {k})"}}]
            # hollow circle + label; top_gains finds the k biggest gains, labels close together (<= 5 periods) merge.
}
Templates must return in res: "x" (plot positions), "xkeys" (keys: ISO date or day number), "top" (top per period),
"series": [{"label", "role", "x", "y"}], "keep" (original indices kept, if filtered) and "bucket" (period index of each
daily row, if the template aggregated by week/month: daily arrays in marks/notes are then summed per period).
If the template returns none of these, layers are skipped.
"""

import numpy as np
from datetime import datetime, timedelta

from chartkit import FMT, resolve


def _eval(expr, env):
    return eval(expr, {"__builtins__": {}, "np": np}, env)  # noqa: S307  (local spec)


def _vars(data, vars_, res):
    """Variables for expr: data path -> numpy array, filtered by keep then summed by bucket to match the x axis."""
    env = {}
    n = len(res["x"])
    keep, bucket = res.get("keep"), res.get("bucket")
    for k, path in (vars_ or {}).items():
        v = resolve(data, path)
        if isinstance(v, list):
            v = np.array(v, dtype=float)
            if keep is not None and len(v) > len(keep):
                v = v[keep]
            if bucket is not None and len(v) == len(bucket) and len(v) != n:
                v = np.bincount(np.asarray(bucket), weights=v, minlength=n)
        env[k] = v
    return env


def note_line(ln, data, kit, env, res=None):
    """One line of a text block: fills {v} (path or expr, fmt), {n}/{N}; returns (text, color, weight).
    Shared by layers.notes and templates with their own text block (paired_bars)."""
    env = dict(env or {})
    if "value" in ln:
        v = ln["value"]
        v = _eval(v["expr"], _vars(data, v.get("vars"), res or {"x": []})) if isinstance(v, dict) else resolve(data, v)
        env["v"] = FMT[ln["fmt"]](float(v)) if ln.get("fmt") else v
    txt = ln["text"].format(**env)
    if ln.get("dot"):
        txt = "• " + txt
    role = ln.get("role", "muted")
    col = kit.c["muted"] if role == "muted" else kit.color(role)
    return txt, col, (kit.w["callout"] if ln.get("bold") else 400)


def _idx(res, key):
    keys = res["xkeys"]
    for i, k in enumerate(keys):
        if str(k) == str(key) or (isinstance(k, (int, float)) and float(k) == float(key) if _isnum(key) else False):
            return i
    raise KeyError(f"layers: period {key!r} not found on the x axis")


def _isnum(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _half(res):
    x = res["x"]
    if len(x) and isinstance(x[0], datetime):
        return timedelta(hours=12)
    return 0.5 if len(x) < 2 else (x[1] - x[0]) / 2


def apply(ax, panel, data, kit, res):
    L = panel.get("layers") or {}
    if not L or not res or "x" not in res:
        return
    x, top = res["x"], np.array(res["top"], dtype=float)
    n = len(x)
    keep = res.get("keep")
    y0, y1 = ax.get_ylim()
    rng = y1 - y0
    env_counts = {}
    # --- spans
    for sp in L.get("spans", []):
        if "last" in sp:
            i0, i1 = max(0, n - int(sp["last"])), n - 1   # last counts axis periods (weeks if aggregated)
        else:
            i0, i1 = _idx(res, sp["from"]), _idx(res, sp["to"])
        h = _half(res)
        ax.axvspan(x[i0] - h, x[i1] + h, color=kit.c["grid"], alpha=sp.get("alpha", 0.55), linewidth=0, zorder=0)
        if sp.get("label"):
            env_counts["_span_x"] = x[i0] - h
    # --- marks
    m = L.get("marks")
    if m:
        if "at" in m:
            win = [_idx(res, k) for k in m["at"]]
        else:
            env = _vars(data, m["when"].get("vars"), res)
            ok = np.asarray(_eval(m["when"]["expr"], env), dtype=bool)
            win = [i for i in range(n) if ok[i]]
        if win:
            ax.scatter([x[i] for i in win], top[win] + rng * 0.035, s=m.get("size", 14), color=kit.color(m.get("role", "accent")),
                       zorder=6, linewidths=0)
        env_counts.update({"n": len(win), "N": n})
    # --- points
    for p in L.get("points", []):
        if "top_gains" in p:
            g = p["top_gains"]
            s = _series(res, g.get("series"))
            yy = np.asarray(s["y"], dtype=float)
            gains = sorted(((yy[i] - yy[i - 1], i) for i in range(1, len(yy))), reverse=True)[: int(g.get("k", 3))]
            gains.sort(key=lambda t: t[1])
            groups, cur = [], []
            for t in gains:
                if cur and t[1] - cur[-1][1] > g.get("merge_within", 5):
                    groups.append(cur); cur = []
                cur.append(t)
            groups.append(cur)
            for grp in groups:
                for _, i in grp:
                    ax.scatter([s["x"][i]], [yy[i]], s=70, facecolor=kit.c["bg"], edgecolor=kit.color(s["role"]), linewidths=1.8, zorder=6)
                i = grp[-1][1]
                fmt = FMT[g.get("fmt", "usd")]
                txt = ", ".join(g.get("text", "+{g}").format(g=fmt(gg), k=res["xkeys"][j]) for gg, j in grp)
                if g.get("suffix"):
                    txt += g["suffix"].format(k=", ".join(str(res["xkeys"][j]) for _, j in grp))
                kit.callout(ax, s["x"][i], yy[i], txt, role=s["role"], dx=-4, dy=12, ha="right")
        else:
            s = _series(res, p.get("series"))
            i = _idx(res, p["at"])
            ax.scatter([s["x"][i]], [s["y"][i]], s=70, facecolor=kit.c["bg"], edgecolor=kit.color(p.get("role", s["role"])), linewidths=1.8, zorder=6)
            kit.callout(ax, s["x"][i], s["y"][i], p["text"], role=p.get("role", s["role"]), dx=0, dy=12, ha=p.get("ha", "center"))
    # --- notes: raise the y ceiling by line count (so a 3-line block does not hit the top gridline), drop ticks in the text rows
    notes = L.get("notes", [])
    if notes:
        lh = 0.075
        most = max(len(nt["lines"]) for nt in notes if nt.get("pos", "tl")[0] == "t") if any(
            nt.get("pos", "tl")[0] == "t" for nt in notes) else 0
        grow = max(1.28, 1 / (0.93 - lh * most)) if most else 1.28
        if L.get("notes_raise", True):
            # notes_raise false: for a declining series with the text in the low corner (e.g. "tr" when tall bars
            # are on the left), raising the ceiling would leave an empty band above the tall bars
            ax.set_ylim(y0, y0 + rng * grow)
            ax.set_yticks([t for t in ax.get_yticks() if t <= y1])
        for note in notes:
            pos = note.get("pos", "tl")
            xa = 0.0 if pos[1] == "l" else 1.0
            ha = "left" if pos[1] == "l" else "right"
            ya = 0.985 if pos[0] == "t" else 0.04 + lh * (len(note["lines"]) - 1)
            if pos[0] == "t" and note.get("x") == "span" and "_span_x" in env_counts:
                xa = ax.transAxes.inverted().transform(ax.transData.transform((_num(env_counts["_span_x"], ax), 0)))[0] + 0.008
                ha = "left"
            for ln in note["lines"]:
                txt, col, wt = note_line(ln, data, kit, env_counts, res)
                ax.text(xa, ya, txt, transform=ax.transAxes, ha=ha, va="top", fontsize=kit.t["callout"], fontfamily=kit.body,
                        fontweight=wt, color=col, zorder=7)
                ya -= lh


def _num(xv, ax):
    import matplotlib.dates as mdates
    return mdates.date2num(xv) if isinstance(xv, datetime) else xv


def _series(res, which):
    ser = res.get("series") or []
    if not ser:
        raise KeyError("layers.points: template returned no series")
    if which is None:
        return next((s for s in ser if s["role"] == "accent"), ser[0])
    if isinstance(which, int):
        return ser[which]
    for s in ser:
        if s["label"] == which or s["role"] == which:
            return s
    raise KeyError(f"layers.points: series {which!r} not found")
