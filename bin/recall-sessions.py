#!/usr/bin/env python3
"""
Recall past Claude Code sessions for a project.
Uses unified index for fast queries, falls back to JSONL parsing.

Usage:
  recall-sessions.py <project_path> [command]

Commands:
  (none)           - List recent sessions
  last             - Show previous session details
  failures         - Show failure patterns and learnings
  cleanup          - Analyze index for cleanup opportunities
  <search_term>    - Search for term in past sessions
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import re

def get_project_folder(cwd: str) -> str:
    """Convert working directory to Claude's project folder naming convention."""
    return cwd.replace('/', '-')

def load_index(project_folder: str) -> dict:
    """Load recall index if it exists."""
    index_file = Path.home() / '.claude' / 'projects' / project_folder / 'recall-index.json'
    if index_file.exists():
        try:
            with open(index_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return None

def find_session_files(project_folder: str) -> list:
    """Find all session files for a project, sorted by modification time."""
    claude_dir = Path.home() / '.claude' / 'projects' / project_folder
    if not claude_dir.exists():
        return []

    sessions = []
    for f in claude_dir.glob('*.jsonl'):
        if not f.name.startswith('agent-'):
            sessions.append(f)

    sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return sessions

def parse_session(session_file: Path, search_term: str = None) -> dict:
    """Parse a session file and extract key information (fallback when no index)."""
    result = {
        'file': session_file.name,
        'session_id': session_file.stem,
        'date': datetime.fromtimestamp(session_file.stat().st_mtime),
        'user_messages': [],
        'matches': []
    }

    try:
        with open(session_file, 'r') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get('type') == 'user':
                        msg = obj.get('message', {})
                        if isinstance(msg, dict):
                            content = msg.get('content', '')
                            if isinstance(content, str) and content:
                                if not content.startswith('<'):
                                    result['user_messages'].append(content[:500])
                                    if search_term and search_term.lower() in content.lower():
                                        result['matches'].append(content[:300])
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        result['error'] = str(e)

    return result

def format_date(date_input) -> str:
    """Format date consistently."""
    if isinstance(date_input, str):
        try:
            dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_input[:16]
    elif isinstance(date_input, datetime):
        return date_input.strftime('%Y-%m-%d %H:%M')
    return str(date_input)

def show_failures(index: dict, project_folder: str):
    """Show failure patterns across sessions."""
    print("## Failure Patterns Across Sessions")
    print()

    failure_patterns = index.get('failure_patterns', {})

    # Always show learnings first if available
    learnings = index.get('learnings', [])
    if learnings:
        print("## Learnings & Best Practices")
        print()
        for learning in learnings:
            if isinstance(learning, dict):
                cat = learning.get('category', 'general')
                title = learning.get('title', 'Unknown')
                desc = learning.get('description', '')
                solution = learning.get('solution', '')
                print(f"### [{cat}] {title}")
                if desc:
                    print(f"  {desc}")
                if solution:
                    print(f"  **Fix:** {solution}")
                tools = learning.get('tools', {})
                if tools:
                    print("  **Tools:**")
                    for name, usage in tools.items():
                        print(f"    - {name}: {usage}")
                examples = learning.get('examples', [])
                if examples:
                    print("  **Examples:**")
                    for ex in examples[:3]:
                        print(f"    `{ex}`")
                print()
            else:
                print(f"  - {learning}")
        print()

    if not failure_patterns:
        if not learnings:
            print("No failure patterns or learnings recorded yet.")
        return

    # Sort by frequency
    sorted_patterns = sorted(
        failure_patterns.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )

    for pattern, failures in sorted_patterns:
        pattern_name = pattern.replace('_', ' ').title()
        print(f"### {pattern_name} ({len(failures)} occurrences)")
        print()

        # Show recent failures of this type
        for f in failures[-5:]:  # Last 5
            date = f.get('date', 'unknown')[:10]
            cmd = f.get('command', 'unknown')[:60]
            error = f.get('error', '')[:100]
            print(f"  **{date}**: `{cmd}`")
            if error:
                print(f"    Error: {error}...")
        print()


def show_cleanup_analysis(index: dict, sessions: list, project_folder: str):
    """Analyze recall data and suggest cleanup actions."""
    print("## Recall Cleanup Analysis")
    print()

    index_file = Path.home() / '.claude' / 'projects' / project_folder / 'recall-index.json'
    print(f"**Index:** `{index_file}`")
    print()

    if not index:
        print("No index found. Nothing to clean.")
        return

    # Analyze sessions
    sessions_data = index.get('sessions', {})
    noise_sessions = []
    sensitive_sessions = []
    useful_sessions = []

    sensitive_patterns = ['BEGIN OPENSSH', 'BEGIN RSA', 'API_KEY=', 'SECRET=', 'TOKEN=', 'password']

    for sid, session in sessions_data.items():
        msg_count = session.get('message_count', 0)
        messages = session.get('user_messages', [])

        # Check for sensitive data
        has_sensitive = False
        for msg in messages:
            content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
            for pattern in sensitive_patterns:
                if pattern.lower() in content.lower():
                    has_sensitive = True
                    break

        if has_sensitive:
            sensitive_sessions.append((sid, session))
        elif msg_count < 3:
            noise_sessions.append((sid, session))
        else:
            useful_sessions.append((sid, session))

    # Report
    print(f"### Sessions: {len(sessions_data)} total")
    print(f"  - Useful: {len(useful_sessions)}")
    print(f"  - Low-value (< 3 msgs): {len(noise_sessions)}")
    print(f"  - **Contains sensitive data: {len(sensitive_sessions)}** {'⚠️  DELETE THESE' if sensitive_sessions else ''}")
    print()

    if sensitive_sessions:
        print("### ⚠️  Sessions with sensitive data:")
        for sid, session in sensitive_sessions:
            print(f"  - `{sid[:8]}...` ({format_date(session.get('date', ''))})")
        print()

    if noise_sessions:
        print("### Low-value sessions (candidates for removal):")
        for sid, session in noise_sessions[:5]:
            summary = session.get('summary', 'No summary')[:60]
            print(f"  - `{sid[:8]}...`: {summary}")
        if len(noise_sessions) > 5:
            print(f"  ... and {len(noise_sessions) - 5} more")
        print()

    # Analyze failure patterns
    failure_patterns = index.get('failure_patterns', {})
    total_failures = sum(len(v) for v in failure_patterns.values())
    print(f"### Failure Patterns: {len(failure_patterns)} categories, {total_failures} total")
    if total_failures > 20:
        print("  Consider clearing noise - keep only actionable patterns")
    print()

    # Check learnings
    learnings = index.get('learnings', [])
    print(f"### Learnings: {len(learnings)}")
    if learnings:
        categories = set(l.get('category', 'unknown') for l in learnings if isinstance(l, dict))
        print(f"  Categories: {', '.join(sorted(categories))}")
    else:
        print("  ⚠️  No learnings defined - consider adding best practices")
    print()

    # Disk usage
    claude_dir = Path.home() / '.claude' / 'projects' / project_folder
    total_size = 0
    jsonl_files = list(claude_dir.glob('*.jsonl'))
    for f in jsonl_files:
        total_size += f.stat().st_size

    print(f"### Disk Usage")
    print(f"  - {len(jsonl_files)} session files")
    print(f"  - {total_size / 1024 / 1024:.1f} MB total")
    if total_size > 50 * 1024 * 1024:
        print("  ⚠️  Consider deleting old .jsonl files")
    print()

    print("---")
    print("To clean: Read the index file, remove noise, add learnings, write back.")
    print("Key learnings to ensure: BB tools at ~/code/kureapp-tools/bitbucket/")

def show_last_session(index: dict, sessions: list, project_folder: str):
    """Show previous session details."""
    # Try index first
    if index and index.get('sessions'):
        sorted_sessions = sorted(
            index['sessions'].items(),
            key=lambda x: x[1].get('date', ''),
            reverse=True
        )

        # Skip current (first), show previous
        if len(sorted_sessions) >= 2:
            session_id, session = sorted_sessions[1]
            print("## Previous Session")
            print(f"**Date:** {format_date(session.get('date', ''))}")
            print(f"**Session:** {session_id[:8]}...")
            print(f"**Stats:** {session.get('message_count', 0)} messages, {session.get('command_count', 0)} commands, {session.get('failure_count', 0)} failures")
            print()
            print("### User Messages:")
            for i, msg in enumerate(session.get('user_messages', [])[:15], 1):
                content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
                clean_msg = content.replace('\n', ' ').strip()[:200]
                if clean_msg:
                    print(f"{i}. {clean_msg}")

            # Show failures if any
            failures = session.get('failures', [])
            if failures:
                print()
                print("### Failures:")
                for f in failures[:5]:
                    cmd = f.get('command', '')[:60]
                    error = f.get('error', '')[:100]
                    print(f"  - `{cmd}`")
                    print(f"    {error}")
            return

    # Fallback to JSONL parsing
    if len(sessions) < 2:
        print("No previous session found (only current session exists)")
        return

    session = sessions[1]
    data = parse_session(session)

    print("## Previous Session")
    print(f"**Date:** {format_date(data['date'])}")
    print(f"**File:** {data['file']}")
    print()
    print("### User Messages:")
    for i, msg in enumerate(data['user_messages'][:15], 1):
        clean_msg = msg.replace('\n', ' ').strip()
        if clean_msg and not clean_msg.startswith('<'):
            print(f"{i}. {clean_msg[:200]}")

def search_sessions(search_term: str, index: dict, sessions: list, project_folder: str):
    """Search for term across sessions."""
    print(f"## Searching for: '{search_term}'")
    print()

    found = False

    # Search index first
    if index and index.get('sessions'):
        for session_id, session in index['sessions'].items():
            messages = session.get('user_messages', [])
            matches = []

            for msg in messages:
                content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
                if search_term.lower() in content.lower():
                    matches.append(content)

            if matches:
                found = True
                print(f"### {format_date(session.get('date', ''))} ({session_id[:8]}...)")
                for match in matches[:3]:
                    print(f"  > {match[:200]}...")
                print()

        # Also search failure patterns
        for pattern, failures in index.get('failure_patterns', {}).items():
            for f in failures:
                if search_term.lower() in f.get('command', '').lower() or search_term.lower() in f.get('error', '').lower():
                    if not found:
                        print("### In Failure Patterns:")
                    found = True
                    print(f"  > [{pattern}] `{f.get('command', '')[:60]}`")

        if found:
            return

    # Fallback to JSONL search
    for session in sessions[:10]:
        data = parse_session(session, search_term)
        if data['matches']:
            found = True
            print(f"### {format_date(data['date'])} ({data['file'][:8]}...)")
            for match in data['matches'][:3]:
                print(f"  > {match[:200]}...")
            print()

    if not found:
        print(f"No matches found for '{search_term}' in recent sessions.")

def list_sessions(index: dict, sessions: list, project_folder: str):
    """List recent sessions with summaries."""
    print("## Recent Sessions")
    print()

    # Use index if available
    if index and index.get('sessions'):
        sorted_sessions = sorted(
            index['sessions'].items(),
            key=lambda x: x[1].get('date', ''),
            reverse=True
        )

        for i, (session_id, session) in enumerate(sorted_sessions[:7]):
            current = " (current)" if i == 0 else ""
            date = format_date(session.get('date', ''))
            summary = session.get('summary', 'No summary')[:150]
            stats = f"[{session.get('message_count', 0)} msgs, {session.get('failure_count', 0)} fails]"

            print(f"**{date}**{current} {stats}")
            print(f"  {summary}")
            print()
        return

    # Fallback to JSONL parsing
    for i, session in enumerate(sessions[:7]):
        data = parse_session(session)
        messages = data['user_messages'][:5]
        summary = "No user messages found"
        for msg in messages:
            if len(msg) > 20:
                summary = msg[:150] + "..." if len(msg) > 150 else msg
                break

        current = " (current)" if i == 0 else ""
        print(f"**{format_date(data['date'])}**{current}")
        print(f"  {summary}")
        print()

def main():
    if len(sys.argv) < 2:
        print("Usage: recall-sessions.py <project_path> [search_term|last|failures]")
        sys.exit(1)

    cwd = sys.argv[1]
    command = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else None

    project_folder = get_project_folder(cwd)
    sessions = find_session_files(project_folder)
    index = load_index(project_folder)

    if not sessions and not index:
        print(f"No sessions found for project: {cwd}")
        print(f"Looking in: ~/.claude/projects/{project_folder}")
        sys.exit(0)

    # Handle commands
    if command:
        cmd_lower = command.lower()

        if cmd_lower == 'last':
            show_last_session(index, sessions, project_folder)
        elif cmd_lower == 'failures':
            if index:
                show_failures(index, project_folder)
            else:
                print("No index available. Run a session to completion to build the index.")
        elif cmd_lower == 'cleanup':
            show_cleanup_analysis(index, sessions, project_folder)
        else:
            # Search
            search_sessions(command, index, sessions, project_folder)
    else:
        list_sessions(index, sessions, project_folder)

if __name__ == '__main__':
    main()
