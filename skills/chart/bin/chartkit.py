"""
chartkit: shared layer for the chart skill.

Reads a style (json), loads fonts, creates a fixed frame (no tight bbox), draws title / subtitle /
source / handle inside the safe area, a horizontal legend, number formatters, saves PNG + SVG.
Reads no data at import time. Templates and render.py call into it.

Usage:
    from chartkit import Kit
    kit = Kit("dark")                      # style name in styles/ or a path to a json file
    fig = kit.figure("16x9")
    ax = kit.axes(fig)                    # default plot area (layout single)
    ... draw ...
    kit.legend(fig, [("Series B", "compare"), ("Series A", "accent")])
    kit.frame(fig, title, subtitle, source)
    png, svg = kit.save(fig, slug, n=1, desc="...")
"""

import glob
import json
import os
import re
import textwrap
from datetime import date, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
# Workspace for data/, specs/, outputs/. Defaults to ./insights under the current directory.
HOME = Path(os.environ.get("INSIGHTS_HOME", "insights")).expanduser().resolve()

_FONTS_LOADED = set()


def _addfonts(pattern):
    if pattern in _FONTS_LOADED:
        return
    for f in glob.glob(os.path.expanduser(pattern), recursive=True):
        try:
            font_manager.fontManager.addfont(f)
        except Exception:  # noqa: BLE001
            pass
    _FONTS_LOADED.add(pattern)


def _font_ok(name):
    try:
        font_manager.findfont(font_manager.FontProperties(family=name), fallback_to_default=False)
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------- formatter ----------

def fmt_usd(v, d=1):
    a = abs(v)
    s = "-" if v < 0 else ""
    if a >= 1e9:
        return f"{s}${a / 1e9:,.{d}f}B"
    if a >= 1e6:
        return f"{s}${a / 1e6:,.{d}f}M"
    if a >= 1e3:
        return f"{s}${a / 1e3:,.0f}K"
    return f"{s}${a:,.0f}"


def fmt_usd_b(v, _=None):
    if v == 0:
        return "$0"
    if abs(v) >= 1e9:
        t = f"{v / 1e9:.2f}".rstrip("0").rstrip(".")
        return f"${t}B"
    return f"${v / 1e6:,.0f}M"


def fmt_usd_m(v, _=None):
    return "$0" if v == 0 else f"${v / 1e6:,.0f}M"


def fmt_pct(v, _=None):
    return f"{v:.0%}"


def fmt_pct1(v, _=None):
    return f"{v:.1%}"


def fmt_num(v, _=None):
    a = abs(v)
    if a >= 1e9:
        return f"{v / 1e9:g}B"
    if a >= 1e6:
        return f"{v / 1e6:g}M"
    if a >= 1e3:
        return f"{v / 1e3:g}K"
    return f"{v:g}"


def fmt_usd2(v, _=None):
    """2 decimals for B: two close bars ($4.47B vs $4.37B) are not rounded to 4.5 vs 4.4."""
    a = abs(v)
    if a >= 1e9:
        return f"${v / 1e9:,.2f}B"
    if a >= 1e6:
        return f"${v / 1e6:,.1f}M"
    return f"${v:,.0f}"


def fmt_x0(v, _=None):
    return f"{v:.0f}x" if abs(v - round(v)) < 1e-9 else f"{v:.1f}x"


def fmt_x(v, _=None):
    return f"{v:.1f}x"


FMT = {"usd": fmt_usd, "usd2": fmt_usd2, "usd_b": fmt_usd_b, "usd_m": fmt_usd_m, "pct": fmt_pct, "pct1": fmt_pct1,
       "num": fmt_num, "x": fmt_x, "x0": fmt_x0, "raw": lambda v, _=None: f"{v:g}"}


def parse_date(s):
    if isinstance(s, (date, datetime)):
        return s
    s = str(s)
    for f in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue
    raise ValueError(f"cannot parse date: {s}")


def nice_date(s):
    """'2026-10-21 19:06 UTC' -> '21 Oct 2026, 19:06 UTC'; '2026-10-21' -> '21 Oct 2026'."""
    t = str(s).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ]?(\d{2}:\d{2})?", t)
    if not m:
        return t
    d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    out = f"{d.day} {d:%b %Y}"
    if m.group(4):
        out += f", {m.group(4)} UTC"
    return out


# ---------- data path ----------

