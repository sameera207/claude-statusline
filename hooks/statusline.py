#!/usr/bin/env python3
"""
Claude Code statusline plugin.

Renders a one-line status bar:
  ⎇ main  │  ████████░░░░░░░░  39%  78k/200k  │  ↑1.7k ↓35k  │  Sonnet 4.6  │  ⏱ 29m

Reads JSON from stdin on every tick; never crashes — errors are suppressed.
Stdlib only, no third-party dependencies.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


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
    if n >= 1_000_000:
        val = n / 1_000_000
        return f"{val:.1f}M".rstrip("0").rstrip(".")
    if n >= 1_000:
        val = n / 1_000
        return f"{val:.1f}k".rstrip("0").rstrip(".")
    return str(n)


# ── Progress bar ─────────────────────────────────────────────────────────────

BAR_WIDTH = 16

def progress_bar(pct: float) -> str:
    filled = round(BAR_WIDTH * pct / 100)
    filled = max(0, min(BAR_WIDTH, filled))
    return "█" * filled + "░" * (BAR_WIDTH - filled)


# ── Session time ─────────────────────────────────────────────────────────────

def fmt_duration_ms(ms: float) -> str:
    total_secs = max(0, int(ms / 1000))
    minutes    = total_secs // 60
    hours      = minutes // 60
    mins       = minutes % 60
    if hours > 0:
        return f"⏱ {hours}h {mins}m"
    return f"⏱ {minutes}m"


# ── Git branch ────────────────────────────────────────────────────────────────

def git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=1,
        )
        branch = result.stdout.strip()
        return branch if branch else "HEAD"
    except Exception:
        return ""


# ── Model name ────────────────────────────────────────────────────────────────

def fmt_model(display_name: str) -> str:
    name = display_name.strip()
    if name.lower().startswith("claude-"):
        name = name[len("claude-"):]
    return name


# ── Main ──────────────────────────────────────────────────────────────────────

def render(data: dict) -> str:
    # git branch
    branch = git_branch()
    branch_segment = f"⎇ {branch}" if branch else ""

    # context window — current_usage is nested inside context_window
    ctx   = data.get("context_window") or {}
    usage = ctx.get("current_usage") or {}

    pct_raw = ctx.get("used_percentage")
    if pct_raw is None:
        effective = (
            usage.get("input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
        )
        limit   = ctx.get("context_window_size") or 0
        pct_raw = (effective / limit * 100) if limit else 0

    pct = float(pct_raw)
    col = colour_for(pct)
    bar = progress_bar(pct)

    # effective context used (all input types combined)
    ctx_used = (
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
    ctx_total = ctx.get("context_window_size") or 0

    ctx_label = ""
    if ctx_total:
        ctx_label = f"  {fmt_tokens(int(ctx_used))}/{fmt_tokens(int(ctx_total))}"

    context_segment = f"{col}{bar}  {pct:.0f}%{ctx_label}{RESET}"

    # session-total input/output tokens (for cost awareness)
    total_in  = ctx.get("total_input_tokens", 0)
    total_out = ctx.get("total_output_tokens", 0)
    io_segment = ""
    if total_in or total_out:
        io_segment = f"↑{fmt_tokens(int(total_in))} ↓{fmt_tokens(int(total_out))}"

    # model
    model_raw  = (data.get("model") or {}).get("display_name", "")
    model_segment = fmt_model(model_raw) if model_raw else ""

    # session time from cost.total_duration_ms
    duration_ms = (data.get("cost") or {}).get("total_duration_ms")
    time_segment = fmt_duration_ms(duration_ms) if duration_ms else ""

    parts = [p for p in [
        branch_segment,
        context_segment,
        io_segment,
        model_segment,
        time_segment,
    ] if p]

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
        sys.stdout.write("⎇ ?  │  ░░░░░░░░░░░░░░░░  --%\n")


if __name__ == "__main__":
    main()
