#!/usr/bin/env python3
"""Generate the synthetic data files used by examples/specs/*.json.

Everything here is made up with a seeded RNG: names are generic ("Chain A", "Token X", "Venue A")
and the numbers do not describe any real market. Re-running gives identical files.

    python3 examples/make_data.py          # writes examples/data/*.json
"""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "data"
ASOF = "2025-06-30"


def days(start, n):
    d0 = date.fromisoformat(start)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w") as fh:
        json.dump(obj, fh, indent=1)
    print(OUT / name)


def chain_metrics(rng):
    """Daily chain TVL, 7d DEX volume and meme token market cap. Memes peak on day 36, the chain keeps growing."""
    n, peak = 81, 36
    t = np.arange(n)
    tvl = 400e6 * np.exp(0.013 * t) * (1 + rng.normal(0, 0.012, n))
    dex7 = 250e6 * (1 + 0.9 * np.tanh(t / 40)) * (1 + 0.25 * np.exp(-((t - peak) / 8) ** 2)) * (1 + rng.normal(0, 0.03, n))
    memes = np.where(t <= peak, 60e6 * np.exp(0.065 * t), 60e6 * np.exp(0.065 * peak) * np.exp(-0.03 * (t - peak)))
    memes = memes * (1 + rng.normal(0, 0.04, n))
    rows = [{"d": d, "tvl": round(a), "dex7": round(b), "memes": round(c)} for d, a, b, c in zip(days("2025-04-01", n), tvl, dex7, memes)]
    write("chain_metrics.json", {"asof": "2025-06-20", "peak": rows[peak]["d"], "chain": rows})


def hourly_mcap(rng):
    """Hourly market cap of Token X over 26 hours, with a jump after an event at hour 5."""
    t0 = int(datetime(2025, 6, 14, 0, 0, tzinfo=timezone.utc).timestamp())
    mc = [350e3 * (1 + rng.normal(0, 0.03)) for _ in range(5)]
    for h in range(5, 26):
        target = 4.6e6 if h < 12 else 3.6e6
        mc.append(mc[-1] + (target - mc[-1]) * 0.45 + rng.normal(0, 120e3))
    rows = [{"t": t0 + 3600 * h, "mc": round(v)} for h, v in enumerate(mc)]
    write("hourly_mcap.json", {"asof": "2025-06-15 02:00 UTC", "event_t": t0 + 5 * 3600 + 11 * 60, "token": rows})


def volume_mix(rng):
    """35 days of daily volume: spot shrinks, two perp venues grow, the total stays roughly flat."""
    n = 35
    t = np.arange(n) / (n - 1)
    wk = 1 + 0.12 * np.cos((np.arange(n) - 5) * 2 * np.pi / 7)    # weekly rhythm, peaks on Sundays
    spot = 1.55e9 * (1 - 0.40 * t) * wk * (1 + rng.normal(0, 0.03, n))
    perp_a = 0.45e9 * (1 + 0.60 * t) * wk * (1 + rng.normal(0, 0.08, n))
    perp_b = 0.08e9 * (1 + 3.60 * t) * wk * (1 + rng.normal(0, 0.10, n))
    perp_b[[9, 10]] *= 2.6                                            # two promo days on Venue B
    rows = [{"d": d, "spot": round(s), "perp_a": round(a), "perp_b": round(b)}
            for d, s, a, b in zip(days("2025-05-27", n), spot, perp_a, perp_b)]
    last30 = rows[-30:]
    tot = sum(r["spot"] + r["perp_a"] + r["perp_b"] for r in last30)
    share = {"perps": sum(r["perp_a"] + r["perp_b"] for r in last30) / tot}
    write("volume_mix.json", {"asof": ASOF, "share_30d": share, "rows": rows})


def token_multiples(rng):
    """Value / yearly holder payout for 8 tokens. Two of the four highlighted ones have no payout (None)."""
    syms = ["Token A", "Token B", "Token C", "Token D", "Token E", "Token F", "Token G", "Token H"]
    mult = [3.2, 13.8, None, None, 22.5, 19.4, 11.6, 8.1]
    rows = [{"sym": s, "pick": i < 4, "multiple": m} for i, (s, m) in enumerate(zip(syms, mult))]
    write("token_multiples.json", {"asof": ASOF, "rows": rows})


