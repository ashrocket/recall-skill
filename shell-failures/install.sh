#!/bin/bash
set -e

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing shell-failures skill..."

# Create directories
mkdir -p "$CLAUDE_DIR/bin"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/shell-failures"

# Symlink command definition
ln -sf "$SKILL_DIR/commands/failures.md" "$CLAUDE_DIR/commands/failures.md"
echo "Linked /failures command"

# Symlink binary
ln -sf "$SKILL_DIR/bin/failures" "$CLAUDE_DIR/bin/failures"
echo "Linked failures binary"

# Copy base SOPs (don't overwrite existing)
if [ ! -f "$CLAUDE_DIR/shell-failures/sops.json" ]; then
    cp "$SKILL_DIR/sops/base.json" "$CLAUDE_DIR/shell-failures/sops.json"
    echo "Copied base SOPs"
else
    echo "SOPs already exist (preserved)"
fi

# Install hooks
python3 "$SKILL_DIR/lib/install-hooks.py"

echo ""
echo "========================================"
echo "shell-failures installed!"
echo "========================================"
echo ""
echo "Commands:"
echo "  /failures          - Show failures with resolutions"
echo "  /failures --sop    - Include SOP guidance"
echo "  /failures --all    - Show all SOPs"
echo ""
echo "SOPs stored at:"
echo "  Global:  ~/.claude/shell-failures/sops.json"
echo "  Project: .claude/sops.json (optional)"
echo ""
