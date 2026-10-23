#!/usr/bin/env python3
"""
x-insights trends: what is an X community talking about, scanned by account tier.

Reads a profile (profiles/<name>.json) and calls twitter-cli:
  - core + projects: user-posts of every account (read everything, even posts without numbers)
  - community: "from:a OR from:b ..." searches in groups of 5
  - keyword queries -> "outside" posts, kept only when they are really about the community's topic
  - quote chains: when a kept post quotes another post, the quoted post is attached and grouped,
    because conversations often spread through quotes of a root post that never names the topic
No filtering on numbers: every post carries has_numbers, tier, lift (views / the author's 14-day median).
Topic regexes are only hints for whoever reads the output (you, or a model).

Run:
  python3 trends.py --profile mychain --hours 24            # markdown
  python3 trends.py --profile mychain --hours 24 --json     # JSON
  python3 trends.py --profile mychain --from-file f.json    # reuse saved tweets, no X calls
  python3 trends.py --profile mychain --expand-quotes 10    # also fetch the 10 most-quoted roots (views, text)
Env: TWITTER_BIN, TWITTER_CHROME_PROFILE (which logged-in Chrome profile twitter-cli reads cookies from),
INSIGHTS_HOME (workspace, default ./insights; scans go to $INSIGHTS_HOME/scans).
Standard library only.
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TW = os.environ.get("TWITTER_BIN") or str(Path.home() / ".local/bin/twitter")
TICK = re.compile(r"\$([A-Z][A-Z0-9]{1,11})\b")
NUM = re.compile(r"(\$\s?\d[\d,.]*\s?[kKmMbB]?)|(\d[\d,.]*\s?%)|(\d[\d,.]*\s?[xX]\b)|(\d[\d,.]*\s?(k|K|M|B)\b)")
TIERS = ("core", "projects", "community", "outside")
ADDR = re.compile(r"(?:[a-z]+:)?(0x[0-9a-fA-F]{40})")


def addr_map(profile):
    """Contract address -> ticker. People often paste 'chain:0x18e6...' instead of $TICKER; without this
    the ticker counts miss them. Optional profile key "address_book": a JSON file {address: symbol}."""
    f = profile.get("address_book")
    if not f:
        return {}
    try:
        return {a.lower(): s.upper() for a, s in json.loads(Path(f).expanduser().read_text()).items()}
    except Exception:  # noqa: BLE001
        return {}


def resolve_addrs(txt, amap):
    def sub(m):
        a = m.group(1).lower()
        return f"${amap[a]} ({a[:6]}…)" if a in amap else m.group(0)
    return ADDR.sub(sub, txt) if amap else txt


def out_dir():
    d = Path(os.environ.get("INSIGHTS_HOME", "insights")).expanduser() / "scans"
    d.mkdir(parents=True, exist_ok=True)
    return d


def tw(args, n, timeout=120):
    """Call twitter-cli, return a list. On error return [] and log to stderr (one failure must not kill the scan)."""
    err = None
    for i in range(3):
        try:
            r = subprocess.run([TW, *args, "-n", str(n), "--json"], capture_output=True, text=True,
                               timeout=timeout, env=os.environ)
            d = json.loads(r.stdout)
            if isinstance(d, dict) and d.get("ok") is False:
                raise RuntimeError(str(d.get("error"))[:120])
            items = d.get("data", d) if isinstance(d, dict) else d
            return items if isinstance(items, list) else []
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(8 * (i + 1))
    print(f"twitter {' '.join(args)[:50]}: {err}", file=sys.stderr)
    return []


def parse_ts(t):
    for k in ("createdAtISO", "createdAt"):
        v = t.get(k)
        if not v:
            continue
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00")) if k == "createdAtISO" else parsedate_to_datetime(v)
        except Exception:  # noqa: BLE001
            continue
    return None


def collect(profile, hours):
    """Return a list of tweets, each tagged with 'tier'."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d")
    tiers = profile.get("tiers") or {"community": profile["accounts"]}
    seen = {}

    def add(items, tier, expect=None):
        for t in items:
            if not isinstance(t, dict) or not t.get("id"):
                continue
            a = ((t.get("author") or {}).get("screenName") or "").lower()
            if expect and a != expect.lower():
                continue  # twitter-cli can return another account when a handle is broken
            if t["id"] not in seen:
                t["tier"] = tier
                seen[t["id"]] = t

    # core + projects: read everything. Rotate the start by day so rate limits (429) never always hit the same account
    full = [(a, "core") for a in tiers.get("core", [])] + [(a, "projects") for a in tiers.get("projects", [])]
    if full:
        k = datetime.now().timetuple().tm_yday % len(full)
        full = full[k:] + full[:k]
    for a, tier in full:
        add(tw(["user-posts", a], 20), tier, expect=a)
        time.sleep(2.5)
    comm = tiers.get("community", [])
    for i in range(0, len(comm), 5):  # groups of 5, 100 results: larger groups let prolific posters crowd out the rest
        q = " OR ".join(f"from:{a}" for a in comm[i:i + 5])
        add(tw(["search", f"{q} since:{since}", "--type", "latest"], 100), "community")
        time.sleep(1.5)
    for q in profile["queries"]:
        add(tw(["search", f"{q} since:{since}", "--type", "latest"], 60), "outside")
        time.sleep(1.5)
    return list(seen.values())


