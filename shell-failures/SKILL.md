---
name: shell-failures
description: Use when bash commands fail - shows SOPs for common errors and proposes new patterns when fixes work
---

# Shell Failures

Shows Standard Operating Procedures when bash commands fail. Learns new patterns when fixes work.

## How It Works

1. **On failure:** Hook matches error against SOPs, shows relevant fix steps
2. **On success after failure:** Proposes saving the pattern as new SOP
3. **On `/failures`:** Shows failure history with resolutions

## Commands

- `/failures` - Show recent failures with what worked
- `/failures --sop` - Include full SOP for each error type
- `/failures --all` - List all SOPs (global + project)

## SOPs

Stored as JSON:
- Global: `~/.claude/shell-failures/sops.json`
- Project: `.claude/sops.json` (overrides global)

## Saving New SOPs

When a fix works, you'll see:
```
✅ That command worked after SHELL_PARSE_ERROR
Save as SOP? Reply: "save global", "save project", or continue
```

Reply with your choice to save the pattern.
