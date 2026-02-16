#!/usr/bin/env python3
"""
Knowledge management library for the recall system.
Handles loading, saving, and formatting learnings from recall-index.json.
"""

import json
import os
from pathlib import Path
from typing import Optional


GLOBAL_CLAUDE_MD = Path.home() / ".claude" / "CLAUDE.md"


def get_project_folder() -> str:
    """Get current project folder name."""
    cwd = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()
    return cwd.replace('/', '-')


def get_project_claude_md() -> Optional[Path]:
    """Find project-level CLAUDE.md by walking up from cwd."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / "CLAUDE.md"
        if candidate.exists():
            return candidate
    return None


def get_index_path(project_folder: str = None) -> Path:
    """Get recall-index.json path for a project."""
    if not project_folder:
        project_folder = get_project_folder()
    return Path.home() / '.claude' / 'projects' / project_folder / 'recall-index.json'


def load_index(project_folder: str = None) -> dict:
    """Load recall index."""
    index_file = get_index_path(project_folder)
    if index_file.exists():
        try:
            with open(index_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        'version': 2,
        'project': project_folder or get_project_folder(),
        'sessions': {},
        'failure_patterns': {},
        'learnings': [],
        'pending_learnings': [],
        'usage': {'skills': {}, 'learnings_shown': {}}
    }


def save_index(index: dict, project_folder: str = None):
    """Save recall index."""
    if not project_folder:
        project_folder = get_project_folder()
    index_file = get_index_path(project_folder)
    index_file.parent.mkdir(parents=True, exist_ok=True)
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2, default=str)


def get_learnings(project_folder: str = None) -> list:
    """Get approved learnings from index."""
    index = load_index(project_folder)
    return index.get('learnings', [])


def get_pending_learnings(project_folder: str = None) -> list:
    """Get pending learnings awaiting approval."""
    index = load_index(project_folder)
    return index.get('pending_learnings', [])


def add_pending_learning(learning: dict, project_folder: str = None):
    """Add a learning to the pending queue."""
    index = load_index(project_folder)
    if 'pending_learnings' not in index:
        index['pending_learnings'] = []

    # Check for duplicates by title
    existing_titles = {l.get('title', '') for l in index['pending_learnings']}
    approved_titles = {l.get('title', '') for l in index.get('learnings', [])}

    if learning.get('title') not in existing_titles and learning.get('title') not in approved_titles:
        index['pending_learnings'].append(learning)
        save_index(index, project_folder)
        return True
    return False


def approve_learning(index: int, project_folder: str = None) -> Optional[dict]:
    """Move a pending learning to approved. Returns the learning or None."""
    idx = load_index(project_folder)
    pending = idx.get('pending_learnings', [])

    if 0 <= index < len(pending):
        learning = pending.pop(index)
        if 'learnings' not in idx:
            idx['learnings'] = []
        idx['learnings'].append(learning)
        save_index(idx, project_folder)
        return learning
    return None


def reject_learning(index: int, project_folder: str = None) -> Optional[dict]:
    """Remove a pending learning. Returns the removed learning or None."""
    idx = load_index(project_folder)
    pending = idx.get('pending_learnings', [])

    if 0 <= index < len(pending):
        learning = pending.pop(index)
        save_index(idx, project_folder)
        return learning
    return None


def approve_all_pending(project_folder: str = None) -> int:
    """Approve all pending learnings. Returns count approved."""
    idx = load_index(project_folder)
    pending = idx.get('pending_learnings', [])

    if not pending:
        return 0

    if 'learnings' not in idx:
        idx['learnings'] = []

    count = len(pending)
    idx['learnings'].extend(pending)
    idx['pending_learnings'] = []
    save_index(idx, project_folder)
    return count


def get_all_knowledge(project_folder: str = None) -> dict:
    """Get all knowledge organized by category."""
    learnings = get_learnings(project_folder)
    categories = {}

    for learning in learnings:
        if isinstance(learning, dict):
            cat = learning.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            title = learning.get('title', 'Unknown')
            solution = learning.get('solution', '')
            categories[cat].append(f"{title}: {solution}" if solution else title)

    return categories


def format_knowledge_summary(knowledge: dict) -> str:
    """Format knowledge for session start display."""
    lines = []
    for cat, items in sorted(knowledge.items()):
        lines.append(f"  [{cat}] {len(items)} learnings")
    return '\n'.join(lines) if lines else "  No learnings yet"
