"""
Tests for hooks/statusline.py
"""
from __future__ import annotations

import sys
import os
import json
import subprocess
from datetime import datetime, timezone, timedelta

# Allow importing from hooks/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
import statusline as sl


# ── fmt_tokens ────────────────────────────────────────────────────────────────

def test_fmt_tokens_small():
    assert sl.fmt_tokens(500) == "500"

def test_fmt_tokens_thousands():
    assert sl.fmt_tokens(136_000) == "136k"

def test_fmt_tokens_thousands_decimal():
    assert sl.fmt_tokens(1_500) == "1.5k"

def test_fmt_tokens_millions():
    assert sl.fmt_tokens(1_000_000) == "1M"

def test_fmt_tokens_millions_decimal():
    assert sl.fmt_tokens(1_500_000) == "1.5M"

def test_fmt_tokens_200k():
    assert sl.fmt_tokens(200_000) == "200k"


# ── colour_for ────────────────────────────────────────────────────────────────

def test_colour_green_low():
    assert sl.colour_for(0) == sl.GREEN

def test_colour_green_boundary():
    assert sl.colour_for(59) == sl.GREEN

def test_colour_amber_at_60():
    assert sl.colour_for(60) == sl.AMBER

def test_colour_amber_boundary():
    assert sl.colour_for(84) == sl.AMBER

def test_colour_red_at_85():
    assert sl.colour_for(85) == sl.RED

def test_colour_red_at_100():
    assert sl.colour_for(100) == sl.RED


# ── progress_bar ──────────────────────────────────────────────────────────────

def test_progress_bar_zero():
    bar = sl.progress_bar(0)
    assert bar == "░" * sl.BAR_WIDTH

def test_progress_bar_full():
    bar = sl.progress_bar(100)
    assert bar == "█" * sl.BAR_WIDTH

def test_progress_bar_half():
    bar = sl.progress_bar(50)
    assert len(bar) == sl.BAR_WIDTH
    assert bar.count("█") == sl.BAR_WIDTH // 2

def test_progress_bar_length_always_correct():
    for pct in [0, 10, 33, 45, 60, 75, 85, 99, 100]:
        assert len(sl.progress_bar(pct)) == sl.BAR_WIDTH


# ── fmt_elapsed ───────────────────────────────────────────────────────────────

def _ts_ago(minutes: int) -> str:
    t = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return t.isoformat()

def test_elapsed_minutes():
    assert sl.fmt_elapsed(_ts_ago(42)) == "⏱ 42m"

def test_elapsed_hours_and_minutes():
    assert sl.fmt_elapsed(_ts_ago(84)) == "⏱ 1h 24m"

def test_elapsed_zero():
    assert sl.fmt_elapsed(_ts_ago(0)) == "⏱ 0m"

def test_elapsed_bad_input():
    assert sl.fmt_elapsed("not-a-date") == "⏱ --"

def test_elapsed_z_suffix():
    t = datetime.now(timezone.utc) - timedelta(minutes=10)
    ts = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert sl.fmt_elapsed(ts) == "⏱ 10m"


# ── fmt_model ─────────────────────────────────────────────────────────────────

def test_fmt_model_strips_prefix():
    assert sl.fmt_model("claude-sonnet-4-6") == "sonnet-4-6"

def test_fmt_model_no_prefix():
    assert sl.fmt_model("gpt-4o") == "gpt-4o"

def test_fmt_model_strips_case_insensitive():
    assert sl.fmt_model("Claude-Opus-4") == "Opus-4"

def test_fmt_model_empty():
    assert sl.fmt_model("") == ""


# ── render integration ────────────────────────────────────────────────────────

def _make_payload(pct=45, used=136_000, total=200_000,
                  model="claude-sonnet-4-6", minutes_ago=42) -> dict:
    return {
        "context_window": {
            "used_percentage": pct,
            "context_window_size": total,
        },
        "current_usage": {
            "input_tokens": used,
        },
        "model": {
            "display_name": model,
        },
        "session": {
            "started_at": _ts_ago(minutes_ago),
        },
    }

def test_render_contains_pct():
    out = sl.render(_make_payload(pct=45))
    assert "45%" in out

def test_render_contains_token_counts():
    out = sl.render(_make_payload(used=136_000, total=200_000))
    assert "136k/200k" in out

def test_render_contains_model():
    out = sl.render(_make_payload(model="claude-sonnet-4-6"))
    assert "sonnet-4-6" in out

def test_render_contains_time():
    out = sl.render(_make_payload(minutes_ago=42))
    assert "⏱" in out

def test_render_null_usage_no_crash():
    payload = {
        "context_window": {"context_window_size": 200_000},
        "current_usage": None,
        "model": {"display_name": "claude-sonnet-4-6"},
        "session": {"started_at": _ts_ago(5)},
    }
    out = sl.render(payload)
    assert "%" in out

def test_render_empty_payload_no_crash():
    out = sl.render({})
    assert isinstance(out, str)

def test_render_1m_context():
    out = sl.render(_make_payload(used=750_000, total=1_000_000))
    assert "750k/1M" in out

def test_render_green_colour():
    out = sl.render(_make_payload(pct=30))
    assert sl.GREEN in out

def test_render_amber_colour():
    out = sl.render(_make_payload(pct=70))
    assert sl.AMBER in out

def test_render_red_colour():
    out = sl.render(_make_payload(pct=90))
    assert sl.RED in out


# ── CLI smoke test ────────────────────────────────────────────────────────────

def test_cli_with_valid_json():
    payload = json.dumps(_make_payload(pct=45))
    script  = os.path.join(os.path.dirname(__file__), "..", "hooks", "statusline.py")
    result  = subprocess.run(
        ["python3", script],
        input=payload,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "45%" in result.stdout

def test_cli_with_empty_stdin():
    script = os.path.join(os.path.dirname(__file__), "..", "hooks", "statusline.py")
    result = subprocess.run(
        ["python3", script],
        input="",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Should output a line (fallback or normal)
    assert result.stdout.strip() != ""

def test_cli_with_garbage_input():
    script = os.path.join(os.path.dirname(__file__), "..", "hooks", "statusline.py")
    result = subprocess.run(
        ["python3", script],
        input="not json at all!!!",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() != ""
