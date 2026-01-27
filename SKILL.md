---
name: recall
version: 1.2.0
description: Session recall, failure tracking, and skill management for Claude Code

installs:
  bin:
    - skill
    - session-context.py
    - index-session.py
    - recall-sessions.py
  hooks:
    - on-bash-failure.py
  lib:
    - sops.py
  commands:
    - recall.md
    - failures.md
    - history.md

hooks:
  SessionStart:
    command: python3 ~/.claude/bin/session-context.py
    timeout: 5
  SessionEnd:
    command: python3 ~/.claude/bin/index-session.py
    timeout: 30
  PostToolUse:
    matcher: Bash
    command: python3 ~/.claude/hooks/on-bash-failure.py
    timeout: 10

dependencies:
---

# Recall Skill

Session memory and failure tracking for Claude Code.

## Features

- **Session Recall**: Search and browse past Claude Code sessions
- **Failure Tracking**: Learn from command failures with SOP suggestions
- **Skill Management**: Install, upgrade, and manage skills

## Commands

- `/recall` - List recent sessions
- `/recall last` - Show previous session details
- `/recall <term>` - Search past sessions
- `/recall failures` - Show failure patterns and learnings
- `/failures` - Analyze failures from current session
- `/history` - Show command history

## Skill Management

```bash
skill install <path>   # Install a skill from source
skill upgrade <name>   # Upgrade an installed skill
skill list             # List installed skills
```

## Hooks

- **SessionStart**: Loads context from previous sessions
- **SessionEnd**: Indexes session for future recall
- **PostToolUse (Bash)**: Provides SOP guidance on failures