def resolve(data, key):
    """Get a value by path 'a.b[].c' or 'a.b[].1' (index into a nested list).
    '[]' = map over a list. Returns a list when '[]' is present, a scalar otherwise."""
    if key is None:
        return None
    parts = key.split(".")

    def walk(node, parts):
        if not parts:
            return node
        p, rest = parts[0], parts[1:]
        if p.endswith("[]"):
            name = p[:-2]
            lst = node[name] if name else node
            return [walk(x, rest) for x in lst]
        if re.fullmatch(r"-?\d+", p):
            return walk(node[int(p)], rest)
        return walk(node[p], rest)

    return walk(data, parts)


def load_data(spec):
    """Read the spec's data file. Returns (data, asof). 'snapshot' selects a sub-block (e.g. 'v3')."""
    d = spec.get("data") or {}
    f = d.get("file")
    if not f:
        return {}, None
    p = Path(f)
    if not p.is_absolute():
        p = Path(f).resolve() if Path(f).exists() else HOME / f
    with open(p) as fh:
        data = json.load(fh)
    asof = data.get("asof") or data.get("as_of")
    snap = d.get("snapshot")
    if snap:
        sub = data.get(snap)
        if isinstance(sub, dict):
            asof = sub.get("asof") or data.get(f"{snap}_asof") or asof
    return data, asof


# ---------- Kit ----------

