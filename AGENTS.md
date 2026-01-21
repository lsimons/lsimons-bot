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
├── lsimons_bot/           # Main application source code
│   ├── app/               # Application core
│   │   ├── __init__.py
│   │   ├── main.py        # Application entry point and initialization
│   │   └── config.py      # Environment configuration
│   └── slack/             # Slack integration layer
│       ├── __init__.py
│       ├── assistant/     # AI assistant handlers
│       │   ├── __init__.py    # register(app) function
│       │   ├── assistant_message.py
│       │   └── assistant_thread_started.py
│       ├── home/          # Home tab handlers
│       │   ├── __init__.py
│       │   └── app_home_opened.py
│       └── messages/      # Message event handlers
│           ├── __init__.py
│           ├── app_mention.py
│           └── message.py
├── tests/                 # Unit tests mirroring source structure
│   ├── app/               # Application core tests
│   │   ├── test_main.py   # Tests for main.py
│   │   └── test_config.py # Tests for config.py
│   └── slack/             # Slack integration tests
│       ├── assistant/     # Tests for assistant module
│       ├── home/          # Tests for home module
│       └── messages/      # Tests for messages module
├── docs/
│   └── spec/              # Persistent specs (000, 001, 002...)
├── app.py                 # Entry point script (imports from lsimons_bot.app.main)
├── manifest.json          # Slack app manifest
├── requirements.txt       # Python dependencies
└── pyrightconfig.json     # Type checker configuration
```

**Key patterns:**
- Two main submodules: `app/` (core) and `slack/` (integration)
- Slack modules have `__init__.py` with a `register(app)` function
- Each handler is in its own file (one handler per file)
- Tests mirror source structure exactly (module → test submodule, file → test file)

**Module Dependencies:**
- `lsimons_bot.app` depends on `lsimons_bot.slack` (imports and registers handlers)
- `lsimons_bot.slack` has NO dependency on `lsimons_bot.app`
- This keeps the Slack integration layer clean and reusable

## Development Standards

### Specs

- All significant changes need a spec.
- See [docs/spec/001-spec-based-development.md] for how to write specs.
- Common patterns are in [docs/spec/000-shared-patterns.md] to keep individual specs short.

### Code Quality Requirements

All code must meet these quality standards:

1. **black**: All code must be formatted
2. **flake8**: Zero warnings or errors
3. **basedpyright**: Zero errors (warnings are informational)
4. **Type Safety**: Full and strict Python typing
5. **Code Coverage**: Minimum 80% test coverage (branches, functions, lines, statements)

### Coding Style and Patterns

This codebase values **compact, pragmatic code**. Follow these patterns:

#### Code Organization

- **Small files**: Keep files under 300 lines (most are under 25 lines)
- **Module structure**: Two main submodules:
  - `lsimons_bot.app/` - Application core (main, config)
  - `lsimons_bot.slack/` - Slack integration (assistant, home, messages)
- **Slack modules**: Each has `__init__.py` with a `register(app)` function
- **Handler files**: One handler per file for clarity
- **Clean dependencies**:
  - `app` depends on `slack` (registers handlers)
  - `slack` has NO dependency on `app` (reusable integration layer)
- **No over-engineering**: Write simple, direct code for current requirements
- **Type hints**: Use full type annotations everywhere

#### Test Organization

- **Mirror source structure**: All modules with submodules get test submodules
  - `lsimons_bot/app/` → `tests/app/`
  - `lsimons_bot/slack/assistant/` → `tests/slack/assistant/`
  - `lsimons_bot/slack/home/` → `tests/slack/home/`
  - `lsimons_bot/slack/messages/` → `tests/slack/messages/`
  - Each source file gets its own test file (e.g., `assistant_message.py` → `test_assistant_message.py`)
- **Pragmatic testing**:
  - Aim for 100% coverage with minimal tests
  - Focus on happy path + key error cases
  - No redundant edge case tests
  - No docstrings on test methods (names are self-documenting)
- **Minimal mocking**:
  - Only mock external dependencies
  - Don't assert on mock call details unless testing specific behavior
  - Use helper methods to reduce duplication
  - Tests verify "does it work" not "how does it work"

#### What to Avoid

- ❌ Long files (>300 lines)
- ❌ Docstrings on test methods
- ❌ Redundant test cases for every edge case
- ❌ Over-mocking or asserting on mock internals
- ❌ Premature abstractions or helper functions for one-time use
- ❌ Feature flags, backwards-compatibility hacks, or hypothetical requirements
- ❌ Verbose test names with full sentences (keep them concise)

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

1. Make sure the git working directory is clean
2. Create a new git branch for new work
3. For a significant change like a new feature, create a spec doc
4. Ask for human review of the spec
5. Only if the human confirms, implement the spec
6. Create tests for the new functionality
7. Run formatting, linting, and tests
8. Commit changes with a proper commit message
9. Do *not* try to handle git branch, push, or pull requests, ask the human

### Initial Setup

```zsh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
slack run
```

### Formatting

Run black from root directory for code formatting:

```zsh
uv run black .
```

### Linting

Run flake8 and basedpyright from root directory for linting:

```zsh
uv run flake8 app.py lsimons_bot tests
```

Run basedpyright for strict type checking:

```zsh
basedpyright lsimons_bot
```

**Note**: If basedpyright is not installed, install it globally:
```zsh
npm install -g basedpyright
```

### Testing

Run pytest from root directory for unit testing:

```zsh
uv run pytest .
```

## Environment and Dependencies

### Required Tools

- **Python**: LTS version
- **uv**: Latest stable version
- **Docker**: For dependent services
- **Slack Apps SDK**: Latest stable version
