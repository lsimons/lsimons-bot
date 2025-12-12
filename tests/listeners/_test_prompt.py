"""Tests for _prompt module functions."""

from listeners._prompt import (
    build_message_context,
    build_system_prompt,
    estimate_tokens,
    format_for_slack,
    get_suggested_prompts,
    trim_messages_for_context,
)


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function."""

    def test_build_system_prompt_default(self) -> None:
        """Test building system prompt with defaults."""
        prompt = build_system_prompt()

        assert "helpful AI assistant" in prompt
        assert "Slack" in prompt
        assert "professional" in prompt

    def test_build_system_prompt_with_context(self) -> None:
        """Test building system prompt with context injection."""
        context = "You are in channel #engineering"
        prompt = build_system_prompt(context=context)

        assert context in prompt
        assert "helpful AI assistant" in prompt

    def test_build_system_prompt_custom_base(self) -> None:
        """Test building system prompt with custom base."""
        custom_prompt = "You are a code reviewer. {context}"
        context = "Focus on Python code."

        prompt = build_system_prompt(base_prompt=custom_prompt, context=context)

        assert "code reviewer" in prompt
        assert "Focus on Python code" in prompt

    def test_build_system_prompt_custom_without_context_placeholder(self) -> None:
        """Test custom prompt without {context} placeholder."""
        custom_prompt = "You are a helpful assistant."
        context = "Channel: engineering"

        prompt = build_system_prompt(base_prompt=custom_prompt, context=context)

        assert "helpful assistant" in prompt
        assert "Channel: engineering" in prompt

    def test_build_system_prompt_empty_context(self) -> None:
        """Test with empty context string."""
        prompt = build_system_prompt(context="")

        assert "helpful AI assistant" in prompt


class TestGetSuggestedPrompts:
    """Tests for get_suggested_prompts function."""

    def test_get_suggested_prompts_basic(self) -> None:
        """Test getting basic suggested prompts."""
        prompts = get_suggested_prompts()

        assert len(prompts) >= 4
        titles = [p["title"] for p in prompts]
        assert "Summarize" in titles
        assert "Answer Question" in titles

    def test_get_suggested_prompts_with_channel_topic(self) -> None:
        """Test getting prompts for channel with topic."""
        prompts = get_suggested_prompts(channel_topic="General discussion")

        assert len(prompts) >= 4
        titles = [p["title"] for p in prompts]
        assert "Summarize" in titles

    def test_get_suggested_prompts_engineering_channel(self) -> None:
        """Test prompts for engineering channel."""
        prompts = get_suggested_prompts(channel_topic="Engineering team discussions")

        titles = [p["title"] for p in prompts]
        assert "Code Review" in titles

    def test_get_suggested_prompts_dev_channel(self) -> None:
        """Test prompts for dev channel."""
        prompts = get_suggested_prompts(channel_topic="Development")

        titles = [p["title"] for p in prompts]
        assert "Code Review" in titles

    def test_get_suggested_prompts_design_channel(self) -> None:
        """Test prompts for design channel."""
        prompts = get_suggested_prompts(channel_topic="UI/UX Design")

        titles = [p["title"] for p in prompts]
        assert "Design Feedback" in titles

    def test_get_suggested_prompts_all_have_title_description(self) -> None:
        """Test that all prompts have required fields."""
        prompts = get_suggested_prompts(channel_topic="Engineering")

        for prompt in prompts:
            assert "title" in prompt
            assert "description" in prompt
            assert isinstance(prompt["title"], str)
            assert isinstance(prompt["description"], str)
            assert len(prompt["title"]) > 0
            assert len(prompt["description"]) > 0


class TestFormatForSlack:
    """Tests for format_for_slack function."""

    def test_format_for_slack_basic(self) -> None:
        """Test basic formatting for Slack."""
        response = "Hello there!"
        formatted = format_for_slack(response)

        assert formatted == "Hello there!"

    def test_format_for_slack_strips_whitespace(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        response = "  Hello there!  \n\n"
        formatted = format_for_slack(response)

        assert formatted == "Hello there!"
        assert not formatted.startswith(" ")
        assert not formatted.endswith(" ")

    def test_format_for_slack_preserves_mentions(self) -> None:
        """Test that Slack mentions are preserved."""
        response = "Hey @user, this is for @channel"
        formatted = format_for_slack(response)

        assert "@user" in formatted
        assert "@channel" in formatted

    def test_format_for_slack_limits_blank_lines(self) -> None:
        """Test that excessive blank lines are limited."""
        response = "Line 1\n\n\n\nLine 2"
        formatted = format_for_slack(response)

        assert "\n\n\n" not in formatted
        assert "Line 1\n\nLine 2" in formatted

    def test_format_for_slack_empty_string(self) -> None:
        """Test formatting empty string."""
        formatted = format_for_slack("")

        assert formatted == ""

    def test_format_for_slack_with_code_block(self) -> None:
        """Test formatting with code blocks."""
        response = """Here's some code:
