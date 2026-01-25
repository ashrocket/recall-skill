#!/bin/bash
set -e

CLAUDE_DIR="$HOME/.claude"

echo "Uninstalling shell-failures skill..."

# Remove symlinks
rm -f "$CLAUDE_DIR/commands/failures.md"
rm -f "$CLAUDE_DIR/bin/failures"
echo "✓ Removed symlinks"

# Note: We don't remove sops.json to preserve user customizations
echo "✓ SOPs preserved at ~/.claude/shell-failures/sops.json"

# Note: Hook removal would require parsing hooks.json
echo "⚠ Hook entry in ~/.claude/hooks.json must be removed manually"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ shell-failures uninstalled"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
