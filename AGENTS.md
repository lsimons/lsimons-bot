# AGENTS.md - Instructions for AI Coding Agents

This document provides instructions for AI code-generation agents.

## Response Style

- Be concise in responses - avoid over-explaining changes.
- Focus on the specific task requested rather than extensive commentary.

## Project Overview

- Python AI bot for Schuberg Philis Slack.

## Project Structure

```
lsimons-bot/
├── listeners/             # Slack Bolt listener categories (actions, commands, events, messages, shortcuts, views)
│   ├── actions/
│   ├── commands/
│   ├── events/
│   ├── messages/
│   ├── shortcuts/
│   └── views/
├── tests/                 # Unit tests organized by feature/category
├── docs/
│   └── spec/              # Persistent specs (000, 001, 002...)
├── history/               # AI-generated planning/ephemeral docs
├── .beads/                # bd (beads) issue tracking files
└── [config files]         # Root-level configuration
```

## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**
```bash
bd ready --json
```

**Create new issues:**
```bash
bd create "Issue title" -t bug|feature|task -p 0-4 --json
bd create "Issue title" -p 1 --deps discovered-from:bd-123 --json
bd create "Subtask" --parent <epic-id> --json  # Hierarchical subtask (gets ID like epic-id.1)
```

**Claim and update:**
```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**
```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`
6. **Commit together**: Always commit the `.beads/issues.jsonl` file together with the code changes so issue state stays in sync with code state

### Auto-Sync

bd automatically syncs with git:
- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### Managing AI-Generated Planning Documents

AI assistants often create planning and design documents during development:
- PLAN.md, IMPLEMENTATION.md, ARCHITECTURE.md
- DESIGN.md, CODEBASE_SUMMARY.md, INTEGRATION_PLAN.md
- TESTING_GUIDE.md, TECHNICAL_DESIGN.md, and similar files

These can clutter the project. So:

- Store ALL AI-generated planning/design docs in `history/`
- Keep the repository root clean and focused on permanent project files
- Only access `history/` when explicitly asked to review past planning
- See below for the use of specifications to store in `docs/spec/`, which are permanently useful bits to extract from the planning documents

**Benefits:**
- ✅ Clean repository root
- ✅ Clear separation between ephemeral and permanent documentation
- ✅ Easy to exclude from version control if desired
- ✅ Preserves planning history for archeological research
- ✅ Reduces noise when browsing the project

### CLI Help

Run `bd <command> --help` to see all available flags for any command.
For example: `bd create --help` shows `--parent`, `--deps`, `--assignee`, etc.

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ✅ Store AI planning docs in `history/` directory
- ✅ Run `bd <cmd> --help` to discover available flags
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems
- ❌ Do NOT clutter repo root with planning documents

## Development Standards

### Specs

- All significant changes need a spec.
- See [docs/spec/001-spec-based-development.md] for how to write specs, and refer to [docs/spec/002-slack-listener-patterns.md] for repository listener conventions and registration patterns.
- Common patterns are in [docs/spec/000-shared-patterns.md] to keep individual specs short.

### Code Quality Requirements

All code must meet these quality standards:

1. **Code Coverage**: Minimum 80% test coverage (branches, functions, lines, statements)
2. **flake8**: Zero warnings or errors
3. **black**: All code must be formatted
4. **Type Safety**: Full and strict Python typing
5. **basedpyright**: Zero errors (warnings are informational)

### Commit Message Convention

Follow [Conventional Commits](https://conventionalcommits.org/) with these types:

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `build`: Build system changes
- `ci`: CI configuration changes
- `perf`: Performance improvements
- `revert`: Reverting commits
- `improvement`: General code improvements
- `chore`: Maintenance tasks

**Format**: `type(scope): description`
**Example**: `feat(core-model): add new validation rules`

## Development process - building and testing

### Process

Always follow this development process:

0. Use beads (bd) for all issue tracking
1. Make sure the git working directory is clean
2. Create a new git branch for new work
3. For a significant change like a new feature, create a spec doc
4. Ask for human review of the spec
5. Only if the human confirms, implement the spec
6. Create tests for the new functionality
7. Run tests, linting, and formatting
8. Commit changes with a proper commit message
9. Do *not* try to handle git branch, push, or pull requests, ask the human

### Initial Setup

```zsh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
slack run
```

### Testing

Run pytest from root directory for unit testing:

```zsh
uv run pytest .
```

### Linting

Run flake8 and basedpyright from root directory for linting:

```zsh
uv run flake8 app.py app_oauth.py lsimons_bot tests
```

Run basedpyright for strict type checking:

```zsh
basedpyright lsimons_bot
```

**Note**: If basedpyright is not installed, install it globally:
```zsh
npm install -g basedpyright
```

### Formatting

Run black from root directory for code formatting:

```zsh
uv run black .
```

## Environment and Dependencies

### Required Tools

- **Python**: LTS version
- **uv**: Latest stable version
- **Docker**: For dependent services
- **Slack Apps SDK**: Latest stable version