```python
def hello():
    print("Hello")
```
Done!"""
        formatted = format_for_slack(response)

        assert "```python" in formatted
        assert "def hello():" in formatted


class TestTrimMessagesForContext:
    """Tests for trim_messages_for_context function."""

    def test_trim_messages_empty_list(self) -> None:
        """Test trimming empty message list."""
        result = trim_messages_for_context([])

        assert result == []

    def test_trim_messages_under_limit(self) -> None:
        """Test with messages under token limit."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        result = trim_messages_for_context(messages, max_tokens=1000)

        assert len(result) == 2
        assert result == messages

    def test_trim_messages_over_limit(self) -> None:
        """Test with messages over token limit."""
        messages = [
            {"role": "user", "content": "A" * 5000},
            {"role": "assistant", "content": "B" * 5000},
            {"role": "user", "content": "C" * 5000},
        ]

        result = trim_messages_for_context(messages, max_tokens=2000)

        assert len(result) <= len(messages)
        # Should keep at least first and some of last messages
        assert result[0]["content"].startswith("A")

    def test_trim_messages_single_message(self) -> None:
        """Test with single message."""
        messages = [{"role": "user", "content": "Hello"}]

        result = trim_messages_for_context(messages, max_tokens=1)

        assert len(result) >= 1

    def test_trim_messages_preserves_start(self) -> None:
        """Test that start messages are preserved."""
        messages = [
            {"role": "system", "content": "System context"},
            {"role": "user", "content": "First user message"},
            {"role": "assistant", "content": "A" * 3000},
            {"role": "user", "content": "B" * 3000},
        ]

        result = trim_messages_for_context(messages, max_tokens=1000)

        # Should preserve system and first messages
        assert any(m["content"] == "System context" for m in result)


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_estimate_tokens_empty_string(self) -> None:
        """Test estimating tokens for empty string."""
        tokens = estimate_tokens("")

        assert tokens == 0

    def test_estimate_tokens_short_text(self) -> None:
        """Test estimating tokens for short text."""
        tokens = estimate_tokens("Hello")

        assert tokens >= 1
        assert tokens <= 2

    def test_estimate_tokens_longer_text(self) -> None:
        """Test estimating tokens for longer text."""
        text = "This is a longer piece of text with multiple words."
        tokens = estimate_tokens(text)

        assert tokens > 0
        assert tokens == len(text) // 4

    def test_estimate_tokens_consistency(self) -> None:
        """Test that token estimation is consistent."""
        text = "A" * 100
        tokens = estimate_tokens(text)

        assert tokens == 25  # 100 / 4


class TestBuildMessageContext:
    """Tests for build_message_context function."""

    def test_build_message_context_user_only(self) -> None:
        """Test building context with only user message."""
        context = build_message_context(user_message="What is AI?")

        assert "What is AI?" in context
        assert "User message:" in context

    def test_build_message_context_with_channel(self) -> None:
        """Test building context with channel context."""
        context = build_message_context(
            user_message="Tell me about this",
            channel_context="Channel: engineering",
        )

        assert "Channel: engineering" in context
        assert "Tell me about this" in context

    def test_build_message_context_with_thread(self) -> None:
        """Test building context with thread context."""
        context = build_message_context(
            user_message="Continue the discussion",
            thread_context="Previous: We talked about X",
        )

        assert "Previous: We talked about X" in context
        assert "Continue the discussion" in context

    def test_build_message_context_all_parts(self) -> None:
        """Test building context with all parts."""
        context = build_message_context(
            user_message="Help me",
            channel_context="#engineering",
            thread_context="Context from thread",
        )

        assert "#engineering" in context
        assert "Context from thread" in context
        assert "Help me" in context

    def test_build_message_context_empty_parts(self) -> None:
        """Test building context with empty parts."""
        context = build_message_context(
            user_message="",
            channel_context=None,
            thread_context=None,
        )

        assert context == ""

    def test_build_message_context_formatting(self) -> None:
        """Test that context is properly formatted."""
        context = build_message_context(
            user_message="Question",
            channel_context="Channel info",
            thread_context="Thread info",
        )

        # Should have proper line breaks between sections
        assert "\n\n" in context
