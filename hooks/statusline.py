#!/usr/bin/env python3
"""
Claude Code statusline plugin.

Renders a one-line status bar:
  ⎇ main  │  ████████░░░░░░░░  45%  136k/200k  │  claude-sonnet-4-6  │  ⏱ 42m

Reads JSON from stdin on every tick; never crashes — errors are suppressed.
Stdlib only, no third-party dependencies.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone


# ── ANSI colours ────────────────────────────────────────────────────────────

GREEN  = "\033[32m"
AMBER  = "\033[33m"
RED    = "\033[31m"
RESET  = "\033[0m"


def colour_for(pct: float) -> str:
    if pct >= 85:
        return RED
    if pct >= 60:
        return AMBER
    return GREEN


# ── Token formatting ─────────────────────────────────────────────────────────

def fmt_tokens(n: int) -> str:
    """Format a token count as e.g. '136k' or '1M'."""
    if n >= 1_000_000:
        val = n / 1_000_000
        if val == int(val):
            return f"{int(val)}M"
        return f"{val:.1f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        val = n / 1_000
        if val == int(val):
            return f"{int(val)}k"
        return f"{val:.1f}k".rstrip("0").rstrip(".")
    return str(n)


# ── Progress bar ─────────────────────────────────────────────────────────────

BAR_WIDTH = 16

def progress_bar(pct: float) -> str:
    filled = round(BAR_WIDTH * pct / 100)
    filled = max(0, min(BAR_WIDTH, filled))
    empty  = BAR_WIDTH - filled
    return "█" * filled + "░" * empty


# ── Session time ─────────────────────────────────────────────────────────────

def fmt_elapsed(started_at: str) -> str:
    """Return '⏱ 42m' or '⏱ 1h 24m' from an ISO-8601 timestamp."""
    try:
        # Accept both Z-suffix and +00:00 formats
        started_at = started_at.replace("Z", "+00:00")
        start = datetime.fromisoformat(started_at)
        now   = datetime.now(timezone.utc)
        total_secs = max(0, int((now - start).total_seconds()))
        minutes = total_secs // 60
        hours   = minutes // 60
        mins    = minutes % 60
        if hours > 0:
            return f"⏱ {hours}h {mins}m"
        return f"⏱ {minutes}m"
    except Exception:
        return "⏱ --"


# ── Git branch ────────────────────────────────────────────────────────────────

def git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        branch = result.stdout.strip()
        return branch if branch else "HEAD"
    except Exception:
        return ""


# ── Model name ────────────────────────────────────────────────────────────────

def fmt_model(display_name: str) -> str:
    """Strip leading 'claude-' prefix for display."""
    name = display_name.strip()
    if name.lower().startswith("claude-"):
        name = name[len("claude-"):]
    return name


# ── Main ──────────────────────────────────────────────────────────────────────

def render(data: dict) -> str:
    # ── git branch ──────────────────────────────────────────────────────────
    branch = git_branch()
    branch_segment = f"⎇ {branch}  " if branch else ""

    # ── context window ───────────────────────────────────────────────────────
    ctx = data.get("context_window") or {}
    usage = data.get("current_usage") or {}

    # used_percentage is the authoritative source; fall back to calculating
    pct_raw = ctx.get("used_percentage")
    if pct_raw is None:
        used   = usage.get("input_tokens", 0) or 0
        limit  = ctx.get("context_window_size") or 0
        pct_raw = (used / limit * 100) if limit else 0

    pct   = float(pct_raw)
    col   = colour_for(pct)
    bar   = progress_bar(pct)

    used_tokens  = usage.get("input_tokens") or ctx.get("used_tokens") or 0
    total_tokens = ctx.get("context_window_size") or 0

    token_label = ""
    if total_tokens:
        token_label = f"  {fmt_tokens(int(used_tokens))}/{fmt_tokens(int(total_tokens))}"

    context_segment = (
        f"{col}{bar}  {pct:.0f}%{token_label}{RESET}"
    )

    # ── model ────────────────────────────────────────────────────────────────
    model_raw  = (data.get("model") or {}).get("display_name", "")
    model_name = fmt_model(model_raw) if model_raw else ""
    model_segment = model_name if model_name else ""

    # ── elapsed time ─────────────────────────────────────────────────────────
    started_at = (data.get("session") or {}).get("started_at", "")
    time_segment = fmt_elapsed(started_at) if started_at else ""

    # ── assemble ─────────────────────────────────────────────────────────────
    parts = []
    if branch_segment:
        parts.append(branch_segment.rstrip())
    parts.append(context_segment)
    if model_segment:
        parts.append(model_segment)
    if time_segment:
        parts.append(time_segment)

    return "  │  ".join(parts)


def main() -> None:
    try:
        raw  = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    try:
        line = render(data)
        sys.stdout.write(line + "\n")
    except Exception:
        # Never crash the session; print a minimal placeholder
        sys.stdout.write("⎇ ?  │  ░░░░░░░░░░░░░░░░  --%\n")


if __name__ == "__main__":
    main()
