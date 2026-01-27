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
  stats            - Show skill and learning usage statistics
  export [file]    - Export index to file (default: recall-backup.json)
  import <file>    - Import index from file
  reset            - Reset to empty index (keeps backup)
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


def get_session_details_dir(project_folder: str) -> Path:
    """Get the directory for storing session detail files."""
    return Path.home() / '.claude' / 'projects' / project_folder / 'recall-sessions'


def load_session_details(project_folder: str, session_id: str) -> dict:
    """Load full session details from separate file.

    Returns None if detail file doesn't exist.
    """
    details_file = get_session_details_dir(project_folder) / f"{session_id}.json"
    if details_file.exists():
        try:
            with open(details_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return None


def list_all_project_indices() -> list:
    """List all project folders with recall indices."""
    projects_dir = Path.home() / '.claude' / 'projects'
    if not projects_dir.exists():
        return []

    projects = []
    for proj_dir in projects_dir.iterdir():
        if proj_dir.is_dir():
            index_file = proj_dir / 'recall-index.json'
            if index_file.exists():
                projects.append(proj_dir.name)
    return projects


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

def save_index(project_folder: str, index: dict):
    """Save index back to disk."""
    index_file = Path.home() / '.claude' / 'projects' / project_folder / 'recall-index.json'
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2, default=str)

def get_index_path(project_folder: str) -> Path:
    """Get the path to the recall index file."""
    return Path.home() / '.claude' / 'projects' / project_folder / 'recall-index.json'

def export_index(index: dict, project_folder: str, export_path: str = None):
    """Export index to a file for backup/testing."""
    if not index:
        print("No index to export.")
        return

    # Default export path
    if not export_path:
        export_path = f"recall-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

    # Make path absolute if relative
    export_file = Path(export_path)
    if not export_file.is_absolute():
        export_file = Path.cwd() / export_file

    # Add metadata
    export_data = {
        'exported_at': datetime.now().isoformat(),
        'project_folder': project_folder,
        'index': index
    }

    with open(export_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"## Exported Recall Index")
    print(f"**File:** `{export_file}`")
    print()
    print("Contents:")
    print(f"  - {len(index.get('sessions', {}))} sessions")
    print(f"  - {len(index.get('learnings', []))} learnings")
    print(f"  - {len(index.get('failure_patterns', {}))} failure pattern categories")
    skills = index.get('usage', {}).get('skills', {})
    print(f"  - {len(skills)} skills tracked")
    print()
    print("Use `/recall import <file>` to restore this backup.")

def import_index(project_folder: str, import_path: str):
    """Import index from a backup file."""
    import_file = Path(import_path)
    if not import_file.is_absolute():
        import_file = Path.cwd() / import_file

    if not import_file.exists():
        print(f"Error: File not found: {import_file}")
        return

    try:
        with open(import_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}")
        return

    # Handle both direct index and wrapped export format
    if 'index' in data and 'exported_at' in data:
        # Wrapped export format
        index = data['index']
        print(f"Importing from backup created: {data.get('exported_at', 'unknown')}")
    else:
        # Direct index format
        index = data

    # Backup current index first
    current_index_path = get_index_path(project_folder)
    if current_index_path.exists():
        backup_path = current_index_path.with_suffix('.json.bak')
        import shutil
        shutil.copy(current_index_path, backup_path)
        print(f"Current index backed up to: {backup_path}")

    # Save imported index
    save_index(project_folder, index)

    print()
    print(f"## Imported Recall Index")
    print(f"**From:** `{import_file}`")
    print()
    print("Imported:")
    print(f"  - {len(index.get('sessions', {}))} sessions")
    print(f"  - {len(index.get('learnings', []))} learnings")
    print(f"  - {len(index.get('failure_patterns', {}))} failure pattern categories")

def reset_index(index: dict, project_folder: str):
    """Reset index to empty state, keeping a backup."""
    index_path = get_index_path(project_folder)

    # Backup current index
    if index and index_path.exists():
        backup_path = f"recall-backup-pre-reset-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        export_index(index, project_folder, backup_path)
        print()

    # Create empty index
    empty_index = {
        'version': 2,
        'project': project_folder,
        'sessions': {},
        'failure_patterns': {},
        'learnings': [],
        'usage': {
            'skills': {},
            'learnings_shown': {}
        }
    }

    save_index(project_folder, empty_index)

    print("## Index Reset")
    print("Created empty index. Previous data backed up above.")
    print()
    print("The index will rebuild as you use sessions.")
    print("Use `/recall import <file>` to restore from backup.")

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