def pool_returns(rng):
    """Per $10K in each pool over 30 days: fees earned (+) and price move plus IL (-)."""
    names = ["Pool 1", "Pool 2", "Pool 3", "Pool 4", "Pool 5", "Pool 6"]
    fees = rng.uniform(350, 990, len(names)).round()
    loss = -np.array([5, 260, 430, 4, 290, 9]) * rng.uniform(0.9, 1.1, len(names))
    pools = {f"p{i + 1}": {"label": n, "fees": float(f), "loss": float(round(l))} for i, (n, f, l) in enumerate(zip(names, fees, loss))}
    write("pool_returns.json", {"asof": ASOF, "pools": pools})


def holder_split(rng):
    """Share of a 1B supply by holder group."""
    write("holder_split.json", {"asof": ASOF, "supply": 1_000_000_000,
                                "split": {"fresh": 0.141, "pool": 0.122, "early": 0.057, "burned": 0.034},
                                "fresh_wallets": 31, "early_wallets": 74})


def tvl_by_age(rng):
    """TVL by day since launch for four chains, as [day, value] pairs, first 112 days."""
    d = np.arange(1, 113)

    def curve(scale, k, mid, noise, jumps=()):
        y = scale / (1 + np.exp(-k * (d - mid)))
        for day, size in jumps:                                       # one-off inflows that stay
            y = y + np.where(d >= day, size, 0)
        return [[int(a), round(float(b))] for a, b in zip(d, y * (1 + rng.normal(0, noise, len(d))))]

    ser = {
        "chain_a": curve(0.92e9, 0.08, 40, 0.008, jumps=((18, 80e6), (33, 70e6), (46, 75e6))),
        "chain_b": curve(0.30e9, 0.05, 70, 0.02),
        "chain_c": curve(0.55e9, 0.25, 6, 0.02),
        "chain_d": curve(0.20e9, 0.10, 30, 0.03),
    }
    # chain_c fades after its points program ends
    ser["chain_c"] = [[a, round(b * (1 - 0.6 * max(0, a - 60) / 52))] for a, b in ser["chain_c"]]
    write("tvl_by_age.json", {"asof": "2025-06-01", "latest": {"asof": "2025-06-30 12:00 UTC"}, "series": ser})


def lock_split(rng):
    """Locked supply split and weekly payouts to stakers. Hero numbers in the spec are derived from these."""
    price = 0.15
    split = {"burned": 250e6, "treasury": 280e6, "other": 12e6, "staked": 58e6}
    weekly = [{"label": "2 Jun", "value": 180e3}, {"label": "9 Jun", "value": 150e3},
              {"label": "16 Jun*", "value": 95e3}, {"label": "23 Jun", "value": 110e3}]
    annual = weekly[-1]["value"] * 52
    derived = {
        "apr_staked": annual / (split["staked"] * price),
        "apr_if_treasury_stakes": annual / ((split["staked"] + split["treasury"]) * price),
        "apr_all_locked": annual / (sum(split.values()) * price),
    }
    write("lock_split.json", {"asof": ASOF, "price": price, "split": split, "weekly": weekly, "derived": derived})


def venue_apr(rng):
    """7-day APR of the same asset pair on Venue A vs Venue B. One pair has no Venue B pool."""
    labels = ["Asset 1", "Asset 2", "Asset 3", "Asset 4", "Asset 5"]
    a = [0.184, 0.092, 0.131, 0.047, 0.215]
    b = [0.121, 0.104, 0.069, 0.031, None]
    rows = [{"label": l, "a_apr_7d": x, "b_apr_7d": y} for l, x, y in zip(labels, a, b)]
    ahead = sum(1 for x, y in zip(a, b) if y is not None and x > y)
    write("venue_apr.json", {"asof": ASOF, "compare": rows, "summary": {"ahead": ahead, "paired": sum(y is not None for y in b)}})


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    for fn in (chain_metrics, hourly_mcap, volume_mix, token_multiples, pool_returns, holder_split, tvl_by_age,
               lock_split, venue_apr):
        fn(rng)
