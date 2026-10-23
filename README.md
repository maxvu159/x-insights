# x-insights

A Claude Code workflow that turns what a crypto community on X is talking about into **data insight posts**: one
reviewed chart plus a short post with a number the original posters don't have.

```
accounts on X ──► scan (trends.py) ──► angle ──► image brief + data probe ──► locked numbers (data/<slug>.json)
                                                                                 │
           hand over ◄── fact check ◄── chart + independent review ◄── post ◄────┘
           (never auto-posts)            (chart skill)                  (one at a time, ≤ 4 lines)
```

Two skills ship in this plugin:

| Skill | What it does |
|---|---|
| `x-insights` | The 8-step workflow: scan a community by account tier, rank posts by lift, follow quote chains, pick an angle, lock numbers in one snapshot, write the post, review it, hand it over. |
| `chart` | Spec → PNG + SVG renderer with fixed frames, a style file, 10 templates and a reviewer checklist. Writes a JSON spec instead of new matplotlib code each time. |

The value is mostly in the rules: every step carries the lesson of a post that went wrong. See
[`skills/x-insights/reference/rules.md`](skills/x-insights/reference/rules.md).

## Install

```bash
# in Claude Code
/plugin marketplace add maxvu159/x-insights
/plugin install x-insights@x-insights
```

Or copy `skills/x-insights` and `skills/chart` into `~/.claude/skills/` (or a project's `.claude/skills/`).

### Requirements

- Python 3.10+ with `matplotlib` (3.8+) and `numpy` for charts. `trends.py` and `lib.py` use the standard library only.
- [twitter-cli](https://github.com/maxvu159/twitter-cli) for reading X. It reads cookies from a logged-in Chrome
  profile; no API key. Install the fork, which fixes search and supports posts over 280 characters:
  ```bash
  uv tool install "git+https://github.com/maxvu159/twitter-cli@longform-notetweet"
  export TWITTER_BROWSER=chrome TWITTER_CHROME_PROFILE="Default"   # the Chrome profile logged into X
  twitter whoami
  ```
- Font: [Inter](https://rsms.me/inter/) (free, OFL). Without it the charts fall back to DejaVu Sans.

### Environment

| Variable | Default | Meaning |
|---|---|---|
| `INSIGHTS_HOME` | `./insights` | workspace: `scans/`, `scripts/`, `data/`, `specs/`, `outputs/`, `posts/` |
| `INSIGHTS_HANDLE` | style's `handle` | handle printed top right on charts |
| `TWITTER_BIN` | `~/.local/bin/twitter` | twitter-cli binary |
| `TWITTER_CHROME_PROFILE` | | Chrome profile twitter-cli reads cookies from |

## Quickstart

1. **Make a profile.** Copy `skills/x-insights/profiles/_template.json` and `_template.md` to `<name>.json` / `<name>.md`.
   Fill the tiers: `core` (official accounts), `projects` (apps and founders; their numbers are self-reported),
   `community` (30 to 60 accounts that move the conversation). Write the `filter` regex with the community's nicknames.
2. **Write your voice.** Edit `skills/x-insights/reference/voice.md`: stance, sound, two example posts, published list.
3. **Scan.**
   ```bash
   python3 skills/x-insights/bin/trends.py --profile <name> --hours 48
   ```
   Read the top posts, the emerging names and the quote chains. Missing accounts and nicknames show up there; add them.
4. **Run the workflow** in Claude Code: `/x-insights <name>` (or `/x-insights <name> <topic>`). It proposes angles,
   writes the image brief, pulls and locks numbers, writes the post with you one at a time, draws and reviews the chart,
   and saves everything to `insights/posts/DATE-<name>-posts.md`.
5. **Try the chart skill alone:**
   ```bash
   cd skills/chart && python3 bin/render.py examples/specs/stacked_daily.json --preview /tmp/x.png
   ```

## Run it daily (optional, not shipped)

What works in practice: a cron job at a fixed hour runs `trends.py --json`, passes the result plus the profile's
`angle_types` and `stance_rules` to `claude -p` asking for 6 angles (title, stance, what people say with links, one
"bait" number), and sends the message to a Telegram topic. You then pick an angle and run `/x-insights <name> <slug>`
by hand. Keep a log of sent and chosen angles so the next morning avoids repeats, and only returns to a chosen angle
when there is a new number. twitter-cli and `claude -p` need the logged-in desktop session (macOS keychain), so run the
job from a GUI-session scheduler, not over SSH.

## What it will not do

- Post to X. Posting needs `twitter whoami`, the exact text shown to you, and your explicit yes.
- Invent numbers. Every number in a post must be in a data file with an `asof`.

## License

MIT