def show_stats(index: dict, project_folder: str):
    """Show skill and learning usage statistics."""
    print("## Recall Usage Statistics")
    print()

    usage = index.get('usage', {})

    # Skill usage
    skills = usage.get('skills', {})
    if skills:
        print("### Skill Invocations")
        print()
        sorted_skills = sorted(skills.items(), key=lambda x: x[1].get('count', 0), reverse=True)
        for skill_name, data in sorted_skills:
            count = data.get('count', 0)
            last_used = data.get('last_used', 'never')[:10]
            sessions = len(data.get('sessions', []))
            print(f"  **{skill_name}**: {count} uses across {sessions} sessions (last: {last_used})")
        print()
    else:
        print("### Skill Invocations")
        print("  No skill usage tracked yet.")
        print()

    # Learning displays
    learnings_shown = usage.get('learnings_shown', {})
    if learnings_shown:
        print("### Learnings Displayed")
        print()
        sorted_learnings = sorted(learnings_shown.items(), key=lambda x: x[1].get('count', 0), reverse=True)
        for learning_key, data in sorted_learnings:
            count = data.get('count', 0)
            last_shown = data.get('last_shown', 'never')[:10]
            print(f"  **{learning_key}**: shown {count} times (last: {last_shown})")
        print()
    else:
        print("### Learnings Displayed")
        print("  No learning displays tracked yet.")
        print()

    # Summary
    total_skills = sum(s.get('count', 0) for s in skills.values())
    total_learnings = sum(l.get('count', 0) for l in learnings_shown.values())
    print("### Summary")
    print(f"  Total skill invocations: {total_skills}")
    print(f"  Total learning displays: {total_learnings}")
    print(f"  Unique skills used: {len(skills)}")
    print(f"  Unique learnings shown: {len(learnings_shown)}")

    # Identify unused learnings
    all_learnings = index.get('learnings', [])
    learning_keys = set()
    for l in all_learnings:
        if isinstance(l, dict):
            key = f"{l.get('category', 'general')}/{l.get('title', 'Unknown')}"
            learning_keys.add(key)

    shown_keys = set(learnings_shown.keys())
    unused = learning_keys - shown_keys
    if unused:
        print()
        print("### Unused Learnings (never displayed)")
        for key in sorted(unused):
            print(f"  - {key}")


