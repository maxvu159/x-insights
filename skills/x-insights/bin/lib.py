#!/usr/bin/env python3
"""
Small shared helpers for per-angle fetch scripts: HTTP JSON with retries, JSON-RPC, log scans, ERC-20 reads.
Copy into $INSIGHTS_HOME/scripts/ or import from here. Standard library only.

    from lib import http_json, rpc, get_logs, balance_of, erc20_meta
    RPC = "https://rpc.example.org"
    tvl = http_json("https://api.llama.fi/v2/historicalChainTvl/Base")
    logs = get_logs(RPC, token, [TRANSFER], 1_000_000, 1_200_000)
"""

import json
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 x-insights", "Content-Type": "application/json"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def http_json(url, body=None, tries=4, timeout=30):
    """GET (or POST when body is given) and parse JSON. Backs off on 429 and 5xx."""
    for i in range(tries):
        try:
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa: BLE001
            code = getattr(e, "code", None)
            if i == tries - 1 or (code and code < 500 and code != 429):
                raise
            time.sleep(30 if code == 429 else 5 * (i + 1))


def rpc(url, method, params):
    r = http_json(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]


def get_logs(url, address, topics, start, end, step=50_000):
    """eth_getLogs over [start, end], in chunks; halves a chunk when the node refuses it (too many results)."""
    out, a = [], start
    while a <= end:
        b = min(a + step - 1, end)
        try:
            out += rpc(url, "eth_getLogs", [{"address": address, "topics": topics,
                                             "fromBlock": hex(a), "toBlock": hex(b)}])
            a = b + 1
        except RuntimeError:
            if step <= 100:
                raise
            step //= 2
    return out


def call(url, to, data, block="latest"):
    return rpc(url, "eth_call", [{"to": to, "data": data}, block])


def balance_of(url, token, holder, block="latest"):
    return int(call(url, token, "0x70a08231" + holder.lower().replace("0x", "").rjust(64, "0"), block), 16)


def erc20_meta(url, token):
    """(symbol, decimals). symbol falls back to '?' for non-standard tokens."""
    dec = int(call(url, token, "0x313ce567"), 16)
    try:
        raw = bytes.fromhex(call(url, token, "0x95d89b41")[2:])
        n = int.from_bytes(raw[32:64], "big")
        sym = raw[64:64 + n].decode(errors="ignore") or "?"
    except Exception:  # noqa: BLE001
        sym = "?"
    return sym, dec
