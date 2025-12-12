# 002 - Slack Bolt Listener Patterns

**Purpose:** Define consistent patterns and conventions for Slack Bolt "listeners" in this repository so contributors (human and agent) can add, register, test, and document listeners in a predictable, low-friction way.

This spec describes:
- Directory and file layout conventions for listener categories
- The registration pattern used by the central registration orchestrator
- Example skeletons for adding new listeners
- Testing and documentation guidance
- Implementation and commit workflow notes

---

## Requirements
- Listener code must be easy to discover and import by the app bootstrap.
- Each listener category (actions, commands, events, messages, shortcuts, views) must expose a single `register(app: App)` entrypoint.
- The top-level `listeners/__init__.py` (the orchestrator) calls each category's `register` function.
- Listener modules should contain a single responsibility (one handler per file is preferred) and be named clearly.
- Code must be typed where practical and import-safe (no side-effects during import that require network or credentials).
- Specs should be short and refer to this document when adding new patterns.

---

## Directory layout (recommended)
Use the following layout under the repository root:

- `listeners/`
  - `__init__.py`          # Orchestrates registration across categories
  - `actions/`             # action_id -> handler mapping
    - `__init__.py`        # Exposes register(app: App)
    - `<something>.py`     # One listener per file preferred
  - `commands/`
    - `__init__.py`
    - `<command>.py`
  - `events/`
    - `__init__.py`
    - `<event>.py`
  - `messages/`
    - `__init__.py`
    - `<message_listener>.py`
  - `shortcuts/`
    - `__init__.py`
    - `<shortcut>.py`
  - `views/`
    - `__init__.py`
    - `<view_submission>.py`

Notes:
- Keep `__init__.py` files minimal and focused on exports and `register` functions.
- Keep any complex, reusable helpers in a shared module (e.g., `listeners/_utils.py` or `listeners/_types.py`) if needed.

---

## Registration pattern

Design goals:
- Importing modules should not register handlers automatically.
- Registration happens explicitly when the application bootstrap calls `listeners.register_all(app)` or equivalent.
- Each category exposes `register(app: App)` that performs `app.action(...)`, `app.command(...)`, `app.event(...)`, etc.

Recommended orchestrator (`listeners/__init__.py`) behavior:
- Discover known categories (hard-coded import list is preferred for clarity).
- Import each category module and call its `register(app)` function in a deterministic order.
- Do not attempt runtime filesystem discovery (dynamic imports) unless there's a compelling reason — prefer explicit imports so static analysis and tests work reliably.

Example orchestrator shape (illustrative; adapt to app bootstrap code):

    # listeners/__init__.py (conceptual)
    from slack_bolt import App
    from . import actions, commands, events, messages, shortcuts, views

    def register_all(app: App):
        """
        Register all listener categories with the given Slack `app`.
        Call this once during app startup.
        """
        actions.register(app)
        commands.register(app)
        events.register(app)
        messages.register(app)
        shortcuts.register(app)
        views.register(app)

Each category `__init__.py` should follow a minimal pattern:

    # listeners/actions/__init__.py (conceptual)
    from slack_bolt import App
    # Import specific listeners explicitly
    from .sample_action import sample_action_handler

    def register(app: App):
        # register listeners with the app
        app.action("sample_action_id")(sample_action_handler)

Important:
- Do not perform `register` calls at module import time. They must be invoked only when `register(app)` is called by the orchestrator.

---

## Naming and file-level conventions
- File names: `snake_case` and reflect the handler purpose (e.g., `approve_request.py`, `app_home_opened.py`).
- Handler function names: `handle_<purpose>` or `<purpose>_handler`.
- For command listeners, prefer `command_<name>_handler`.
- Keep one handler per file when possible — reduces merge conflicts and makes tracking easier.
- When a listener requires helper functions, put them in the same file below the handler or in a `_utils.py` in the category directory if shared.

---

## Example skeletons

