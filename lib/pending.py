#!/usr/bin/env python3
"""
Pending learnings storage.
Manages proposals awaiting user approval.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

PENDING_FILE = Path.home() / '.claude' / 'pending-learnings.json'


def load_pending() -> dict:
    """Load pending learnings."""
    if not PENDING_FILE.exists():
        return {'version': 1, 'pending': []}

    try:
        return json.loads(PENDING_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {'version': 1, 'pending': []}


def save_pending(data: dict):
    """Save pending learnings."""
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_text(json.dumps(data, indent=2, default=str))


def add_pending(
    category: str,
    title: str,
    content: str,
    session_id: str,
    session_summary: str,
    project: str,
    suggested_scope: str = 'global',
    source: str = 'heuristic'
) -> str:
    """Add a pending learning. Returns the ID."""
    data = load_pending()

    # Check for duplicates (same content)
    for existing in data['pending']:
        if existing.get('content') == content:
            return existing.get('id', '')

    learning_id = str(uuid.uuid4())[:8]

    data['pending'].append({
        'id': learning_id,
        'timestamp': datetime.now().isoformat(),
        'session_id': session_id,
        'session_summary': session_summary[:100],
        'project': project,
        'category': category,
        'title': title,
        'content': content,
        'suggested_scope': suggested_scope,
        'source': source
    })

    save_pending(data)
    return learning_id


def remove_pending(learning_id: str) -> bool:
    """Remove a pending learning by ID."""
    data = load_pending()
    original_len = len(data['pending'])
    data['pending'] = [p for p in data['pending'] if p.get('id') != learning_id]

    if len(data['pending']) < original_len:
        save_pending(data)
        return True
    return False


def get_pending_count() -> int:
    """Get count of pending learnings."""
    data = load_pending()
    return len(data.get('pending', []))


def clear_pending():
    """Clear all pending learnings."""
    save_pending({'version': 1, 'pending': []})
