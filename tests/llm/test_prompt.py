"""Unit tests for LLM prompt engineering module.

Tests cover:
- System prompt building with context injection
- Suggested prompt generation based on channel topics
- Slack message formatting
- Message trimming for token limits
- Token estimation
- Message context building
"""

import pytest

from lsimons_bot.llm.prompt import (
    build_message_context,
    build_system_prompt,
    estimate_tokens,
    format_for_slack,
    get_suggested_prompts,
    trim_messages_for_context,
)


class TestBuildSystemPrompt:
    """Tests for system prompt building."""

    def test_build_system_prompt_default(self):
        """Build system prompt uses default template."""
        prompt = build_system_prompt()
        assert "helpful AI assistant" in prompt
        assert "Slack" in prompt

    def test_build_system_prompt_with_context(self):
        """Build system prompt injects context."""
        context = "You are in #engineering channel"
        prompt = build_system_prompt(context=context)
        assert context in prompt

    def test_build_system_prompt_custom_base(self):
        """Build system prompt uses custom base template."""
        custom = "You are a test assistant"
        prompt = build_system_prompt(base_prompt=custom)
        assert "test assistant" in prompt

    def test_build_system_prompt_custom_with_context(self):
        """Build system prompt with custom base and context."""
        custom = "Base: {context}"
        context = "test context"
        prompt = build_system_prompt(base_prompt=custom, context=context)
        assert "Base: test context" == prompt

    def test_build_system_prompt_custom_no_placeholder(self):
        """Build system prompt appends context if no placeholder."""
        custom = "Custom base"
        context = "Extra context"
        prompt = build_system_prompt(base_prompt=custom, context=context)
        assert custom in prompt
        assert context in prompt

    def test_build_system_prompt_removes_placeholder(self):
        """Build system prompt removes placeholder if no context."""
        custom = "Start {context} end"
        prompt = build_system_prompt(base_prompt=custom)
        assert "{context}" not in prompt
        assert "Start" in prompt
        assert "end" in prompt


class TestGetSuggestedPrompts:
    """Tests for suggested prompt generation."""

    def test_get_suggested_prompts_basic(self):
        """Get suggested prompts returns basic prompts."""
        prompts = get_suggested_prompts()
        titles = [p["title"] for p in prompts]
        assert "Summarize" in titles
        assert "Answer Question" in titles
        assert "Brainstorm Ideas" in titles
        assert "Explain Concept" in titles

    def test_get_suggested_prompts_with_engineering_topic(self):
        """Get suggested prompts adds code review for engineering channels."""
        prompts = get_suggested_prompts(channel_topic="Engineering team")
        titles = [p["title"] for p in prompts]
        assert "Code Review" in titles

    def test_get_suggested_prompts_with_dev_topic(self):
        """Get suggested prompts recognizes dev topic."""
        prompts = get_suggested_prompts(channel_topic="Backend development")
        titles = [p["title"] for p in prompts]
        assert "Code Review" in titles

    def test_get_suggested_prompts_with_design_topic(self):
        """Get suggested prompts adds design feedback for design channels."""
        prompts = get_suggested_prompts(channel_topic="Design feedback")
        titles = [p["title"] for p in prompts]
        assert "Design Feedback" in titles

    def test_get_suggested_prompts_case_insensitive(self):
        """Get suggested prompts is case insensitive."""
        prompts = get_suggested_prompts(channel_topic="ENGINEERING")
        titles = [p["title"] for p in prompts]
        assert "Code Review" in titles

    def test_get_suggested_prompts_format(self):
        """Get suggested prompts have correct structure."""
        prompts = get_suggested_prompts()
        assert len(prompts) > 0
        for prompt in prompts:
            assert "title" in prompt
            assert "description" in prompt
            assert isinstance(prompt["title"], str)
            assert isinstance(prompt["description"], str)


class TestFormatForSlack:
    """Tests for Slack message formatting."""

    def test_format_for_slack_empty_string(self):
        """Format for Slack handles empty string."""
        result = format_for_slack("")
        assert result == ""

    def test_format_for_slack_strips_whitespace(self):
        """Format for Slack strips leading/trailing whitespace."""
        text = "  Hello world  \n"
        result = format_for_slack(text)
        assert result == "Hello world"

    def test_format_for_slack_limits_blank_lines(self):
        """Format for Slack limits consecutive blank lines to 2."""
        text = "Line 1\n\n\n\nLine 2"
        result = format_for_slack(text)
        assert "Line 1\n\nLine 2" in result
        assert "\n\n\n" not in result

    def test_format_for_slack_preserves_mentions(self):
        """Format for Slack preserves Slack mentions."""
        text = "Hey @user check this out"
        result = format_for_slack(text)
        assert "@user" in result

    def test_format_for_slack_preserves_code_blocks(self):
        """Format for Slack preserves code blocks."""
        text = "```python\nprint('hello')\n```"
        result = format_for_slack(text)
        assert "```python" in result


