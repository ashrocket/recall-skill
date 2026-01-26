#!/bin/bash
#
# Install recall-skill for Claude Code
#
# Usage: ./install.sh [options]
#
# Options:
#   --all          Install all skills (default)
#   --recall       Install recall skill only (session indexing/search)
#   --failures     Install failures skill only (bash failure SOPs)
#   --history      Install history skill only (command history)
#   --minimal      Install history only (no hooks, no overhead)
#   --help         Show this help
#
# You can combine options: ./install.sh --recall --history

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

# Default: install all
INSTALL_RECALL=false
INSTALL_FAILURES=false
INSTALL_HISTORY=false
SHOW_HELP=false

# Parse arguments
if [ $# -eq 0 ]; then
    # No args = install all
    INSTALL_RECALL=true
    INSTALL_FAILURES=true
    INSTALL_HISTORY=true
else
    while [ $# -gt 0 ]; do
        case "$1" in
            --all)
                INSTALL_RECALL=true
                INSTALL_FAILURES=true
                INSTALL_HISTORY=true
                ;;
            --recall)
                INSTALL_RECALL=true
                ;;
            --failures)
                INSTALL_FAILURES=true
                ;;
            --history)
                INSTALL_HISTORY=true
                ;;
            --minimal)
                INSTALL_HISTORY=true
                ;;
            --help|-h)
                SHOW_HELP=true
                ;;
            *)
                echo "Unknown option: $1"
                SHOW_HELP=true
                ;;
        esac
        shift
    done
fi

if [ "$SHOW_HELP" = true ]; then
    cat << 'EOF'
recall-skill installer

Usage: ./install.sh [options]

Options:
  --all          Install all skills (default if no options given)
  --recall       Install recall skill (session indexing and search)
  --failures     Install failures skill (bash failure SOPs)
  --history      Install history skill (command history)
  --minimal      Alias for --history (no hooks, no overhead)
  --help         Show this help

You can combine options: ./install.sh --recall --history

Skill Details:
  recall     SessionStart + SessionEnd hooks. Indexes sessions for search.
             Overhead: Runs on every session start and end.

  failures   PostToolUse hook on Bash commands. Tracks failures and SOPs.
             Overhead: Runs after every Bash command.

  history    No hooks. Shows command history on-demand.
             Overhead: None (on-demand only).

Examples:
  ./install.sh                    # Install everything
  ./install.sh --minimal          # Just history (no hooks)
  ./install.sh --recall --history # Session search + history, no bash hook
EOF
    exit 0
fi

# Check if anything selected
if [ "$INSTALL_RECALL" = false ] && [ "$INSTALL_FAILURES" = false ] && [ "$INSTALL_HISTORY" = false ]; then
    echo "No skills selected. Use --help for options."
    exit 1
fi

echo "Installing recall-skill for Claude Code..."
echo ""

# Show what will be installed
echo "Selected skills:"
[ "$INSTALL_RECALL" = true ] && echo "  ✓ recall (SessionStart + SessionEnd hooks)"
[ "$INSTALL_FAILURES" = true ] && echo "  ✓ failures (PostToolUse Bash hook)"
[ "$INSTALL_HISTORY" = true ] && echo "  ✓ history (no hooks)"
echo ""

# Create directories
mkdir -p "$CLAUDE_DIR/bin"
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/hooks"
mkdir -p "$CLAUDE_DIR/lib"

# Install shared library (needed by failures skill)
if [ "$INSTALL_FAILURES" = true ]; then
    echo "Installing shared library..."
    cp "$SCRIPT_DIR/lib/__init__.py" "$CLAUDE_DIR/lib/"
    cp "$SCRIPT_DIR/lib/sops.py" "$CLAUDE_DIR/lib/"

    # Install base SOPs
    mkdir -p "$CLAUDE_DIR/shell-failures"
    if [ ! -f "$CLAUDE_DIR/shell-failures/sops.json" ]; then
        echo "Installing base SOPs..."
        cp "$SCRIPT_DIR/sops/base.json" "$CLAUDE_DIR/shell-failures/sops.json"
    else
        echo "Keeping existing SOPs (not overwriting ~/.claude/shell-failures/sops.json)"
    fi
fi

# Install recall skill
if [ "$INSTALL_RECALL" = true ]; then
    echo "Installing recall skill..."
    cp "$SCRIPT_DIR/bin/recall-sessions.py" "$CLAUDE_DIR/bin/"
    cp "$SCRIPT_DIR/bin/index-session.py" "$CLAUDE_DIR/bin/"
    cp "$SCRIPT_DIR/bin/session-context.py" "$CLAUDE_DIR/bin/"
    cp "$SCRIPT_DIR/commands/recall.md" "$CLAUDE_DIR/commands/"
fi

# Install failures skill
if [ "$INSTALL_FAILURES" = true ]; then
    echo "Installing failures skill..."
    cp "$SCRIPT_DIR/bin/claude-failures" "$CLAUDE_DIR/bin/"
    cp "$SCRIPT_DIR/hooks/on-bash-failure.py" "$CLAUDE_DIR/hooks/"
    cp "$SCRIPT_DIR/commands/failures.md" "$CLAUDE_DIR/commands/"
fi

# Install history skill
if [ "$INSTALL_HISTORY" = true ]; then
    echo "Installing history skill..."
    cp "$SCRIPT_DIR/bin/claude-history" "$CLAUDE_DIR/bin/"
    cp "$SCRIPT_DIR/commands/history.md" "$CLAUDE_DIR/commands/"
fi

# Make all scripts executable
chmod +x "$CLAUDE_DIR/bin/"* 2>/dev/null || true
chmod +x "$CLAUDE_DIR/hooks/"* 2>/dev/null || true

echo ""
echo "Files installed successfully!"
echo ""

# Show hook configuration if needed
if [ "$INSTALL_RECALL" = true ] || [ "$INSTALL_FAILURES" = true ]; then
    echo "=================================================="
    echo "IMPORTANT: Add hooks to ~/.claude/settings.json"
    echo "=================================================="
    echo ""
    echo "Add the following to your settings.json 'hooks' section:"
    echo ""

    echo "{"
    echo '  "hooks": {'

    NEED_COMMA=false

    if [ "$INSTALL_RECALL" = true ]; then
        cat << 'EOF'
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
EOF
        NEED_COMMA=true
    fi

    if [ "$INSTALL_FAILURES" = true ]; then
        if [ "$NEED_COMMA" = true ]; then
            echo "    ,"
        fi
        cat << 'EOF'
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
EOF
    fi

    echo "  }"
    echo "}"
    echo ""
fi

# Show available commands
echo "Available commands after installation:"
[ "$INSTALL_RECALL" = true ] && echo "  /recall          - Search past sessions, view learnings"
[ "$INSTALL_FAILURES" = true ] && echo "  /failures        - Analyze failures with SOPs"
[ "$INSTALL_HISTORY" = true ] && echo "  /history         - Show shell command history"
echo ""

if [ "$INSTALL_FAILURES" = true ]; then
    echo "SOPs location: ~/.claude/shell-failures/sops.json"
    echo "Project SOPs: .claude/sops.json (create in project root to override)"
    echo ""
fi

if [ "$INSTALL_RECALL" = true ] || [ "$INSTALL_FAILURES" = true ]; then
    echo "Done! Restart Claude Code for hooks to take effect."
else
    echo "Done! No hooks to configure - commands are ready to use."
fi