class Kit:
    def __init__(self, style="dark"):
        p = Path(style)
        if not p.suffix:
            p = SKILL / "styles" / f"{style}.json"
        with open(p) as fh:
            self.s = json.load(fh)
        if os.environ.get("INSIGHTS_HANDLE"):
            self.s["handle"] = os.environ["INSIGHTS_HANDLE"]
        self.name = self.s["name"]
        self.c = self.s["colors"]
        self.t = self.s["type"]
        self.w = self.s["weights"]
        self.lay = dict(self.s["layout"])
        self.safe = self.s["safe"]
        self.shift = 0.0          # push the plot area down for a 2-line subtitle (plan_text)
        f = self.s["fonts"]
        for pat in [f.get("files", ""), "~/Library/Fonts/Inter*", "~/.local/share/fonts/Inter*", "/usr/share/fonts/**/Inter*"]:
            _addfonts(pat)
        self.body = f["body"] if _font_ok(f["body"]) else f.get("fallback", "DejaVu Sans")
        self.display = f["display"] if _font_ok(f["display"]) else self.body
        if self.body != f["body"]:
            print(f"[chartkit] font {f['body']} not found, using {self.body}")
        plt.rcParams.update({
            "figure.facecolor": self.c["bg"], "axes.facecolor": self.c["bg"], "savefig.facecolor": self.c["bg"],
            "font.family": self.body, "font.size": self.t["label"], "text.color": self.c["text"],
            "axes.edgecolor": self.c["grid"], "axes.labelcolor": self.c["muted"],
            "xtick.color": self.c["muted"], "ytick.color": self.c["muted"],
            "axes.grid": False, "grid.color": self.c["grid"], "grid.linewidth": 0.6,
            "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.spines.bottom": False,
            "text.parse_math": False,                       # strings with two $ signs do not become mathtext
            "svg.fonttype": self.s["save"].get("svg_fonttype", "path"),
        })

    # --- colors ---
    def color(self, role):
        if role in self.c:
            return self.c[role]
        if isinstance(role, str) and role.startswith("#"):
            raise ValueError(f"specs must not use hex colors ({role}); use a role: {list(self.c)}")
        raise KeyError(f"color role not in style {self.name}: {role}")

    def on(self, role):
        """Text color to place on a fill of this role: picked by the fill's luminance, not by role name."""
        h = self.color(role).lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        bg = self.c["bg"].lstrip("#")
        br, bgc, bb = (int(bg[i:i + 2], 16) / 255 for i in (0, 2, 4))
        lum_bg = 0.2126 * br + 0.7152 * bgc + 0.0722 * bb
        # dark bg: light fill -> bg-colored (dark) text; dark fill -> text color (light). Light bg: the reverse.
        return self.c["bg"] if abs(lum - lum_bg) > 0.35 else self.c["text"]

    # --- frame ---
    def figure(self, frame="16x9"):
        w, h = self.s["frames"][frame]
        fig = plt.figure(figsize=(w, h), facecolor=self.c["bg"])
        fig._kit_frame = frame
        self.fig_w, self.fig_h = w, h
        return fig

    def line_h(self, size, spacing=1.15):
        """Height of one text line (fraction of figure height)."""
        return size * spacing / 72 / getattr(self, "fig_h", 6.75)

    def plan_text(self, title, subtitle=""):
        """Call before creating axes: counts title and subtitle lines, pushes the plot area down if needed."""
        nt = self.wrap(title, self.t["title"], 0.80).count("\n")
        ns = self.wrap(subtitle, self.t["subtitle"]).count("\n") if subtitle else 0
        self.shift = nt * self.line_h(self.t["title"], 1.1) + ns * self.line_h(self.t["subtitle"], 1.25)
        return self.shift

    def rect(self, which="plot", fig=None):
        """Figure coords [x, y, w, h] for each region, from the style layout (shift already applied)."""
        sx = self.safe["x"]
        L = dict(self.lay)
        L["plot_top"] -= self.shift
        L["legend_y"] -= self.shift
        full_w = 1 - 2 * sx
        pad = L.get("ytick_pad", 0.045)      # keeps y tick labels inside the safe area
        if which == "plot":
            return [sx + pad, L["plot_bottom"], full_w - pad, L["plot_top"] - L["plot_bottom"]]
        if which == "hero_row":
            return [sx, L["plot_top"] - L["hero_h"], full_w, L["hero_h"]]
        if which == "plot_under_hero":
            top = L["plot_top"] - L["hero_h"] - L["gap"]
            return [sx + pad, L["plot_bottom"], full_w - pad, top - L["plot_bottom"]]
        if which == "main":
            w = full_w - L["side_w"] - L["gap"]
            return [sx + pad, L["plot_bottom"], w - pad, L["plot_top"] - L["plot_bottom"]]
        if which == "side":
            w = L["side_w"]
            return [1 - sx - w, L["plot_bottom"], w, L["plot_top"] - L["plot_bottom"]]
        if which in ("main_under_hero", "side_under_hero"):
            top = L["plot_top"] - L["hero_h"] - L["gap"]
            w_side = L["side_w"]
            if which == "main_under_hero":
                return [sx + pad, L["plot_bottom"], full_w - w_side - L["gap"] - pad, top - L["plot_bottom"]]
            return [1 - sx - w_side, L["plot_bottom"], w_side, top - L["plot_bottom"]]
        if which in ("left", "right"):
            w = (full_w - L["gap"]) / 2
            x = sx if which == "left" else sx + w + L["gap"]
            return [x + pad, L["plot_bottom"], w - pad, L["plot_top"] - L["plot_bottom"]]
        raise KeyError(which)

    def axes(self, fig, which="plot", rect=None):
        ax = fig.add_axes(rect or self.rect(which))
        ax.set_facecolor(self.c["bg"])
        ax.tick_params(length=0, colors=self.c["muted"], labelsize=self.t["tick"])
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_fontfamily(self.body)
        ax.grid(axis="y", color=self.c["grid"], lw=0.6)
        ax.set_axisbelow(True)
        return ax

    # --- text ---
    def wrap(self, text, size, width_frac=None):
        """Estimated wrapping: number of characters that fit one line at font 'size' in the safe area."""
        if not text:
            return ""
        fig_w = getattr(self, "fig_w", 12.0)
        usable = fig_w * (width_frac or (1 - 2 * self.safe["x"])) * 72    # pt
        per_char = size * 0.52
        n = max(20, int(usable / per_char))
        return "\n".join(textwrap.wrap(text, n))

    def frame(self, fig, title, subtitle="", source="", handle=True, asof=None):
        """Title anchors at the top of the safe area going down; source anchors at the bottom going up. Multi-line
        text pushes content down (plan_text already computed the plot shift)."""
        sx, L = self.safe["x"], self.lay
        top = 1 - self.safe["y"]
        tw = self.wrap(title, self.t["title"], 0.80)
        fig.text(sx, top, tw, fontsize=self.t["title"], linespacing=1.1, fontfamily=self.display,
                 fontweight=self.w["title"], color=self.c["text"], ha="left", va="top")
        if subtitle:
            y = top - (tw.count("\n") + 1) * self.line_h(self.t["title"], 1.1) - 0.018
            fig.text(sx, y, self.wrap(subtitle, self.t["subtitle"]), fontsize=self.t["subtitle"], linespacing=1.25,
                     fontfamily=self.body, color=self.c["muted"], ha="left", va="top")
        if source:
            src = source if source.lower().startswith("source") else f"Source: {source}"
            if asof and str(asof) not in src and nice_date(asof) not in src:
                src += f" · {nice_date(asof)}"
            fig.text(sx, self.safe["y"], self.wrap(src, self.t["source"]), fontsize=self.t["source"], linespacing=1.3,
                     fontfamily=self.body, color=self.c["muted"], ha="left", va="bottom")
        if handle and self.s.get("handle"):
            fig.text(1 - sx, top, self.s["handle"], fontsize=self.t["handle"], fontfamily=self.body,
                     color=self.c["muted"], ha="right", va="top")

    def legend(self, fig, items, y=None, x=None):
        """items: [(label, role)]. One horizontal row under the subtitle. Not drawn for <2 items."""
        items = [(l, r) for l, r in items if l]
        if len(items) < 2:
            return None
        handles = [Patch(facecolor=self.color(r), edgecolor="none", label=l) for l, r in items]
        leg = fig.legend(handles=handles, loc="upper left",
                         bbox_to_anchor=(x if x is not None else self.safe["x"], y if y is not None else self.lay["legend_y"] - self.shift),
                         ncol=min(len(items), self.s["legend"].get("ncol", 4)), frameon=False,
                         handlelength=1.0, handleheight=1.0, columnspacing=1.6, handletextpad=0.6,
                         prop={"family": self.body, "size": self.t["legend"]}, labelcolor=self.c["text"], borderaxespad=0)
        return leg

    def hero(self, fig, items, rect=None):
        """items: [{"value": "56%", "label": "...", "role": "accent"}], laid out horizontally inside rect."""
        x0, y0, w, h = rect or self.rect("hero_row")
        n = max(1, len(items))
        for i, it in enumerate(items):
            x = x0 + i * (w / n)
            fig.text(x, y0 + h * 0.45, it["value"], fontsize=it.get("size", self.t["hero"]), fontfamily=self.display,
                     fontweight=self.w["hero"], color=self.color(it.get("role", "accent")), ha="left", va="baseline")
            if it.get("label"):
                fig.text(x, y0 + h * 0.12, self.wrap(it["label"], self.t["hero_label"], w / n * 0.95),
                         fontsize=self.t["hero_label"], fontfamily=self.body, color=self.c["muted"], ha="left", va="baseline")

    def callout(self, ax, x, y, text, role="text", dx=0, dy=8, ha="left", va="bottom", on_dark=False):
        col = self.c["bg"] if on_dark else self.color(role) if role != "text" else self.c["text"]
        ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                    color=col, fontsize=self.t["callout"], fontfamily=self.body, fontweight=self.w["callout"],
                    annotation_clip=False)

    @staticmethod
    def spread(values, min_gap):
        """Push y values at least min_gap apart, keeping order. Used for line end labels."""
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = list(values)
        for a, b in zip(order, order[1:]):
            if out[b] - out[a] < min_gap:
                out[b] = out[a] + min_gap
        return out

    def yfmt(self, ax, kind):
        import matplotlib.ticker as mt
        ax.yaxis.set_major_formatter(mt.FuncFormatter(FMT[kind]))

    def xfmt(self, ax, kind):
        import matplotlib.ticker as mt
        ax.xaxis.set_major_formatter(mt.FuncFormatter(FMT[kind]))

    # --- save ---
    def save(self, fig, slug, n=1, desc="chart", out_root=None, preview=None):
        """PNG 300dpi + SVG (text as paths), fixed frame, NO tight bbox.
        out: outputs/<slug>/final/FINAL-<n>-hook_<desc>.(png|svg). preview = alternative png path."""
        if preview:
            fig.savefig(preview, dpi=self.s["save"]["dpi"], facecolor=self.c["bg"])
            plt.close(fig)
            return preview, None
        root = Path(out_root) if out_root else HOME / "outputs"
        d = root / slug / "final"
        d.mkdir(parents=True, exist_ok=True)
        base = d / f"FINAL-{n}-hook_{desc}"
        png, svg = f"{base}.png", f"{base}.svg"
        fig.savefig(png, dpi=self.s["save"]["dpi"], facecolor=self.c["bg"])
        fig.savefig(svg, facecolor=self.c["bg"])
        plt.close(fig)
        return png, svg
