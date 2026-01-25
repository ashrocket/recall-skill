#!/usr/bin/env python3
"""
Merge shell-failures hook into existing hooks.json
"""

import json
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
HOOKS_FILE = CLAUDE_DIR / "hooks.json"
SKILL_DIR = Path(__file__).resolve().parent.parent

HOOK_CONFIG = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": f"python3 {SKILL_DIR / 'hooks' / 'post-bash.py'}",
            "timeout": 10
        }
    ]
}


def main():
    # Load existing hooks
    config = {"hooks": {}}
    if HOOKS_FILE.exists():
        try:
            with open(HOOKS_FILE) as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    if "hooks" not in config:
        config["hooks"] = {}

    # Add/update PostToolUse
    if "PostToolUse" not in config["hooks"]:
        config["hooks"]["PostToolUse"] = []

    # Check if already installed
    post_hooks = config["hooks"]["PostToolUse"]
    already_installed = any(
        "shell-failures" in str(h.get("hooks", [{}])[0].get("command", ""))
        for h in post_hooks
    )

    if not already_installed:
        config["hooks"]["PostToolUse"].append(HOOK_CONFIG)

    # Save
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with open(HOOKS_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print("Hook config updated")


if __name__ == "__main__":
    main()
