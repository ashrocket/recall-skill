Search and recall information from past Claude Code sessions for the current project.

Uses a unified index that captures user messages, bash commands, and failure patterns across sessions.

Usage:
- `/recall` - List recent sessions with summaries and stats
- `/recall [search term]` - Search past sessions (messages, commands, failures, skills)
- `/recall last` - Show details from the most recent previous session
- `/recall failures` - Show failure patterns and learnings
- `/recall knowledge` - Show current CLAUDE.md contents (global and project)
- `/recall stats` - Show skill and learning usage statistics
- `/recall cleanup` - Analyze index and show available cleanup actions
- `/recall cleanup --noise` - Remove low-value sessions (<3 msgs, no failures)
- `/recall cleanup --sensitive` - Remove sessions containing secrets/tokens
- `/recall cleanup --jsonl` - Remove old .jsonl files (>30d sessions, >7d agents)
- `/recall cleanup --dedup` - Deduplicate failure pattern entries
- `/recall cleanup --all` - Run all cleanup actions
- `/recall learn` - Review and approve pending learnings
- `/recall learn --batch` - Accept all pending learnings
- `/recall learn --approve N` - Approve specific pending learning by index
- `/recall learn --reject N` - Reject specific pending learning by index

Examples:
- `/recall linkedin` - Find discussions about LinkedIn
- `/recall permission denied` - Find when you hit permission errors
- `/recall failures` - See learnings and best practices
- `/recall cleanup --all` - Clean everything at once

Run the session parser script and display results:
```
python3 ~/.claude/bin/recall-sessions.py "$PWD" $ARGUMENTS
```

## How it works

**SessionEnd hook** (`index-session.py`):
- Automatically indexes each session when it ends
- Captures: user messages, bash commands, failures, error patterns
- Builds searchable index at `~/.claude/projects/{project}/recall-index.json`

**SessionStart hook** (`session-context.py`):
- Shows context from previous sessions when starting a new one
- Surfaces recurring failure patterns as warnings
- Hints at incomplete tasks from last session

## Cleanup Mode

`/recall cleanup` without flags shows an analysis report with suggested actions.
With flags, it performs the cleanup directly:

- `--noise` - Removes sessions with <3 messages and no failures from index + detail files
- `--sensitive` - Removes sessions containing secrets (API keys, tokens, SSH keys, passwords)
- `--jsonl` - Removes raw .jsonl files older than 30 days (agents: 7 days), keeps 5 most recent
- `--dedup` - Merges duplicate failure pattern entries (same command prefix)
- `--all` - Runs all four cleanup actions in sequence

## Learning System

Learnings are automatically proposed by `extract-knowledge.py` when:
- A command fails 3+ times in a session with the same error category
- A failed command is followed by a successful variant (resolution pair)

Use `/recall learn` to review pending proposals, or `/recall learn --batch` to accept all.

Learnings are structured as:
```json
{
  "category": "shell|git|aws|python|etc",
  "title": "Short descriptive title",
  "description": "What the issue/pattern is",
  "solution": "How to fix or avoid it"
}
```

After cleanup or learning approval, run `/recall failures` to verify results.
