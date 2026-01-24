#!/usr/bin/env python3
"""
SessionEnd hook: Index session data for /recall.
Creates a unified index with user messages, commands, and failure patterns.
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

def find_current_session(project_folder: str) -> Path:
    """Find the most recent session file."""
    claude_dir = Path.home() / '.claude' / 'projects' / project_folder
    if not claude_dir.exists():
        return None

    sessions = []
    for f in claude_dir.glob('*.jsonl'):
        if not f.name.startswith('agent-'):
            sessions.append(f)

    if not sessions:
        return None

    sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return sessions[0]

def parse_session_full(session_file: Path) -> dict:
    """Parse session file and extract comprehensive data."""
    result = {
        'session_id': session_file.stem,
        'date': datetime.fromtimestamp(session_file.stat().st_mtime).isoformat(),
        'user_messages': [],
        'commands': [],
        'failures': [],
        'failure_patterns': {},
        'topics': set(),
        'summary': ''
    }

    try:
        with open(session_file, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            try:
                obj = json.loads(line)

                # Extract user messages
                if obj.get('type') == 'user':
                    msg = obj.get('message', {})
                    if isinstance(msg, dict):
                        content = msg.get('content', '')
                        if isinstance(content, str) and content and not content.startswith('<'):
                            result['user_messages'].append({
                                'index': i,
                                'content': content[:500],
                                'timestamp': obj.get('timestamp', '')
                            })
                            # Extract potential topics (capitalized words, technical terms)
                            words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b|\b[a-z]+(?:_[a-z]+)+\b', content)
                            result['topics'].update(words[:10])

                # Extract tool calls (bash commands)
                if obj.get('type') == 'assistant':
                    msg = obj.get('message', {})
                    if isinstance(msg, dict):
                        content = msg.get('content', [])
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get('type') == 'tool_use':
                                    if block.get('name') == 'Bash':
                                        cmd_input = block.get('input', {})
                                        command = cmd_input.get('command', '')
                                        if command:
                                            result['commands'].append({
                                                'index': i,
                                                'tool_id': block.get('id', ''),
                                                'command': command[:300]
                                            })

                # Extract tool results (to find failures)
                if obj.get('type') == 'user':
                    msg = obj.get('message', {})
                    if isinstance(msg, dict):
                        content = msg.get('content', [])
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get('type') == 'tool_result':
                                    tool_content = block.get('content', '')
                                    is_error = block.get('is_error', False)

                                    # Check for error indicators
                                    if is_error or (isinstance(tool_content, str) and any(err in tool_content.lower() for err in ['error:', 'failed', 'exception', 'traceback', 'permission denied', 'not found', 'command not found'])):
                                        tool_id = block.get('tool_use_id', '')
                                        # Find the command that caused this
                                        for cmd in result['commands']:
                                            if cmd.get('tool_id') == tool_id:
                                                error_msg = tool_content[:500] if isinstance(tool_content, str) else str(tool_content)[:500]
                                                result['failures'].append({
                                                    'command': cmd['command'],
                                                    'error': error_msg,
                                                    'index': i
                                                })

                                                # Categorize failure pattern
                                                pattern = categorize_error(error_msg)
                                                if pattern:
                                                    if pattern not in result['failure_patterns']:
                                                        result['failure_patterns'][pattern] = []
                                                    result['failure_patterns'][pattern].append({
                                                        'command': cmd['command'][:100],
                                                        'error': error_msg[:200]
                                                    })
                                                break

            except json.JSONDecodeError:
                continue
    except Exception as e:
        result['error'] = str(e)

    # Generate summary from first few user messages
    if result['user_messages']:
        first_msgs = [m['content'] for m in result['user_messages'][:3]]
        result['summary'] = ' | '.join(m[:100] for m in first_msgs)

    # Convert topics set to list for JSON serialization
    result['topics'] = list(result['topics'])[:20]

    return result

def categorize_error(error_msg: str) -> str:
    """Categorize error into a pattern type."""
    error_lower = error_msg.lower()

    patterns = [
        ('permission_denied', ['permission denied', 'access denied', 'eacces']),
        ('not_found', ['not found', 'no such file', 'enoent', 'command not found']),
        ('syntax_error', ['syntax error', 'parse error', 'unexpected token']),
        ('connection_error', ['connection refused', 'timeout', 'econnrefused', 'network']),
        ('import_error', ['import error', 'module not found', 'no module named']),
        ('type_error', ['typeerror', 'type error']),
        ('git_error', ['fatal:', 'git']),
        ('npm_error', ['npm err', 'npm warn']),
        ('python_error', ['traceback', 'exception']),
    ]

    for pattern_name, keywords in patterns:
        if any(kw in error_lower for kw in keywords):
            return pattern_name

    return 'other_error'

def load_index(project_folder: str) -> dict:
    """Load existing index or create new one."""
    index_file = Path.home() / '.claude' / 'projects' / project_folder / 'recall-index.json'

    if index_file.exists():
        try:
            with open(index_file, 'r') as f:
                return json.load(f)
        except:
            pass

    return {
        'version': 1,
        'project': project_folder,
        'sessions': {},
        'failure_patterns': {},
        'learnings': []
    }

def save_index(project_folder: str, index: dict):
    """Save index to disk."""
    index_dir = Path.home() / '.claude' / 'projects' / project_folder
    index_dir.mkdir(parents=True, exist_ok=True)

    index_file = index_dir / 'recall-index.json'
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2, default=str)

def main():
    # Get project path from environment or argument
    cwd = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()
    if len(sys.argv) > 1:
        cwd = sys.argv[1]

    project_folder = get_project_folder(cwd)
    session_file = find_current_session(project_folder)

    if not session_file:
        print(f"No session found for project: {cwd}", file=sys.stderr)
        sys.exit(0)

    # Parse session
    session_data = parse_session_full(session_file)

    # Load and update index
    index = load_index(project_folder)

    session_id = session_data['session_id']

    # Add/update session in index
    index['sessions'][session_id] = {
        'date': session_data['date'],
        'summary': session_data['summary'],
        'message_count': len(session_data['user_messages']),
        'command_count': len(session_data['commands']),
        'failure_count': len(session_data['failures']),
        'topics': session_data['topics'],
        'user_messages': session_data['user_messages'][:20],  # Keep first 20
        'failures': session_data['failures'][:10]  # Keep first 10 failures
    }

    # Merge failure patterns into global patterns
    for pattern, failures in session_data['failure_patterns'].items():
        if pattern not in index['failure_patterns']:
            index['failure_patterns'][pattern] = []
        for f in failures:
            f['session_id'] = session_id
            f['date'] = session_data['date']
            index['failure_patterns'][pattern].append(f)
        # Keep only last 20 of each pattern
        index['failure_patterns'][pattern] = index['failure_patterns'][pattern][-20:]

    # Save updated index
    save_index(project_folder, index)

    print(f"Indexed session {session_id[:8]}... ({len(session_data['user_messages'])} messages, {len(session_data['commands'])} commands, {len(session_data['failures'])} failures)")

if __name__ == '__main__':
    main()
