"""Shared helpers for templates."""

import re

from chartkit import FMT, parse_date, resolve


def val(data, x):
    """x is a number -> return it. x is a data path string ('rows[].spot', 'v3.apr') -> resolve.
    Any other string -> returned as is (a label)."""
    if isinstance(x, (int, float)) or x is None:
        return x
    if isinstance(x, dict) and "expr" in x:
        # {"expr": "locked / supply"}: names in the expression are top-level numeric keys of data
        env = {k: v for k, v in (data or {}).items() if isinstance(v, (int, float))}
        return eval(x["expr"], {"__builtins__": {}}, env)  # noqa: S307  (local spec)
    if isinstance(x, str) and re.fullmatch(r"[A-Za-z_][\w\-]*(\[\])?(\.[\w\-]+(\[\])?)*", x) and "." in x or (isinstance(x, str) and x.endswith("[]")):
        try:
            r = resolve(data, x)
            return x if isinstance(r, dict) else r
        except (KeyError, IndexError, TypeError):
            return x
    if isinstance(x, str) and x in (data or {}) and not isinstance(data[x], dict):
        return data[x]
    return x


def items_of(panel, data):
    """Normalise the item list: panel['items'] (hand-written items, values may be data paths)
    or panel['rows'] (path to a list of dicts) + a 'fields' mapping."""
    if panel.get("items"):
        out = []
        for it in panel["items"]:
            d = dict(it)
            for k in ("value", "pos", "neg", "note"):
                if k in d:
                    d[k] = val(data, d[k])
            out.append(d)
        return out
    rows = resolve(data, panel["rows"])
    f = panel.get("fields", {})
    out = []
    for r in rows:
        d = {"label": r.get(f.get("label", "label")), "value": r.get(f.get("value", "value"))}
        if f.get("note"):
            d["note"] = r.get(f["note"])
        if f.get("role"):
            d["role"] = r.get(f["role"])
        for k in ("pos", "neg"):
            if f.get(k):
                d[k] = r.get(f[k])
        out.append(d)
    return out


def fmt_of(o, default="num"):
    return FMT[o.get("fmt", default)]


def dates_of(data, key):
    return [parse_date(x) for x in resolve(data, key)]


def left_margin(ax, kit, labels):
    """Shift the axes right so y tick labels (item names) stay inside the safe area."""
    n = max((len(str(l)) for l in labels), default=0)
    pt = (kit.t["label"] + 1) * 0.56 * n + 10          # estimated text width, pt
    fig_w_in = ax.figure.get_size_inches()[0]
    dx = pt / 72 / fig_w_in
    x, y, w, h = ax.get_position().bounds
    ax.set_position([x + dx, y, w - dx, h])
