"""
segment_bar: one 100% horizontal bar split into segments, labels inside, small captions above.

Use when: "one total split by who holds how much" (e.g. locked supply: burned / treasury / staked).
Usually paired with hero (big numbers) in layout hero_top or hero_main_side.

panel:
  items: [{label, value, role, caption?}]   absolute values; caption is the small text above the segment
  opts: fmt (num), min_label (0.05: segments below this share get no inside label), bar_h (0.5)
"""

from ._common import fmt_of, items_of


YTICKS = False   # no numeric y tick labels, render gives ytick_pad back to the template


def draw(ax, panel, data, kit, ctx):
    o = panel.get("opts", {})
    items = items_of(panel, data)
    f = fmt_of(o)
    tot = sum(float(d["value"]) for d in items)
    x = 0.0
    h = o.get("bar_h", 0.5)
    for d in items:
        v = float(d["value"]) / tot
        role = d.get("role", "compare")
        ax.barh(0, v, left=x, height=h, color=kit.color(role), linewidth=0)
        if v >= o.get("min_label", 0.05):
            ax.text(x + v / 2, 0, f(float(d["value"])), ha="center", va="center", fontsize=kit.t["label"] + 2,
                    fontfamily=kit.body, fontweight=600, color=kit.on(role))
        cap = d.get("caption") or d.get("label")
        if cap:
            small = v < 0.12
            ha = "center" if not small else ("right" if x + v > 0.85 else "left")
            cx = x + v / 2 if ha == "center" else (x + v if ha == "right" else x)
            # small segment: caption goes below the bar so it does not hit its neighbour
            y, va = (h / 2 + 0.12, "bottom") if not small else (-h / 2 - 0.12, "top")
            ax.text(cx, y, cap, ha=ha, va=va, fontsize=kit.t["label"], fontfamily=kit.body,
                    color=kit.color(role) if role == "accent" else kit.c["muted"])
        x += v
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.6, 0.9)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    return {"legend": []}
