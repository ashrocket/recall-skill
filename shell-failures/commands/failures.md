---
name: failures
description: Show shell command failures from this session with resolutions and SOPs
---

Analyze bash command failures and show what worked.

Usage:
- `/failures` - Show recent failures with resolutions
- `/failures --sop` - Include SOP guidance for each error type
- `/failures --all` - Show all SOPs (global + project)
- `/failures --recent N` - Show last N failure groups (default: 10)

Run: `python3 ~/.claude/shell-failures/bin/failures "$PWD" $ARGUMENTS`

After showing output, if there are unresolved failures, suggest fixes based on SOPs.
