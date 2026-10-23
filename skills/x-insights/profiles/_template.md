# Profile: My Chain

Accounts, queries, topics and the data map live in `<name>.json`. This file records where the numbers come from and
the traps you have hit. Keep it short and keep adding traps: every trap here is a wrong post you did not publish.

## Data sources

Fill in your own. These public endpoints cover most EVM chains and need no key:

| Need | Call | Notes |
|---|---|---|
| Chain TVL by day | `https://api.llama.fi/v2/historicalChainTvl/<Chain>` | |
| Protocol TVL on the chain | `https://api.llama.fi/protocol/<slug>` → `chainTvls["<Chain>"]` | skip the `-borrowed` key; lending protocols and their curators can double count |
| DEX volume | `https://api.llama.fi/overview/dexs/<Chain>` | |
| App revenue, holder revenue | `https://api.llama.fi/overview/fees/<Chain>?dataType=dailyAppRevenue` (or `dailyHoldersRevenue`) | `total30d` for 30-day comparisons |
| Price, mcap, history | CoinGecko `coins/markets?ids=`, `coins/<id>/market_chart?days=120&interval=daily` | 429: wait 30 s and retry |
| Pool price and volume | GeckoTerminal `networks/<net>/pools/<addr>/ohlcv/day\|hour?currency=usd` | about 30 calls a minute |
| Find a token | DexScreener `tokens/v1/<chain>/<addrs>`, `latest/dex/search?q=` | |
| On-chain | your chain's public RPC | use `bin/lib.py` (`rpc`, `get_logs`, `balance_of`) |
| Stock prices | Yahoo `query1.finance.yahoo.com/v8/finance/chart/<T>` | |

Addresses you use often (official wallets, main tokens, main pools):
- ...

## Data traps

Generic ones that apply almost everywhere. Add your own below.

- **Copycat tokens with the same ticker:** liquidity close to FDV is a sign of a fake. Always write the real contract.
- **Claims compare different periods:** "A is 12x B" is often one day; over 30 days it may be 6x. Compare the same period before using a number.
- **Unlabelled wallets:** if a wallet is not officially labelled, write "likely" in the post.
- **LP APR:** usually the pool average on current TVL, full range, before gas. Say so in the source line.
- **Daily files keyed by UTC date:** a job that runs at 08:00 local time may hold yesterday's UTC numbers.
- **`eth_getLogs` limits:** many RPCs cap the block range or the result count. Split the range when you hit the cap.
- **Numbers the reader cannot see:** an unlisted market or a one-user vault is not "the rate" of a protocol. Check what the app shows.

Your traps:
- ...
