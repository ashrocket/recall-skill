# recall-skill

A Claude Code skill for searching and recalling information from past sessions.

**recall-skill** automatically indexes your Claude Code sessions and provides a searchable history with:
- Session summaries and user messages
- Failure pattern tracking and categorization
- Structured learnings and best practices
- Cleanup tools for managing session data

## Features

### Session Indexing
Every time a Claude Code session ends, the skill automatically:
- Extracts user messages and commands
- Identifies and categorizes failures (permission denied, not found, syntax errors, etc.)
- Builds a searchable index at `~/.claude/projects/{project}/recall-index.json`

### Session Context on Startup
When you start a new session, you'll see:
- Summary of your last session
- Total sessions and failure count
- Recurring failure patterns as warnings
- Hints about incomplete tasks

### Searchable History
Use `/recall` commands to:
- List recent sessions with stats
- Search for specific topics across sessions
- View failure patterns and learnings
- Analyze and clean up old data

## Installation

```bash
git clone https://github.com/ashrocket/recall-skill.git
cd recall-skill
./install.sh
```

The install script will:
1. Copy scripts to `~/.claude/bin/`
2. Copy the command to `~/.claude/commands/`
3. Show instructions for adding hooks to your `settings.json`

### Manual Hook Configuration

Add to `~/.claude/settings.json`:

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
    ]
  }
}
```

## Usage

### Basic Commands

| Command | Description |
|---------|-------------|
| `/recall` | List recent sessions with summaries and stats |
| `/recall <search>` | Search past sessions for a topic |
| `/recall last` | Show details from the previous session |
| `/recall failures` | Show failure patterns and learnings |
| `/recall cleanup` | Analyze index for cleanup opportunities |

### Examples

```bash
# Find discussions about authentication
/recall authentication

# See what you worked on yesterday
/recall last

# Check recurring errors and best practices
/recall failures

# Clean up old data and see disk usage
/recall cleanup
```

## Index Structure

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
  "learnings": [
    {
      "category": "shell",
      "title": "Avoid complex command substitution",
      "description": "zsh parses $(...) differently",
      "solution": "Split into multiple simple commands"
    }
  ]
}
```

## Learnings

The `learnings` array stores actionable best practices. Each learning should have:

| Field | Description |
|-------|-------------|
| `category` | Type: `shell`, `git`, `ssh`, `python`, `deployment`, etc. |
| `title` | Short descriptive title |
| `description` | What the issue/pattern is |
| `solution` | How to fix or avoid it |
| `tools` | (Optional) Map of tool names to usage examples |
| `examples` | (Optional) Array of example commands |

### Example Learning

```json
{
  "category": "bitbucket",
  "title": "Use BB CLI tools instead of gh",
  "description": "This project uses Bitbucket, NOT GitHub",
  "solution": "Use tools at ~/code/kureapp-tools/bitbucket/",
  "tools": {
    "create-pr.sh": "./create-pr.sh -t 'Title' -c",
    "merge-pr.sh": "./merge-pr.sh PR_ID"
  },
  "examples": [
    "~/code/tools/bitbucket/create-pr.sh -t 'Fix bug' -c",
    "~/code/tools/bitbucket/merge-pr.sh 42"
  ]
}
```

## Cleanup Mode

When you run `/recall cleanup`, Claude will:

1. **Analyze sessions** - Identify low-value sessions (<3 messages) and sessions containing sensitive data
2. **Check failure patterns** - Report noise level and suggest clearing non-actionable errors
3. **Verify learnings** - Check that useful learnings exist
4. **Report disk usage** - Show raw `.jsonl` file sizes and warn if >50MB

### What to Clean

- **Delete immediately**: Sessions containing API keys, SSH keys, tokens, passwords
- **Consider removing**: Sessions with <3 messages, old sessions with no learnings extracted
- **Clear from failure_patterns**: One-off errors, DNS lookups for non-existent domains
- **Keep/add to learnings**: Recurring issues with actionable fixes

## File Structure

```
~/.claude/
├── bin/
│   ├── recall-sessions.py    # Main CLI
│   ├── index-session.py      # SessionEnd hook
│   └── session-context.py    # SessionStart hook
├── commands/
│   └── recall.md             # Skill definition
├── projects/
│   └── {project}/
│       ├── recall-index.json # Searchable index
│       └── *.jsonl           # Raw session files
└── settings.json             # Hook configuration
```

## Requirements

- Python 3.8+
- Claude Code CLI

## Failure Categories

The skill automatically categorizes failures:

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

## Tips

1. **Add learnings proactively** - When you solve a recurring issue, add it to learnings so Claude remembers
2. **Clean up regularly** - Run `/recall cleanup` monthly to remove noise
3. **Search before asking** - Use `/recall <topic>` to find past discussions
4. **Check failures** - Run `/recall failures` when hitting errors to see past solutions

## Contributing

PRs welcome! Ideas for improvement:
- Better topic extraction
- Semantic search
- Cross-project search
- Automatic learning extraction from resolved failures

## License

MIT