Minimal action listener file:

    # /dev/null/listeners/actions/approve_request.py (example)
    from typing import Any
    from slack_bolt import Ack, Say, Respond, App
    from slack_bolt.request import BoltRequest

    def approve_request_handler(ack: Ack, body: dict[str, Any], logger) -> None:
        ack()
        # implementation goes here
        logger.info("approve_request invoked for %s", body.get("user"))

    # exported symbol can be imported by listeners/actions/__init__.py
    __all__ = ["approve_request_handler"]

Category register example:

    # /dev/null/listeners/actions/__init__.py (example)
    from slack_bolt import App
    from .approve_request import approve_request_handler

    def register(app: App) -> None:
        # Bind the handler to the action ID used in Slack's interactive payload
        app.action("approve_request")(approve_request_handler)

Orchestrator usage in app bootstrap:

    # /dev/null/app.py (bootstrap excerpt)
    from slack_bolt import App
    from listeners import register_all

    app = App()
    register_all(app)
    # start app or continue bootstrap

---

## Adding a new listener (step-by-step)
1. Create a new file in the appropriate category, named clearly (e.g., `listeners/commands/reload_config.py`).
2. Implement the handler function and export the symbol via `__all__` (optional but recommended).
3. Update the category `__init__.py` to import the handler and register it inside `register(app)`.
4. Add or update unit tests for the handler in `tests/listeners/<category>/`.
5. Add a short line to the spec index if the new pattern needs documenting (rare).
6. Run local linting and tests.
7. Commit code and include the `.beads/issues.jsonl` update as part of the same commit if the change corresponds to a tracked issue per repository rules.

---

## Testing guidance
- Unit test approach: verify the handler logic separately from Slack Bolt's decorator binding.
- Use fixtures to construct fake payloads and assert expected outcomes.
- For registration, a simple smoke test can import the category module, create a `slack_bolt.App()` instance, call `register(app)`, and assert no exceptions during registration.
- Avoid starting networked servers in tests; keep tests fast and deterministic.

Example test checklist:
- Handler code executes for a typical payload.
- Edge cases (missing fields) handled gracefully.
- `register(app)` doesn't raise and binds expected number of listeners.

---

## Documentation & specs
- Add short examples to `docs/spec/002-slack-listener-patterns.md` when conventions change.
- Link this spec from `AGENTS.md` and other higher-level docs so automated agents and contributors find it quickly.
- When adding a new category or changing registration flow, update this spec and create a short changelog entry in `docs/history/` if present.

---

## Implementation notes & pitfalls
- Avoid side-effects at import time (e.g., network calls, environment-dependent behavior). Import-time side-effects complicate tests and CI.
- Prefer explicit imports over filesystem discovery to keep static analysis, linters, and code navigation simple.
- Keep handler code small and pure where possible — move complex operations into separate service modules to ease testing and reuse.
- Be mindful of Slack rate limits; handlers that perform multiple API calls should batch work or use async/background processing if necessary.

---

## Commit and issue workflow
- When implementing work described by a `bd` issue, update the issue (status change) before starting and commit the `.beads/issues.jsonl` changes together with code.
- Use spec number references in commit messages when appropriate, e.g., `spec 002: add skeleton for approve_request action`.
- If you discover new patterns worth sharing, create or update a spec under `docs/spec/` and reference it from `AGENTS.md`.

---

## Quick reference (at-a-glance)
- Each category: implement `register(app: App)` in `listeners/<category>/__init__.py`
- Orchestrator: call each category's `register(app)` from `listeners/__init__.py` (exposed as `register_all`)
- One handler per file preferred
- No registration at import time
- Tests: unit tests + registration smoke test
- Document new patterns in `docs/spec/`

---

## Implementation checklist
- [ ] Create new listener file under the correct category
- [ ] Export handler symbols clearly
- [ ] Update category `__init__.py` to import and register
- [ ] Ensure `listeners/__init__.py` calls category register functions
- [ ] Add/update tests in `tests/listeners/`
- [ ] Update AGENTS.md if this affects agent behaviors
- [ ] Run `pytest`, `flake8`, and `black` before committing

---

Implementation notes follow the shared spec template in `docs/spec/000-shared-patterns.md`. Keep specs short and actionable.