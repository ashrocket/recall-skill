#!/usr/bin/env python3
"""
SessionStart hook: Surface relevant context from past sessions.
Shows recent session summary and any recurring failure patterns.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

def get_project_folder(cwd: str) -> str:
    """Convert working directory to Claude's project folder naming convention."""
    return cwd.replace('/', '-')

def load_index(project_folder: str) -> dict:
    """Load existing index."""
    index_file = Path.home() / '.claude' / 'projects' / project_folder / 'recall-index.json'

    if index_file.exists():
        try:
            with open(index_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return None

def format_time_ago(date_str: str) -> str:
    """Format date as relative time."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        now = datetime.now()
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)

        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
    except:
        return date_str[:10]

def main():
    # Get project path
    cwd = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()
    if len(sys.argv) > 1:
        cwd = sys.argv[1]

    project_folder = get_project_folder(cwd)
    index = load_index(project_folder)

    if not index or not index.get('sessions'):
        # No history yet - that's fine, silent exit
        sys.exit(0)

    sessions = index.get('sessions', {})
    failure_patterns = index.get('failure_patterns', {})

    # Sort sessions by date
    sorted_sessions = sorted(
        sessions.items(),
        key=lambda x: x[1].get('date', ''),
        reverse=True
    )

    # Only show context if there's something meaningful
    if not sorted_sessions:
        sys.exit(0)

    output = []
    output.append("## Session Context from /recall")
    output.append("")

    # Show last session summary
    last_session_id, last_session = sorted_sessions[0]
    time_ago = format_time_ago(last_session.get('date', ''))

    output.append(f"**Last session** ({time_ago}): {last_session.get('summary', 'No summary')[:150]}")

    # Show stats
    total_sessions = len(sessions)
    total_failures = sum(s.get('failure_count', 0) for s in sessions.values())

    if total_sessions > 1:
        output.append(f"**History**: {total_sessions} sessions, {total_failures} total failures")

    # Show knowledge summary (v2)
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
        from knowledge import get_all_knowledge, format_knowledge_summary
        from pending import get_pending_count

        knowledge = get_all_knowledge()
        has_knowledge = any(knowledge.values())

        if has_knowledge:
            output.append("")
            output.append("**Knowledge loaded:**")
            output.append(format_knowledge_summary(knowledge))

        pending = get_pending_count()
        if pending > 0:
            output.append("")
            output.append(f"**Pending:** {pending} learnings awaiting review (`/recall learn`)")
    except ImportError:
        pass  # Knowledge library not installed

    # Show recurring failure patterns (if any)
    significant_patterns = []
    for pattern, failures in failure_patterns.items():
        if len(failures) >= 2:  # Pattern occurred multiple times
            significant_patterns.append((pattern, len(failures), failures[-1]))

    if significant_patterns:
        output.append("")
        output.append("**Recurring issues** (use `/recall failures` for details):")
        for pattern, count, last_failure in sorted(significant_patterns, key=lambda x: -x[1])[:3]:
            pattern_name = pattern.replace('_', ' ').title()
            output.append(f"  - {pattern_name}: {count}x (last: `{last_failure.get('command', 'unknown')[:50]}...`)")

    # Show incomplete tasks hint from last session
    last_messages = last_session.get('user_messages', [])
    if last_messages:
        last_msg = last_messages[-1].get('content', '')
        if any(word in last_msg.lower() for word in ['todo', 'next', 'later', 'continue', 'finish']):
            output.append("")
            output.append(f"**Possible continuation**: \"{last_msg[:100]}...\"")

    output.append("")
    output.append("_Use `/recall` to search past sessions, `/recall last` for full previous session_")
    output.append("")

    print('\n'.join(output))

if __name__ == '__main__':
    main()
