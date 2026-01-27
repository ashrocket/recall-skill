Search and recall information from past Claude Code sessions for the current project.

Uses a unified index that captures user messages, bash commands, and failure patterns across sessions.

Usage:
- `/recall` - List recent sessions with summaries and stats
- `/recall [search term]` - Search past sessions for specific topics
- `/recall last` - Show details from the most recent previous session
- `/recall failures` - Show failure patterns and learnings
- `/recall cleanup` - Clean up old sessions and manage learnings
- `/recall learn` - Review and approve pending learnings
- `/recall learn --batch` - Accept all pending learnings with suggested scope

Examples:
- `/recall linkedin` - Find discussions about LinkedIn
- `/recall permission denied` - Find when you hit permission errors
- `/recall failures` - See learnings and best practices
- `/recall cleanup` - Remove noise, add learnings

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

When `/recall cleanup` is invoked, Claude should:

1. **Read the recall-index.json** at `~/.claude/projects/{project}/recall-index.json`

2. **Analyze sessions for usefulness:**
   - Sessions with <3 messages and no failures = likely noise
   - Sessions with only context continuation messages = noise
   - Sessions containing sensitive data (keys, tokens) = DELETE immediately
   - Sessions >7 days old with no learnings extracted = candidates for removal

3. **Clean failure_patterns:**
   - Remove one-off errors that aren't recurring
   - Remove errors for non-existent domains/files (not actionable)
   - Keep only patterns that have actionable fixes

4. **Add/update learnings:**
   Learnings should be structured as:
   ```json
   {
     "category": "bitbucket|shell|git|ssh|deployment|python|etc",
     "title": "Short descriptive title",
     "description": "What the issue/pattern is",
     "solution": "How to fix or avoid it",
     "tools": {"tool_name": "usage example"},  // optional
     "examples": ["example command 1", "example command 2"]  // optional
   }
   ```

5. **Key learnings to always include for this project:**
   - Bitbucket CLI tools at `~/code/kureapp-tools/bitbucket/` (NOT gh!)
   - Token at `~/.bb-cli-personal-token`
   - Pipelines auto-deploy on merge to dev - don't SSH to deploy

6. **Optionally clean raw .jsonl files** if they're taking too much space

After cleanup, run `/recall failures` to verify the learnings look correct.

After showing results, offer to help with any incomplete tasks found or provide more detail on specific sessions.
