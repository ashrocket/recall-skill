# shell-failures

A Claude Code skill that helps Claude learn from shell command failures.

## Install

```bash
git clone https://github.com/you/shell-failures ~/.claude/skills/shell-failures
~/.claude/skills/shell-failures/install.sh
```

## Usage

The skill works automatically:
- When a bash command fails, you'll see the relevant SOP
- When a fix works, you'll be asked to save the pattern

Commands:
- `/failures` - Show failures with resolutions
- `/failures --sop` - Include SOP details
- `/failures --all` - List all SOPs

## Customization

Edit `~/.claude/shell-failures/sops.json` to customize global SOPs.

Create `.claude/sops.json` in a project for project-specific SOPs.

## Uninstall

```bash
~/.claude/skills/shell-failures/uninstall.sh
```
