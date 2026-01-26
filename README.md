# recall-skill

A collection of Claude Code skills for session memory, failure tracking, and command history.

## Skills Overview

| Skill | Command | Hooks | Overhead |
|-------|---------|-------|----------|
| **recall** | `/recall` | SessionStart + SessionEnd | Every session start/end |
| **failures** | `/failures` | PostToolUse (Bash) | Every Bash command |
| **history** | `/history` | None | On-demand only |

### recall - Session Memory

Automatically indexes your Claude Code sessions and provides searchable history:
- Session summaries and user messages
- Failure pattern tracking and categorization
- Structured learnings and best practices
- Cross-session search

### failures - Bash Failure SOPs

Tracks bash command failures and provides Standard Operating Procedures:
- Automatic failure detection after each Bash command
- Pattern matching to known error types
- SOPs with proven solutions
- Learning from what worked vs what failed

### history - Command History

Simple on-demand command history viewer:
- View recent commands from the current session
- Filter to show only failed commands
- No hooks, no overhead

## Installation

```bash
git clone https://github.com/ashrocket/recall-skill.git
cd recall-skill
./install.sh
```

### Installation Options

```bash
# Install everything (default)
./install.sh

# Install specific skills
./install.sh --recall           # Just session memory
./install.sh --failures         # Just failure SOPs
./install.sh --history          # Just command history

# Combine options
./install.sh --recall --history # Session memory + history, no bash hook

# Minimal install (no hooks, no overhead)
./install.sh --minimal          # Same as --history
```

Use `./install.sh --help` for full details.

### Hook Configuration

After installation, add hooks to `~/.claude/settings.json`. The installer shows the exact configuration needed based on your selected skills.

**Full configuration (all skills):**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/bin/session-context.py",
            "timeout": 5
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/bin/index-session.py",
            "timeout": 30
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/on-bash-failure.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Usage

### /recall - Session Memory

| Command | Description |
|---------|-------------|
| `/recall` | List recent sessions with summaries and stats |
| `/recall <search>` | Search past sessions for a topic |
| `/recall last` | Show details from the previous session |
| `/recall failures` | Show failure patterns and learnings |
| `/recall cleanup` | Analyze index for cleanup opportunities |

**Examples:**

```bash
# Find discussions about authentication
/recall authentication

# See what you worked on yesterday
/recall last

# Check recurring errors and best practices
/recall failures
```

### /failures - Bash Failure SOPs

| Command | Description |
|---------|-------------|
| `/failures` | Show recent failures with resolutions |
| `/failures --sop` | Include Standard Operating Procedures |
| `/failures --recent 20` | Show more failure groups |

The failures skill:
1. Tracks every bash command and its exit status
2. Groups failures by error type (permission denied, not found, etc.)
3. Records what commands eventually worked
4. Provides SOPs based on learned patterns

### /history - Command History

| Command | Description |
|---------|-------------|
| `/history` | Show last 20 commands |
| `/history 50` | Show last 50 commands |
| `/history --failures` | Show only failed commands with errors |

## Choosing What to Install

**Install everything** if you want full session memory and failure tracking. The hooks add minimal latency but run on every session and bash command.

**Install --recall only** if you want session search without the per-bash-command overhead.

**Install --failures only** if you mainly want bash failure SOPs without session indexing.

**Install --minimal** (history only) if you want zero overhead - just on-demand command history.

## File Structure

```
~/.claude/
├── bin/
│   ├── recall-sessions.py    # recall CLI
│   ├── index-session.py      # recall SessionEnd hook
│   ├── session-context.py    # recall SessionStart hook
│   ├── claude-failures       # failures CLI
│   └── claude-history        # history CLI
├── hooks/
│   └── on-bash-failure.py    # failures PostToolUse hook
├── commands/
│   ├── recall.md             # /recall skill definition
│   ├── failures.md           # /failures skill definition
│   └── history.md            # /history skill definition
├── projects/
│   └── {project}/
│       ├── recall-index.json # Searchable index (recall)
│       └── *.jsonl           # Raw session files
└── settings.json             # Hook configuration
```

## Index Structure (recall)

The recall index (`recall-index.json`) contains:

```json
{
  "version": 1,
  "project": "-Users-you-code-myproject",
  "sessions": {
    "session-uuid": {
      "date": "2026-01-20T15:30:00",
      "summary": "First few user messages...",
      "message_count": 15,
      "command_count": 42,
      "failure_count": 3,
      "topics": ["authentication", "api"],
      "user_messages": [...],
      "failures": [...]
    }
  },
  "failure_patterns": {
    "permission_denied": [...],
    "not_found": [...],
    "git_error": [...]
  },
  "learnings": [...]
}
```

## Learnings

The `learnings` array stores actionable best practices:

| Field | Description |
|-------|-------------|
| `category` | Type: `shell`, `git`, `ssh`, `python`, `deployment`, etc. |
| `title` | Short descriptive title |
| `description` | What the issue/pattern is |
| `solution` | How to fix or avoid it |
| `tools` | (Optional) Map of tool names to usage examples |
| `examples` | (Optional) Array of example commands |

## Failure Categories

Both recall and failures skills categorize errors:

| Category | Triggers |
|----------|----------|
| `permission_denied` | "permission denied", "access denied", "EACCES" |
| `not_found` | "not found", "no such file", "ENOENT" |
| `syntax_error` | "syntax error", "parse error" |
| `connection_error` | "connection refused", "timeout" |
| `import_error` | "import error", "module not found" |
| `type_error` | "TypeError" |
| `git_error` | "fatal:", git errors |
| `npm_error` | "npm ERR", "npm WARN" |
| `python_error` | "Traceback", "Exception" |
| `other_error` | Everything else |

## Requirements

- Python 3.8+
- Claude Code CLI

## Tips

1. **Start minimal** - Try `--history` first, add more skills as needed
2. **Add learnings proactively** - When you solve a recurring issue, add it to learnings
3. **Clean up regularly** - Run `/recall cleanup` monthly to remove noise
4. **Search before asking** - Use `/recall <topic>` to find past discussions

## Contributing

PRs welcome! Ideas for improvement:
- Better topic extraction
- Semantic search
- Cross-project search
- Automatic learning extraction from resolved failures

## License

MIT
