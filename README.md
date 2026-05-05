# claude-statusline

A Claude Code plugin that renders a one-line status bar at the bottom of every session.

```
⎇ main  │  ████████░░░░░░░░  45%  136k/200k  │  sonnet-4-6  │  ⏱ 42m
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

### 1. Copy the plugin into place

```bash
mkdir -p ~/.claude/plugins/statusline/hooks
cp hooks/statusline.py ~/.claude/plugins/statusline/hooks/statusline.py
chmod +x ~/.claude/plugins/statusline/hooks/statusline.py
```

### 2. Register the status line in `~/.claude/settings.json`

Add the following to your `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/plugins/statusline/hooks/statusline.py"
  }
}
```

If you already have a `settings.json`, merge the `statusLine` key into the existing object.

### 3. Restart Claude Code

Close and reopen any Claude Code sessions to activate the status bar.

## What each segment shows

| Segment | Source |
|---------|--------|
| `⎇ main` | Current git branch (`git branch --show-current`) |
| `████████░░░░░░░░  45%  136k/200k` | Context window usage — 16-char bar, percentage, token counts |
| `sonnet-4-6` | Active model (`claude-` prefix stripped) |
| `⏱ 42m` | Elapsed session time |

Token counts are formatted as `136k` / `200k` / `1.5M` / `1M` depending on magnitude.

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
