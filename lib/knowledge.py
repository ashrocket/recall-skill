#!/usr/bin/env python3
"""
CLAUDE.md knowledge management utilities.
Handles reading, writing, and merging knowledge entries.
"""

import os
import re
from pathlib import Path
from typing import Optional

# Category headers in CLAUDE.md
CATEGORIES = ['Credentials', 'Tools', 'Gotchas', 'Workflows']

GLOBAL_CLAUDE_MD = Path.home() / '.claude' / 'CLAUDE.md'


def get_project_claude_md() -> Path:
    """Find project CLAUDE.md path. Creates .claude/ in git root or cwd."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / '.claude' / 'CLAUDE.md'
        if candidate.parent.exists():  # .claude dir exists
            return candidate
        # Also check for project root markers
        if (parent / '.git').exists():
            return parent / '.claude' / 'CLAUDE.md'
    return Path.cwd() / '.claude' / 'CLAUDE.md'


def load_claude_md(path: Path) -> dict:
    """Load CLAUDE.md into structured dict by category."""
    result = {cat: [] for cat in CATEGORIES}

    if not path.exists():
        return result

    try:
        content = path.read_text()
    except IOError:
        return result

    current_category = None

    for line in content.split('\n'):
        # Check for category header
        for cat in CATEGORIES:
            if line.strip().startswith(f'## {cat}'):
                current_category = cat
                break
        else:
            # Not a header, add to current category
            if current_category and line.strip().startswith('- '):
                result[current_category].append(line.strip()[2:])

    return result


def save_claude_md(path: Path, knowledge: dict, header: str = "# Knowledge"):
    """Save structured knowledge dict to CLAUDE.md."""
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [header, '']

    for cat in CATEGORIES:
        items = knowledge.get(cat, [])
        if items:
            lines.append(f'## {cat}')
            for item in items:
                lines.append(f'- {item}')
            lines.append('')

    path.write_text('\n'.join(lines))


def add_knowledge(item: str, category: str, scope: str = 'global') -> bool:
    """Add a knowledge item to the appropriate CLAUDE.md.

    Args:
        item: The knowledge entry text
        category: One of CATEGORIES
        scope: 'global' for ~/.claude/CLAUDE.md, 'project' for .claude/CLAUDE.md
    """
    if category not in CATEGORIES:
        return False

    if scope not in ('global', 'project'):
        return False

    if scope == 'global':
        path = GLOBAL_CLAUDE_MD
        header = '# Global Knowledge'
    else:
        path = get_project_claude_md()
        header = '# Project Knowledge'

    knowledge = load_claude_md(path)

    # Avoid duplicates
    if item not in knowledge[category]:
        knowledge[category].append(item)
        save_claude_md(path, knowledge, header)

    return True


def get_all_knowledge() -> dict:
    """Load and merge global + project knowledge."""
    global_k = load_claude_md(GLOBAL_CLAUDE_MD)
    project_k = load_claude_md(get_project_claude_md())

    # Merge (project items come after global)
    merged = {}
    for cat in CATEGORIES:
        merged[cat] = global_k.get(cat, []) + project_k.get(cat, [])

    return merged


def format_knowledge_summary(knowledge: dict) -> str:
    """Format knowledge for SessionStart display."""
    lines = []
    for cat in CATEGORIES:
        items = knowledge.get(cat, [])
        if items:
            lines.append(f"  - {cat}: {len(items)} items")
    return '\n'.join(lines) if lines else "  (none)"