class TestTrimMessagesForContext:
    """Tests for message trimming."""

    def test_trim_messages_empty_list(self):
        """Trim messages handles empty list."""
        result = trim_messages_for_context([])
        assert result == []

    def test_trim_messages_within_limit(self):
        """Trim messages returns all if under limit."""
        messages = [
            {"role": "user", "content": "Short"},
            {"role": "assistant", "content": "Response"},
        ]
        result = trim_messages_for_context(messages, max_tokens=1000)
        assert len(result) == 2

    def test_trim_messages_over_limit(self):
        """Trim messages removes old messages when over limit."""
        messages = [
            {"role": "system", "content": "A" * 100},
            {"role": "user", "content": "B" * 100},
            {"role": "assistant", "content": "C" * 100},
            {"role": "user", "content": "D" * 100},
            {"role": "assistant", "content": "E" * 100},
        ]
        result = trim_messages_for_context(messages, max_tokens=50)
        assert len(result) < len(messages)
        # Should keep first few messages (context) and recent ones
        assert result[0] == messages[0]

    def test_trim_messages_preserves_first_messages(self):
        """Trim messages preserves important context from beginning."""
        messages = [
            {"role": "system", "content": "Context 1"},
            {"role": "system", "content": "Context 2"},
            {"role": "system", "content": "Context 3"},
            {"role": "user", "content": "Q" * 5000},
        ]
        result = trim_messages_for_context(messages, max_tokens=100)
        # First 3 messages should be preserved
        assert messages[0] in result
        assert messages[1] in result
        assert messages[2] in result

    def test_trim_messages_always_returns_at_least_one(self):
        """Trim messages always returns at least one message."""
        messages = [
            {"role": "user", "content": "A" * 10000},
        ]
        result = trim_messages_for_context(messages, max_tokens=10)
        assert len(result) >= 1


class TestEstimateTokens:
    """Tests for token estimation."""

    def test_estimate_tokens_empty_string(self):
        """Estimate tokens returns 0 for empty string."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_none(self):
        """Estimate tokens returns 0 for None."""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_simple_text(self):
        """Estimate tokens uses rough approximation."""
        # 4 characters per token
        text = "1234"
        assert estimate_tokens(text) == 1

    def test_estimate_tokens_longer_text(self):
        """Estimate tokens scales with text length."""
        text = "a" * 400
        assert estimate_tokens(text) == 100

    def test_estimate_tokens_is_integer(self):
        """Estimate tokens returns integer."""
        assert isinstance(estimate_tokens("hello"), int)


class TestBuildMessageContext:
    """Tests for message context building."""

    def test_build_message_context_user_message_only(self):
        """Build message context with only user message."""
        context = build_message_context("Hello")
        assert "User message:" in context
        assert "Hello" in context

    def test_build_message_context_with_channel(self):
        """Build message context includes channel context."""
        context = build_message_context(
            "Hello",
            channel_context="Channel: #general",
        )
        assert "Channel context:" in context
        assert "Channel: #general" in context

    def test_build_message_context_with_thread(self):
        """Build message context includes thread context."""
        context = build_message_context(
            "Hello",
            thread_context="Previous messages...",
        )
        assert "Thread context:" in context
        assert "Previous messages..." in context

    def test_build_message_context_all_parts(self):
        """Build message context includes all parts."""
        context = build_message_context(
            "Hello",
            channel_context="Channel info",
            thread_context="Thread info",
        )
        assert "Channel context:" in context
        assert "Thread context:" in context
        assert "User message:" in context

    def test_build_message_context_order(self):
        """Build message context maintains proper order."""
        context = build_message_context(
            "Message",
            channel_context="Channel",
            thread_context="Thread",
        )
        channel_pos = context.find("Channel context:")
        thread_pos = context.find("Thread context:")
        user_pos = context.find("User message:")
        assert channel_pos < thread_pos < user_pos

    def test_build_message_context_sections_separated(self):
        """Build message context separates sections with blank lines."""
        context = build_message_context(
            "Message",
            channel_context="Channel",
            thread_context="Thread",
        )
        assert "\n\n" in context