def show_failures(index: dict, project_folder: str):
    """Show failure patterns across sessions."""
    print("## Failure Patterns Across Sessions")
    print()

    failure_patterns = index.get('failure_patterns', {})

    # Track that we're showing learnings (for usage stats)
    learnings = index.get('learnings', [])
    learnings_to_track = []

    # Always show learnings first if available
    if learnings:
        print("## Learnings & Best Practices")
        print()
        for learning in learnings:
            if isinstance(learning, dict):
                cat = learning.get('category', 'general')
                title = learning.get('title', 'Unknown')
                desc = learning.get('description', '')
                solution = learning.get('solution', '')

                # Track this learning was shown
                learnings_to_track.append(f"{cat}/{title}")

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

        # Update usage stats for displayed learnings
        if learnings_to_track:
            if 'usage' not in index:
                index['usage'] = {'skills': {}, 'learnings_shown': {}}
            if 'learnings_shown' not in index['usage']:
                index['usage']['learnings_shown'] = {}

            now = datetime.now().isoformat()
            for learning_key in learnings_to_track:
                if learning_key not in index['usage']['learnings_shown']:
                    index['usage']['learnings_shown'][learning_key] = {'count': 0, 'first_shown': now}
                index['usage']['learnings_shown'][learning_key]['count'] += 1
                index['usage']['learnings_shown'][learning_key]['last_shown'] = now

            # Save updated index
            save_index(project_folder, index)

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
    """Show previous session details.

    Uses tiered storage: loads full details from session file if available.
    """
    # Try index first to identify the previous session
    if index and index.get('sessions'):
        sorted_sessions = sorted(
            index['sessions'].items(),
            key=lambda x: x[1].get('date', ''),
            reverse=True
        )

        # Skip current (first), show previous
        if len(sorted_sessions) >= 2:
            session_id, session_summary = sorted_sessions[1]

            # Try to load full details from separate file
            details = load_session_details(project_folder, session_id)

            print("## Previous Session")
            print(f"**Date:** {format_date(session_summary.get('date', ''))}")
            print(f"**Session:** {session_id[:8]}...")
            print(f"**Stats:** {session_summary.get('message_count', 0)} messages, {session_summary.get('command_count', 0)} commands, {session_summary.get('failure_count', 0)} failures")
            print()

            # Use details file if available (has full content)
            if details:
                print("### User Messages:")
                for i, msg in enumerate(details.get('user_messages', [])[:15], 1):
                    content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
                    clean_msg = content.replace('\n', ' ').strip()[:200]
                    if clean_msg:
                        print(f"{i}. {clean_msg}")

                # Show failures if any
                failures = details.get('failures', [])
                if failures:
                    print()
                    print("### Failures:")
                    for f in failures[:5]:
                        cmd = f.get('command', '')[:80]
                        error = f.get('error', '')[:150]
                        print(f"  - `{cmd}`")
                        print(f"    {error}")
            else:
                # Fallback to summary from index
                print("### Summary:")
                print(f"  {session_summary.get('summary', 'No summary')}")
                print()
                print("_(Full details not available - session was indexed before tiered storage)_")
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
    """Search for term across sessions.

    Searches both index summaries and detail files for comprehensive results.
    """
    print(f"## Searching for: '{search_term}'")
    print()

    found = False
    search_lower = search_term.lower()

    # Search sessions - try detail files first, fall back to index
    if index and index.get('sessions'):
        sorted_sessions = sorted(
            index['sessions'].items(),
            key=lambda x: x[1].get('date', ''),
            reverse=True
        )

        for session_id, session_summary in sorted_sessions[:20]:  # Search last 20 sessions
            matches = []

            # Try to load full details
            details = load_session_details(project_folder, session_id)

            if details:
                # Search in detail file (more content)
                for msg in details.get('user_messages', []):
                    content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
                    if search_lower in content.lower():
                        matches.append(content)
            else:
                # Fall back to summary in index
                summary = session_summary.get('summary', '')
                if search_lower in summary.lower():
                    matches.append(summary)

            if matches:
                found = True
                print(f"### {format_date(session_summary.get('date', ''))} ({session_id[:8]}...)")
                for match in matches[:3]:
                    print(f"  > {match[:200]}...")
                print()

        # Also search failure patterns
        for pattern, failures in index.get('failure_patterns', {}).items():
            for f in failures:
                if search_lower in f.get('command', '').lower() or search_lower in f.get('error', '').lower():
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

    if found:
        return

    # No local results - search other projects
    print(f"No results in current project ({project_folder[-30:]}).")
    print()

    all_projects = list_all_project_indices()
    other_projects = [p for p in all_projects if p != project_folder]

    if not other_projects:
        print("No other projects to search.")
        return

    global_results = []

    for proj in other_projects:
        proj_index = load_index(proj)
        if not proj_index:
            continue

        proj_sessions = proj_index.get('sessions', {})
        matches_in_proj = []

        for session_id, session_summary in proj_sessions.items():
            summary = session_summary.get('summary', '')
            if search_lower in summary.lower():
                matches_in_proj.append({
                    'session_id': session_id,
                    'date': session_summary.get('date', ''),
                    'summary': summary
                })

        if matches_in_proj:
            global_results.append({
                'project': proj,
                'matches': matches_in_proj
            })

    if global_results:
        print(f"Found matches in {len(global_results)} other project(s):")
        print()
        for result in global_results:
            proj_name = result['project'].split('-')[-1] if '-' in result['project'] else result['project']
            print(f"### {proj_name} ({len(result['matches'])} matches)")
            for match in result['matches'][:3]:
                print(f"  > [{match['date'][:10]}] {match['summary'][:150]}...")
            if len(result['matches']) > 3:
                print(f"  ... and {len(result['matches']) - 3} more")
            print()
    else:
        print(f"No matches found for '{search_term}' in any project.")

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
        cmd_parts = command.split(None, 1)  # Split into command and argument
        cmd_name = cmd_parts[0].lower()
        cmd_arg = cmd_parts[1] if len(cmd_parts) > 1 else None

        if cmd_name == 'last':
            show_last_session(index, sessions, project_folder)
        elif cmd_name == 'failures':
            if index:
                show_failures(index, project_folder)
            else:
                print("No index available. Run a session to completion to build the index.")
        elif cmd_name == 'stats':
            if index:
                show_stats(index, project_folder)
            else:
                print("No index available. Run a session to completion to build the index.")
        elif cmd_name == 'export':
            if index:
                export_index(index, project_folder, cmd_arg)
            else:
                print("No index available to export.")
        elif cmd_name == 'import':
            if cmd_arg:
                import_index(project_folder, cmd_arg)
            else:
                print("Usage: /recall import <file>")
                print("Example: /recall import recall-backup.json")
        elif cmd_name == 'reset':
            reset_index(index, project_folder)
        elif cmd_name == 'cleanup':
            show_cleanup_analysis(index, sessions, project_folder)
        elif cmd_name == 'learn':
            # Run the learn script
            learn_script = Path(__file__).parent / 'recall-learn.py'
            if learn_script.exists():
                import subprocess
                args = ['python3', str(learn_script)]
                if cmd_arg:
                    args.append(cmd_arg)
                subprocess.run(args)
            else:
                print("Learn script not found. Check installation.")
        elif cmd_name == 'knowledge':
            # Show current knowledge
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
                from knowledge import get_all_knowledge, GLOBAL_CLAUDE_MD, get_project_claude_md

                print("## Current Knowledge")
                print()
                print(f"**Global:** `{GLOBAL_CLAUDE_MD}`")
                print(f"**Project:** `{get_project_claude_md()}`")
                print()

                knowledge = get_all_knowledge()
                for cat, items in knowledge.items():
                    if items:
                        print(f"### {cat}")
                        for item in items:
                            print(f"  - {item}")
                        print()

                if not any(knowledge.values()):
                    print("No knowledge loaded yet.")
                    print("Use `/recall learn` to review and approve pending learnings.")
            except ImportError as e:
                print(f"Knowledge library not found: {e}")
        else:
            # Search
            search_sessions(command, index, sessions, project_folder)
    else:
        list_sessions(index, sessions, project_folder)

if __name__ == '__main__':
    main()