def update_author_views(tweets, days=14):
    """author_views.json: {author: [[ts, views, id], ...]} over 14 days, for lift = views / the author's own median."""
    p = out_dir() / "author_views.json"
    try:
        store = json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        store = {}
    cut = time.time() - days * 86400
    ids = {}
    for t in tweets:
        a = ((t.get("author") or {}).get("screenName") or "?")
        ts = parse_ts(t)
        v = (t.get("metrics") or {}).get("views") or 0
        if (t.get("text") or "").startswith("@"):
            continue  # replies get few views, keep them out of the baseline
        if ts and v:
            ids.setdefault(a, {})[t["id"]] = [int(ts.timestamp()), v]
    for a, m in ids.items():
        cur = {str(x[2]) if len(x) > 2 else f"{x[0]}": x for x in store.get(a, [])}
        for tid, (ts, v) in m.items():
            cur[tid] = [ts, v, tid]
        store[a] = [x for x in cur.values() if x[0] > cut][-300:]
    p.write_text(json.dumps(store))
    med = {}
    for a, rows in store.items():
        vals = [x[1] for x in rows if x[1] > 0]
        if len(vals) >= 8:  # with fewer posts lift is meaningless (first days show 20-80x)
            med[a] = statistics.median(vals)
    return med


HANDLE = re.compile(r"@([A-Za-z0-9_]{2,15})")


def emerging_handles(profile, tweets, cutoff, min_authors=3):
    """Emerging names: an @handle mentioned by >= 3 different authors in the window and not yet in the profile.
    Catches new projects the filter does not know yet (one real case: 19 posts about a new project, none passed
    the filter because its name was not in it)."""
    tiers = profile.get("tiers") or {}
    # skip core, community, dropped and recap bots. Projects are NOT skipped: a project that posts little but is
    # mentioned a lot still needs to surface
    known = {a.lower() for k in ("core", "community") for a in tiers.get(k, [])}
    known |= {a.lower() for a in profile.get("dropped", [])}
    known |= {a.lower() for a in profile.get("recap_accounts", [])}
    projects = {a.lower() for a in tiers.get("projects", [])}
    seen = {}
    for t in tweets:
        txt = t.get("text") or ""
        if txt.startswith("RT @") or t.get("isRetweet") or txt.startswith("@"):
            continue
        ts = parse_ts(t)
        if not ts or ts < cutoff:
            continue
        a = ((t.get("author") or {}).get("screenName") or "?").lower()
        for h in set(m.lower() for m in HANDLE.findall(txt)):
            if h in known or h == a:
                continue
            e = seen.setdefault(h, {"authors": set(), "posts": 0})
            e["authors"].add(a)
            e["posts"] += 1
    return {h: {**e, "project": h in projects} for h, e in seen.items() if len(e["authors"]) >= min_authors}


def quoted_of(t):
    """The quoted post, if any: {id, author, text}. twitter-cli includes it without views or time."""
    q = t.get("quotedTweet")
    if not isinstance(q, dict) or not q.get("id"):
        return None
    return {"id": q["id"], "author": (q.get("author") or {}).get("screenName") or "?",
            "text": (q.get("text") or "").replace("\n", " ")[:400]}


