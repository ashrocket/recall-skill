#!/usr/bin/env python3
"""
Interactive learning review for /recall learn command.
Shows pending learnings and accepts user input for approval.
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from pending import load_pending, remove_pending, get_pending_count
from knowledge import add_knowledge, CATEGORIES


def format_learning(learning: dict, index: int) -> str:
    """Format a learning for display."""
    opposite = 'project' if learning['suggested_scope'] == 'global' else 'global'
    lines = [
        f"### {index}. [{learning['category']}] {learning['title']}",
        f"From: {learning['session_summary']} ({learning['timestamp'][:10]})",
        "",
        f"  {learning['content']}",
        "",
        f"  Suggested: {learning['suggested_scope']}",
        "",
        f"  [a]ccept  [A]ccept to {opposite}  [e]dit  [r]eject  [s]kip"
    ]
    return '\n'.join(lines)


def show_pending():
    """Show all pending learnings for review."""
    data = load_pending()
    pending = data.get('pending', [])

    if not pending:
        print("## No Pending Learnings")
        print()
        print("Knowledge extraction happens automatically at session end.")
        print("Proposals will appear here for your review.")
        return

    print(f"## Pending Learnings ({len(pending)} items)")
    print()
    print("Review each item and choose an action:")
    print("  [a]ccept - Add with suggested scope")
    print("  [A]ccept - Add with opposite scope")
    print("  [e]dit  - Edit content before adding")
    print("  [r]eject - Delete permanently")
    print("  [s]kip  - Keep for later review")
    print()

    for i, learning in enumerate(pending, 1):
        print(format_learning(learning, i))
        print()


def process_action(learning_id: str, action: str, learning: dict) -> str:
    """Process user action on a learning."""
    if action == 'a':
        # Accept with suggested scope
        scope = learning['suggested_scope']
        success = add_knowledge(learning['content'], learning['category'], scope)
        if success:
            remove_pending(learning_id)
            return f"Added to {scope} CLAUDE.md"
        return "Failed to add"

    elif action == 'A':
        # Accept with opposite scope
        scope = 'project' if learning['suggested_scope'] == 'global' else 'global'
        success = add_knowledge(learning['content'], learning['category'], scope)
        if success:
            remove_pending(learning_id)
            return f"Added to {scope} CLAUDE.md"
        return "Failed to add"

    elif action == 'r':
        # Reject
        remove_pending(learning_id)
        return "Rejected and removed"

    elif action == 's':
        # Skip
        return "Skipped (will appear again)"

    elif action == 'e':
        # Edit - just inform, actual editing needs interactive input
        return "Edit mode not available in batch. Use Claude to edit pending-learnings.json"

    return f"Unknown action: {action}"


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == '--batch':
        # Batch mode: accept all with suggested scope
        data = load_pending()
        for learning in data.get('pending', []):
            result = process_action(learning['id'], 'a', learning)
            print(f"{learning['title']}: {result}")
        return

    # Show mode (default)
    show_pending()

    # If there are pending items, show hint
    count = get_pending_count()
    if count > 0:
        print("---")
        print("To accept all with suggested scope: `/recall learn --batch`")
        print("To review interactively, tell Claude which action to take on each item.")


if __name__ == '__main__':
    main()
