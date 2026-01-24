#!/bin/bash
#
# Install recall-skill for Claude Code
#
# Usage: ./install.sh
#
# This will:
# 1. Create ~/.claude/bin and ~/.claude/commands if needed
# 2. Copy scripts to ~/.claude/bin/
# 3. Copy command to ~/.claude/commands/
# 4. Show instructions for adding hooks to settings.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing recall-skill for Claude Code..."
echo ""

# Create directories
mkdir -p "$CLAUDE_DIR/bin"
mkdir -p "$CLAUDE_DIR/commands"

# Copy scripts
echo "Copying scripts to $CLAUDE_DIR/bin/..."
cp "$SCRIPT_DIR/bin/recall-sessions.py" "$CLAUDE_DIR/bin/"
cp "$SCRIPT_DIR/bin/index-session.py" "$CLAUDE_DIR/bin/"
cp "$SCRIPT_DIR/bin/session-context.py" "$CLAUDE_DIR/bin/"
chmod +x "$CLAUDE_DIR/bin/"*.py

# Copy command
echo "Copying command to $CLAUDE_DIR/commands/..."
cp "$SCRIPT_DIR/commands/recall.md" "$CLAUDE_DIR/commands/"

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
    ]
  }
}
EOF

echo ""
echo "Done! Run '/recall' in Claude Code to test."