def quote_chains(posts, expand=0):
    """Group kept posts by the post they quote. A root quoted by kept posts is part of the conversation even when
    its own text never names the topic (a bare link, a nickname the filter does not know). expand=N fetches the N
    most-quoted roots with `twitter tweet` to get their views and to follow one more hop up."""
    roots = {}
    for p in posts:
        q = p.get("quoted")
        if not q:
            continue
        r = roots.setdefault(q["id"], {**q, "quoted_by": [], "views": None, "parent": None})
        r["quoted_by"].append({"id": p["id"], "author": p["author"], "views": p["views"]})
    ranked = sorted(roots.values(), key=lambda r: (-len(r["quoted_by"]), -sum(x["views"] for x in r["quoted_by"])))
    for r in ranked[:expand]:
        got = tw(["tweet", r["id"]], 1)
        main = next((t for t in got if isinstance(t, dict) and t.get("id") == r["id"]), None)
        if main:
            r["views"] = (main.get("metrics") or {}).get("views")
            r["parent"] = quoted_of(main)
        time.sleep(2)
    known = {p["id"] for p in posts}
    return [{**r, "in_scan": r["id"] in known} for r in ranked]


def on_topic(txt, flt):
    """An 'outside' post must really be about the topic: two filter hits, or one in the first 120 characters."""
    hits = flt.findall(txt)
    return len(hits) >= 2 or bool(flt.search(txt[:120]))


def analyze(profile, tweets, hours, expand=0):
    flt = re.compile(profile["filter"], re.I)
    cats = [(c, re.compile(rx, re.I)) for c, rx in profile["categories"]]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    med = update_author_views(tweets)
    amap = addr_map(profile)
    emerging = emerging_handles(profile, tweets, cutoff)
    posts = []
    for t in tweets:
        txt = resolve_addrs((t.get("text") or "").replace("\n", " "), amap)
        if txt.startswith("RT @") or t.get("isRetweet") or txt.startswith("@"):
            continue  # skip retweets and replies
        ts = parse_ts(t)
        if not ts or ts < cutoff:
            continue
        tier = t.get("tier", "community")
        mentions = sorted(h for h in set(m.lower() for m in HANDLE.findall(txt)) if h in emerging)
        if tier == "community" and not flt.search(txt) and not mentions:
            continue  # community posts must hit the filter, or mention an emerging name
        if tier == "outside" and not (on_topic(txt, flt) or (mentions and flt.search(txt))):
            continue  # outside: really on topic; a post naming an emerging name needs only one filter hit
        a = (t.get("author") or {}).get("screenName") or "?"
        views = (t.get("metrics") or {}).get("views") or 0
        labels = [c for c, rx in cats if rx.search(txt)] or ["other"]
        posts.append({"id": t["id"], "author": a, "tier": tier, "views": views, "likes": (t.get("metrics") or {}).get("likes") or 0,
                      "time": ts.isoformat(), "labels": labels, "tickers": sorted(set(TICK.findall(txt))),
                      "has_numbers": len(NUM.findall(txt)) >= 2, "on_topic": bool(flt.search(txt)), "mentions": mentions,
                      "quoted": quoted_of(t),
                      "lift": round(views / med[a], 2) if a in med and views else None,
                      "text": txt[:600], "url": f"https://x.com/{a}/status/{t['id']}"})
    # topics by regex: hints only
    topics = {}
    for p in posts:
        if not p["has_numbers"]:
            continue
        c = p["labels"][0]
        tp = topics.setdefault(c, {"topic": c, "posts": 0, "views": 0, "authors": set(), "top": []})
        tp["posts"] += 1
        tp["views"] += p["views"]
        tp["authors"].add(p["author"])
        tp["top"].append(p)
    out = []
    for tp in topics.values():
        tp["top"] = sorted(tp["top"], key=lambda p: -(p["lift"] or 0) * 1000 - p["views"])[:3]
        tp["authors"] = len(tp["authors"])
        tp["data"] = profile["data_map"].get(tp["topic"])
        out.append(tp)
    out.sort(key=lambda tp: -(tp["views"] * min(tp["authors"], 5) / 5))
    tick = {}
    for p in posts:
        for k in p["tickers"]:
            e = tick.setdefault(k, {"ticker": k, "posts": 0, "views": 0, "authors": set()})
            e["posts"] += 1
            e["views"] += p["views"]
            e["authors"].add(p["author"])
    tickers = sorted(({**e, "authors": len(e["authors"])} for e in tick.values() if len(e["authors"]) >= 2),
                     key=lambda e: -e["views"])[:12]
    by_tier = {k: sum(1 for p in posts if p["tier"] == k) for k in TIERS}
    emerg_out = []
    for h, e in emerging.items():
        ps = [p for p in posts if h in p["mentions"]]
        emerg_out.append({"handle": h, "posts": len(ps), "authors": len(e["authors"]), "tweets": e["posts"], "project": e["project"],
                          "views": sum(p["views"] for p in ps), "top": [p["id"] for p in sorted(ps, key=lambda p: -p["views"])[:4]]})
    emerg_out.sort(key=lambda e: (-e["authors"], -e["views"]))
    return {"tickers": tickers, "profile": profile["name"], "hours": hours, "generated": datetime.now(timezone.utc).isoformat(),
            "tweets": len(tweets), "posts": len(posts), "by_tier": by_tier, "emerging": emerg_out,
            "data_posts": sum(1 for p in posts if p["has_numbers"]), "topics": out,
            "quote_chains": quote_chains(posts, expand),
            "items": sorted(posts, key=lambda p: (TIERS.index(p["tier"]), -(p["lift"] or 0), -p["views"]))}


