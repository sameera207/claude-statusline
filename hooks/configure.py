#!/usr/bin/env python3
"""
SessionStart hook: writes statusLine config into ~/.claude/settings.json
once, using CLAUDE_PLUGIN_ROOT so the path is correct for any user.
"""
import json
import os
import sys
from pathlib import Path

plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
if not plugin_root:
    sys.exit(0)

settings_path = Path.home() / ".claude" / "settings.json"
if not settings_path.exists():
    sys.exit(0)

try:
    settings = json.loads(settings_path.read_text())
except Exception:
    sys.exit(0)

expected_command = f'python3 "{plugin_root}/hooks/statusline.py"'

if settings.get("statusLine", {}).get("command") == expected_command:
    sys.exit(0)

settings["statusLine"] = {
    "type": "command",
    "command": expected_command,
}

try:
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
except Exception:
    pass
