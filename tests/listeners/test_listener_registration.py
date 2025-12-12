"""Tests for listener registration functions."""

from unittest.mock import MagicMock

from slack_bolt import App

from lsimons_bot.listeners import (
    actions,
    commands,
    events,
    messages,
    register_listeners,
    shortcuts,
    views,
)


class TestRegisterListeners:
    """Tests for register_listeners function."""

    def test_register_listeners_calls_all_categories(self) -> None:
        """Test that register_listeners calls register in all categories."""
        app = MagicMock(spec=App)

        # Patch all category register functions
        import lsimons_bot.listeners as listeners_module

        original_actions_register = listeners_module.actions.register
        original_commands_register = listeners_module.commands.register
        original_events_register = listeners_module.events.register
        original_messages_register = listeners_module.messages.register
        original_shortcuts_register = listeners_module.shortcuts.register
        original_views_register = listeners_module.views.register

        try:
            listeners_module.actions.register = MagicMock()
            listeners_module.commands.register = MagicMock()
            listeners_module.events.register = MagicMock()
            listeners_module.messages.register = MagicMock()
            listeners_module.shortcuts.register = MagicMock()
            listeners_module.views.register = MagicMock()

            register_listeners(app)

            listeners_module.actions.register.assert_called_once_with(app)
            listeners_module.commands.register.assert_called_once_with(app)
            listeners_module.events.register.assert_called_once_with(app)
            listeners_module.messages.register.assert_called_once_with(app)
            listeners_module.shortcuts.register.assert_called_once_with(app)
            listeners_module.views.register.assert_called_once_with(app)
        finally:
            # Restore original functions
            listeners_module.actions.register = original_actions_register
            listeners_module.commands.register = original_commands_register
            listeners_module.events.register = original_events_register
            listeners_module.messages.register = original_messages_register
            listeners_module.shortcuts.register = original_shortcuts_register
            listeners_module.views.register = original_views_register


class TestActionsRegister:
    """Tests for actions.register function."""

    def test_actions_register_with_app(self) -> None:
        """Test actions.register accepts app without error."""
        app = MagicMock(spec=App)
        # Should not raise
        actions.register(app)


class TestCommandsRegister:
    """Tests for commands.register function."""

    def test_commands_register_with_app(self) -> None:
        """Test commands.register accepts app without error."""
        app = MagicMock(spec=App)
        # Should not raise
        commands.register(app)


class TestEventsRegister:
    """Tests for events.register function."""

    def test_events_register_with_app(self) -> None:
        """Test events.register accepts app without error."""
        app = MagicMock(spec=App)
        # Should not raise
        events.register(app)


class TestMessagesRegister:
    """Tests for messages.register function."""

    def test_messages_register_with_app(self) -> None:
        """Test messages.register accepts app without error."""
        app = MagicMock(spec=App)
        # Should not raise
        messages.register(app)


class TestShortcutsRegister:
    """Tests for shortcuts.register function."""

    def test_shortcuts_register_with_app(self) -> None:
        """Test shortcuts.register accepts app without error."""
        app = MagicMock(spec=App)
        # Should not raise
        shortcuts.register(app)


class TestViewsRegister:
    """Tests for views.register function."""

    def test_views_register_with_app(self) -> None:
        """Test views.register accepts app without error."""
        app = MagicMock(spec=App)
        # Should not raise
        views.register(app)
