#!/usr/bin/env python3
"""
Local heuristic knowledge extractor.
Extracts paths, credentials, tools from session data without API calls.
"""

import re
import sys
import json
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))

from pending import add_pending


def extract_credential_paths(text: str) -> list:
    """Extract likely credential file paths."""
    patterns = [
        r'~/\.[a-zA-Z0-9_-]*(?:cred|token|key|pass|auth|secret)[a-zA-Z0-9_-]*',
        r'~/\.[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]*(?:cred|token|key|pass|auth)[a-zA-Z0-9_.-]*',
        r'~/.(?:arango|waystar|trillium|bb)[a-zA-Z0-9_-]*',
    ]

    found = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.update(matches)

    return list(found)


def extract_tool_paths(text: str, successful_commands: list) -> list:
    """Extract tool paths from successful commands."""
    tools = set()

    # Look for paths in ~/code/ that are scripts/tools
    pattern = r'~/code/[a-zA-Z0-9_-]+/(?:bin|scripts?|tools?)/[a-zA-Z0-9_.-]+'

    for cmd in successful_commands:
        matches = re.findall(pattern, cmd)
        tools.update(matches)

    # Also look for explicit tool mentions
    tool_pattern = r'~/code/[a-zA-Z0-9_-]+/[a-zA-Z0-9_/-]+\.(?:sh|py|js)'
    for cmd in successful_commands:
        matches = re.findall(tool_pattern, cmd)
        tools.update(matches)

    return list(tools)


def extract_env_files(text: str) -> list:
    """Extract .env and environment file paths."""
    patterns = [
        r'~/\.[a-zA-Z0-9_-]*env[a-zA-Z0-9_/-]*',
        r'~/.kureenv/[a-zA-Z0-9_.-]+',
    ]

    found = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.update(matches)

    return list(found)


def is_complex_session(session_data: dict) -> bool:
    """Determine if session needs Claude API analysis."""
    failures = session_data.get('failures', [])
    messages = session_data.get('user_messages', [])
    commands = session_data.get('commands', [])

    # 3+ failures
    if len(failures) >= 3:
        return True

    # Debugging keywords
    debug_keywords = ['why', 'not working', 'figured out', 'root cause',
                      'the problem', 'issue was', 'fixed by', 'solution']
    all_text = ' '.join(m.get('content', '') for m in messages).lower()
    if any(kw in all_text for kw in debug_keywords):
        return True

    # Long session with many tool calls
    if len(messages) >= 10 and len(commands) >= 15:
        return True

    return False


def extract_from_session(session_data: dict, project_folder: str) -> tuple:
    """Extract knowledge proposals from session data."""
    proposals = []

    session_id = session_data.get('session_id', 'unknown')
    summary = session_data.get('summary', '')[:100]

    # Combine all text for searching
    all_text = ''
    for msg in session_data.get('user_messages', []):
        content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
        all_text += content + '\n'

    # Get successful commands (not in failures)
    failed_cmds = {f.get('command', '') for f in session_data.get('failures', [])}
    successful_cmds = [
        c.get('command', '') for c in session_data.get('commands', [])
        if c.get('command', '') not in failed_cmds
    ]

    # Extract credentials
    creds = extract_credential_paths(all_text)
    for cred in creds:
        proposals.append({
            'category': 'Credentials',
            'title': f'Credential file: {Path(cred).name}',
            'content': cred,
            'suggested_scope': 'global'
        })

    # Extract tools
    tools = extract_tool_paths(all_text, successful_cmds)
    for tool in tools:
        proposals.append({
            'category': 'Tools',
            'title': f'Tool: {Path(tool).name}',
            'content': tool,
            'suggested_scope': 'global'
        })

    # Extract env files
    envs = extract_env_files(all_text)
    for env in envs:
        proposals.append({
            'category': 'Credentials',
            'title': f'Env file: {Path(env).name}',
            'content': env,
            'suggested_scope': 'global'
        })

    return proposals, is_complex_session(session_data)


def main():
    """Process session data from stdin or file argument."""
    if len(sys.argv) > 1 and sys.argv[1] != '-':
        session_file = Path(sys.argv[1])
        if session_file.exists():
            session_data = json.loads(session_file.read_text())
        else:
            print(f"File not found: {session_file}", file=sys.stderr)
            sys.exit(1)
    else:
        session_data = json.load(sys.stdin)

    project = sys.argv[2] if len(sys.argv) > 2 else 'unknown'

    proposals, needs_api = extract_from_session(session_data, project)

    # Add proposals to pending
    added = 0
    for p in proposals:
        add_pending(
            category=p['category'],
            title=p['title'],
            content=p['content'],
            session_id=session_data.get('session_id', 'unknown'),
            session_summary=session_data.get('summary', '')[:100],
            project=project,
            suggested_scope=p['suggested_scope'],
            source='heuristic'
        )
        added += 1

    result = {
        'proposals_added': added,
        'needs_api_analysis': needs_api
    }

    print(json.dumps(result))


if __name__ == '__main__':
    main()
