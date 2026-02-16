#!/usr/bin/env python3
"""
Pending learnings helper for the recall system.
Thin wrapper around knowledge.py for backward compatibility.
"""

from pathlib import Path
import sys

# Ensure knowledge module is importable
sys.path.insert(0, str(Path(__file__).parent))

from knowledge import get_pending_learnings, get_project_folder


def get_pending_count(project_folder: str = None) -> int:
    """Get count of pending learnings awaiting review."""
    pending = get_pending_learnings(project_folder)
    return len(pending)
