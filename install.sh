#!/bin/bash
#
# Install recall-skill for Claude Code
#
# Usage: ./install.sh
#
# This will:
# 1. Create ~/.claude/bin, ~/.claude/commands, ~/.claude/hooks if needed
# 2. Copy scripts to ~/.claude/bin/
# 3. Copy hooks to ~/.claude/hooks/
# 4. Copy commands to ~/.claude/commands/
# 5. Show instructions for adding hooks to settings.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing recall-skill for Claude Code..."
echo ""

# Create directories
mkdir -p "$CLAUDE_DIR/bin"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/hooks"

# Copy bin scripts
echo "Copying scripts to $CLAUDE_DIR/bin/..."
cp "$SCRIPT_DIR/bin/recall-sessions.py" "$CLAUDE_DIR/bin/"
cp "$SCRIPT_DIR/bin/index-session.py" "$CLAUDE_DIR/bin/"
cp "$SCRIPT_DIR/bin/session-context.py" "$CLAUDE_DIR/bin/"
cp "$SCRIPT_DIR/bin/claude-failures" "$CLAUDE_DIR/bin/"
cp "$SCRIPT_DIR/bin/claude-history" "$CLAUDE_DIR/bin/"
chmod +x "$CLAUDE_DIR/bin/"*

# Copy hooks
echo "Copying hooks to $CLAUDE_DIR/hooks/..."
cp "$SCRIPT_DIR/hooks/on-bash-failure.py" "$CLAUDE_DIR/hooks/"
chmod +x "$CLAUDE_DIR/hooks/"*

# Copy commands
echo "Copying commands to $CLAUDE_DIR/commands/..."
cp "$SCRIPT_DIR/commands/recall.md" "$CLAUDE_DIR/commands/"
cp "$SCRIPT_DIR/commands/failures.md" "$CLAUDE_DIR/commands/"
cp "$SCRIPT_DIR/commands/history.md" "$CLAUDE_DIR/commands/"

echo ""
echo "Files installed successfully!"
echo ""
echo "=================================================="
echo "IMPORTANT: Add hooks to ~/.claude/settings.json"
echo "=================================================="
echo ""
echo "Add the following to your settings.json 'hooks' section:"
echo ""
cat << 'EOF'
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
EOF

echo ""
echo "Available commands after installation:"
echo "  /recall          - Search past sessions, show learnings"
echo "  /recall failures - Show failure patterns and SOPs"
echo "  /failures        - Analyze failures with resolutions"
echo "  /history         - Show bash command history"
echo ""
echo "Done! Restart Claude Code for hooks to take effect."
