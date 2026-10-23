#!/usr/bin/env python3
"""
render.py: read spec.json + style -> PNG + SVG.

  python3 <skill dir>/bin/render.py insights/specs/<slug>.json
  python3 <skill dir>/bin/render.py spec.json --style light --preview /tmp/x.png

Spec: see ../spec.md. Layout: single | hero_top | main_side | two_up | hero_main_side.
Prints the PNG path on the last line.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from chartkit import Kit, load_data  # noqa: E402
import templates  # noqa: E402
import layers  # noqa: E402

LAYOUT_RECTS = {
    "single": ["plot"],
    "hero_top": ["plot_under_hero"],
    "main_side": ["main", "side"],
    "two_up": ["left", "right"],
    "hero_main_side": ["main_under_hero", "side_under_hero"],
}


def render(spec, style=None, preview=None, out_root=None):
    kit = Kit(style or spec.get("style", "dark"))
    layout = spec.get("layout", "single")
    panels = spec.get("panels", [])
    if layout not in LAYOUT_RECTS:
        raise ValueError(f"unknown layout: {layout}")
    if len(panels) > kit.s["max_panels"]:
        raise ValueError(f"style {kit.name} allows at most {kit.s['max_panels']} panels, spec has {len(panels)}")
    if len(panels) != len(LAYOUT_RECTS[layout]):
        raise ValueError(f"layout {layout} needs {len(LAYOUT_RECTS[layout])} panels, spec has {len(panels)}")
    data, asof = load_data(spec)
    fig = kit.figure(spec.get("frame", "16x9"))
    kit.plan_text(spec["title"], spec.get("subtitle", ""))
    if spec.get("legend", True) is False:
        kit.shift -= 0.05          # no legend: pull the plot area up to avoid a gap
    ctx = {"fig": fig, "spec": spec, "asof": asof}
    legend = []
    for panel, which in zip(panels, LAYOUT_RECTS[layout]):
        if panel.get("custom"):
            # custom script: module with draw(ax, panel, data, kit, ctx), still goes through frame/save/review
            import importlib.util
            p = Path(panel["custom"])
            p = p if p.is_absolute() else (kit_root() / p)
            sp = importlib.util.spec_from_file_location("custom_panel", p)
            mod = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(mod)
            tpl = mod
        else:
            tpl = templates.get(panel["template"])
        ax = kit.axes(fig, which)
        if not getattr(tpl, "YTICKS", True):
            # template has no numeric y tick labels: give back ytick_pad so the plot starts at the safe area
            x0, y0, w, h = ax.get_position().bounds
            pad = kit.lay.get("ytick_pad", 0.045)
            if which not in ("side", "side_under_hero"):
                ax.set_position([x0 - pad, y0, w + pad, h])
        res = tpl.draw(ax, panel, data, kit, ctx) or {}
        layers.apply(ax, panel, data, kit, res)
        if panel.get("title"):
            x0, y0, w, h = ax.get_position().bounds
            if getattr(tpl, "YTICKS", True):
                x0 -= kit.lay.get("ytick_pad", 0.045)
            fig.text(x0, y0 + h + 0.015, panel["title"], fontsize=kit.t["label"], fontfamily=kit.body,
                     fontweight=600, color=kit.c["muted"], ha="left", va="baseline")
        if panel.get("legend", True):
            for item in res.get("legend", []):
                if item not in legend:
                    legend.append(item)
    if spec.get("hero"):
        kit.hero(fig, spec["hero"], rect=kit.rect("hero_row") if layout in ("hero_top", "hero_main_side") else None)
    if spec.get("legend", True):
        kit.legend(fig, legend)
    kit.frame(fig, spec["title"], spec.get("subtitle", ""), spec.get("source", ""),
              handle=spec.get("handle", True), asof=spec.get("asof_in_source", True) and asof)
    fin = spec.get("final", {})
    return kit.save(fig, spec["slug"], n=fin.get("n", 1), desc=fin.get("desc", "chart"),
                    out_root=out_root, preview=preview)


def kit_root():
    from chartkit import HOME
    return HOME


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--style")
    ap.add_argument("--preview", help="only save a PNG to this path, do not write outputs/")
    ap.add_argument("--out", help="alternative outputs root")
    a = ap.parse_args()
    with open(a.spec) as f:
        spec = json.load(f)
    png, svg = render(spec, a.style, a.preview, a.out)
    if svg:
        print(svg)
    print(png)


if __name__ == "__main__":
    main()
