# claude-statusline

A Claude Code plugin that renders a one-line status bar at the bottom of every session.

```
⎇ main  │  ████████░░░░░░░░  45%  90k/200k  │  ↑1.7k ↓35k  │  Sonnet 4.6  │  ⏱ 42m
```

The bar is colour-coded by context usage:

| Usage    | Colour |
|----------|--------|
| 0 – 59%  | Green  |
| 60 – 84% | Amber  |
| 85%+     | Red    |

## Requirements

- Python 3.8+
- Claude Code

## Installation

Install via the [sameera207 plugin marketplace](https://github.com/sameera207/claude-plugins#installation).

Inside Claude Code:

```
/plugin marketplace add sameera207/claude-plugins
/plugin install claude-statusline@sameera207
```

The plugin auto-configures itself on first run — no manual settings edits needed.

## What each segment shows

| Segment | Source |
|---------|--------|
| `⎇ main` | Current git branch (`git branch --show-current`) |
| `████████░░░░░░░░  45%  90k/200k` | Context window usage — 16-char bar, percentage, effective tokens / window size |
| `↑1.7k ↓35k` | Session-total billed input (↑) and output (↓) tokens |
| `Sonnet 4.6` | Active model (`claude-` prefix stripped) |
| `⏱ 42m` | Elapsed session time |

Token counts are formatted as `1.7k` / `35k` / `1.5M` depending on magnitude.

## How it works

Claude Code pipes a JSON payload to the `statusLine` command on every UI tick. `statusline.py` reads that payload from stdin, extracts the relevant fields, and writes the formatted status line to stdout. The script is purely Python stdlib — no third-party dependencies.

```
Claude Code  →  (JSON on stdin)  →  statusline.py  →  (one-line string on stdout)  →  status bar
```

The script is designed to exit in under 100 ms and never crash. Any error produces a safe fallback line rather than breaking the session.

## Development

Run the test suite:

```bash
python3 -m pytest tests/ -v
```

## Licence

MIT