def to_md(res):
    t = res["by_tier"]
    lines = [f"# x-insights {res['profile']}: {res['hours']}h, {res['tweets']} posts scanned, {res['posts']} on topic "
             f"(core {t['core']}, projects {t['projects']}, community {t['community']}, outside {t['outside']}), "
             f"{res['data_posts']} with numbers", ""]
    if res.get("tickers"):
        lines.append("Tickers named by >= 2 authors: " + ", ".join(
            f"${e['ticker']} {e['posts']} posts/{e['views']:,} views" for e in res["tickers"]))
        lines.append("")
    if res.get("emerging"):
        lines.append("Emerging names (>= 3 authors, not in profile): " + ", ".join(
            f"@{e['handle']} {e['authors']} authors" for e in res["emerging"][:8]))
        lines.append("")
    for tier, title in (("core", "Core"), ("projects", "Projects")):
        items = [p for p in res["items"] if p["tier"] == tier]
        if items:
            lines.append(f"## {title}: {len(items)} posts")
            for p in items[:15]:
                lines.append(f"- @{p['author']} {p['views']:,} views: {p['text'][:160]} {p['url']}")
            lines.append("")
    lines.append("## Community + outside, by lift")
    for p in [p for p in res["items"] if p["tier"] in ("community", "outside")][:25]:
        lift = f", {p['lift']}x their usual" if p.get("lift") else ""
        tag = " [outside]" if p["tier"] == "outside" else ""
        lines.append(f"- @{p['author']}{tag} {p['views']:,} views{lift}: {p['text'][:160]} {p['url']}")
    lines.append("")
    chains = [c for c in res.get("quote_chains", []) if len(c["quoted_by"]) >= 2 or not c["in_scan"]][:10]
    if chains:
        lines.append("## Quote chains (roots the scan may have missed)")
        for c in chains:
            v = f"{c['views']:,} views, " if c.get("views") else ""
            by = ", ".join(f"@{x['author']}" for x in c["quoted_by"][:4])
            up = f" (itself quotes @{c['parent']['author']})" if c.get("parent") else ""
            lines.append(f"- @{c['author']} {v}quoted by {by}{up}: {c['text'][:140]} https://x.com/{c['author']}/status/{c['id']}")
        lines.append("")
    lines.append("## Topics by regex (hints)")
    for i, tp in enumerate(res["topics"], 1):
        lines.append(f"{i}. {tp['topic']}: {tp['posts']} posts, {tp['authors']} authors, {tp['views']:,} views")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, help="name of profiles/<name>.json, or a path to a profile JSON")
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--from-file", help="reuse a saved tweets JSON, no X calls")
    ap.add_argument("--expand-quotes", type=int, default=0, help="fetch the N most-quoted roots (one call each)")
    args = ap.parse_args()
    pp = Path(args.profile)
    pp = pp if pp.suffix == ".json" else SKILL / "profiles" / f"{args.profile}.json"
    profile = json.loads(pp.read_text())
    tweets = json.loads(Path(args.from_file).read_text()) if args.from_file else collect(profile, args.hours)
    res = analyze(profile, tweets, args.hours, args.expand_quotes)
    stamp = datetime.now().strftime("%Y-%m-%d")
    name = profile["name"]
    (out_dir() / f"{name}-{stamp}-tweets.json").write_text(json.dumps(tweets))
    (out_dir() / f"{name}-{stamp}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False) if args.json else to_md(res))


if __name__ == "__main__":
    main()
