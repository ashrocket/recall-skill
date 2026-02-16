#!/usr/bin/env python3
"""
Review and manage pending learnings for the recall system.

Usage:
  recall-learn.py                    - Show pending learnings for review
  recall-learn.py --batch            - Accept all pending learnings
  recall-learn.py --approve <index>  - Approve specific learning
  recall-learn.py --reject <index>   - Reject specific learning
"""

import json
import sys
import os
from pathlib import Path

# Add lib to path
LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from knowledge import (
    get_pending_learnings,
    get_learnings,
    approve_learning,
    reject_learning,
    approve_all_pending,
    get_project_folder,
)


def format_learning(learning: dict, index: int) -> str:
    """Format a single learning for display."""
    cat = learning.get('category', 'general')
    title = learning.get('title', 'Unknown')
    desc = learning.get('description', '')
    solution = learning.get('solution', '')
    source = learning.get('source', 'manual')

    lines = [f"### [{index}] [{cat}] {title}"]
    if desc:
        lines.append(f"  {desc}")
    if solution:
        lines.append(f"  **Fix:** {solution}")
    lines.append(f"  _Source: {source}_")
    return '\n'.join(lines)


def show_pending(project_folder: str):
    """Show all pending learnings."""
    pending = get_pending_learnings(project_folder)
    approved = get_learnings(project_folder)

    print("## Pending Learnings")
    print()
    print(f"**Approved:** {len(approved)} | **Pending:** {len(pending)}")
    print()

    if not pending:
        print("No pending learnings to review.")
        print()
        print("Learnings are proposed automatically when:")
        print("  - A command fails 3+ times with the same error category")
        print("  - A failed command is followed by a successful variant")
        print()
        if approved:
            print(f"You have {len(approved)} approved learnings. Use `/recall failures` to view them.")
        return

    for i, learning in enumerate(pending):
        print(format_learning(learning, i))
        print()

    print("---")
    print("**Actions:**")
    print("  `/recall learn --batch` - Accept all pending learnings")
    print("  `/recall learn --approve 0` - Approve learning #0")
    print("  `/recall learn --reject 0` - Reject learning #0")


def batch_approve(project_folder: str):
    """Approve all pending learnings."""
    count = approve_all_pending(project_folder)
    if count > 0:
        print(f"## Approved {count} learnings")
        print()
        print("These will now appear in `/recall failures` and session start context.")
    else:
        print("No pending learnings to approve.")


def approve_one(project_folder: str, index_str: str):
    """Approve a specific learning by index."""
    try:
        idx = int(index_str)
    except ValueError:
        print(f"Invalid index: {index_str}")
        return

    learning = approve_learning(idx, project_folder)
    if learning:
        print(f"Approved: [{learning.get('category')}] {learning.get('title')}")
    else:
        print(f"No pending learning at index {idx}")


def reject_one(project_folder: str, index_str: str):
    """Reject a specific learning by index."""
    try:
        idx = int(index_str)
    except ValueError:
        print(f"Invalid index: {index_str}")
        return

    learning = reject_learning(idx, project_folder)
    if learning:
        print(f"Rejected: [{learning.get('category')}] {learning.get('title')}")
    else:
        print(f"No pending learning at index {idx}")


def main():
    cwd = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()
    project_folder = get_project_folder()

    args = sys.argv[1:]

    if not args:
        show_pending(project_folder)
    elif args[0] == '--batch':
        batch_approve(project_folder)
    elif args[0] == '--approve' and len(args) > 1:
        approve_one(project_folder, args[1])
    elif args[0] == '--reject' and len(args) > 1:
        reject_one(project_folder, args[1])
    else:
        show_pending(project_folder)


if __name__ == '__main__':
    main()
