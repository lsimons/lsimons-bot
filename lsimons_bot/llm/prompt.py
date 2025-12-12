"""Prompt engineering module for AI assistant.

Provides system prompts, suggested prompts, response formatting,
and token-aware prompt trimming for LLM interactions.
"""

import logging

logger = logging.getLogger(__name__)

# System prompt template with context injection
DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant integrated into Slack.

Guidelines:
- Be concise and friendly in your responses
- Use clear, professional language
- Format responses for readability in Slack
- Preserve Slack mentions (@user, @channel) in your responses
- If asked about something you don't know, be honest about limitations
- When referencing code or technical content, use code blocks with proper formatting

{context}
"""

# Suggested prompt templates for different use cases
SUGGESTED_PROMPTS_TEMPLATES = {
    "summarize": {
        "title": "Summarize",
        "description": "Summarize the recent discussion in this thread",
        "prompt": "Please summarize the key points from our discussion so far in 2-3 sentences.",
    },
    "question": {
        "title": "Answer Question",
        "description": "Help answer a specific question",
        "prompt": "What would be your response to: ",
    },
    "brainstorm": {
        "title": "Brainstorm Ideas",
        "description": "Generate ideas for a topic",
        "prompt": "Let's brainstorm some creative ideas about: ",
    },
    "explain": {
        "title": "Explain Concept",
        "description": "Explain a concept in simple terms",
        "prompt": "Can you explain this concept in simple terms: ",
    },
    "code_review": {
        "title": "Code Review",
        "description": "Review code for issues or improvements",
        "prompt": "Please review this code for potential issues or improvements: ",
    },
    "design_feedback": {
        "title": "Design Feedback",
        "description": "Provide feedback on design",
        "prompt": "What feedback would you give on this design: ",
    },
}


def build_system_prompt(
    base_prompt: str | None = None,
    context: str | None = None,
) -> str:
    """Build the system prompt with optional context injection.

    Args:
        base_prompt: Custom system prompt. Defaults to DEFAULT_SYSTEM_PROMPT
        context: Additional context to inject (e.g., channel topic, selected messages)

    Returns:
        Complete system prompt for LLM
    """
    prompt_template = base_prompt or DEFAULT_SYSTEM_PROMPT

    if context:
        # Inject context into the template
        if "{context}" in prompt_template:
            return prompt_template.format(context=context)
        else:
            # If template doesn't have {context}, append it
            return f"{prompt_template}\n\n{context}"

    # Remove context placeholder if no context provided
    if "{context}" in prompt_template:
        return prompt_template.format(context="")
    return prompt_template


def get_suggested_prompts(channel_topic: str | None = None) -> list[dict[str, str]]:
    """Get suggested prompts based on channel context.

    Args:
        channel_topic: Optional channel topic/description for filtering

    Returns:
        List of suggested prompt dicts with title and description
    """
    prompts = []

    # Always include basic prompts
    for key in ["summarize", "question", "brainstorm", "explain"]:
        if key in SUGGESTED_PROMPTS_TEMPLATES:
            template = SUGGESTED_PROMPTS_TEMPLATES[key]
            prompts.append(
                {
                    "title": template["title"],
                    "description": template["description"],
                }
            )

    # Add channel-specific prompts if topic matches
    if channel_topic:
        topic_lower = channel_topic.lower()

        if any(
            keyword in topic_lower
            for keyword in [
                "engineering",
                "dev",
                "code",
                "tech",
                "backend",
                "frontend",
            ]
        ):
            if "code_review" in SUGGESTED_PROMPTS_TEMPLATES:
                template = SUGGESTED_PROMPTS_TEMPLATES["code_review"]
                prompts.insert(
                    0,
                    {
                        "title": template["title"],
                        "description": template["description"],
                    },
                )

        if any(keyword in topic_lower for keyword in ["design", "ui", "ux", "product", "visual"]):
            if "design_feedback" in SUGGESTED_PROMPTS_TEMPLATES:
                template = SUGGESTED_PROMPTS_TEMPLATES["design_feedback"]
                prompts.insert(
                    0,
                    {
                        "title": template["title"],
                        "description": template["description"],
                    },
                )

    return prompts


def format_for_slack(response_text: str) -> str:
    """Format LLM response for optimal display in Slack.

    Converts markdown formatting to Slack-compatible format and preserves mentions.

    Args:
        response_text: Raw LLM response text

    Returns:
        Slack-formatted response text
    """
    if not response_text:
        return ""

    # Preserve Slack mentions (already in @user format)
    # Slack markdown supports: bold, italic, code, lists, etc.
    # Most markdown maps directly to Slack format

    # Convert markdown code blocks to Slack format
    # ``` code ``` already works in Slack

    # Ensure proper spacing for readability
    formatted = response_text.strip()

    # Limit consecutive blank lines to 2
    while "\n\n\n" in formatted:
        formatted = formatted.replace("\n\n\n", "\n\n")

    return formatted


def trim_messages_for_context(
    messages: list[dict[str, str]],
    max_tokens: int = 4000,
) -> list[dict[str, str]]:
    """Trim conversation history to fit within token limit.

    Keeps recent messages and removes older ones while maintaining conversation flow.
    Rough estimate: ~4 characters per token for English text.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        max_tokens: Maximum tokens allowed for context (default 4000)

    Returns:
        Trimmed message list that fits within token limit
    """
    if not messages:
        return []

    # Rough estimate of tokens (4 chars per token)
    max_chars = max_tokens * 4

    # Calculate current size
    current_size = sum(len(m.get("content", "")) for m in messages)

    if current_size <= max_chars:
        return messages

    logger.warning(
        "Trimming %d messages from %d to %d chars",
        len(messages),
        current_size,
        max_chars,
    )

    # Keep the first system message and latest messages
    trimmed = []
    chars_used = 0

    # Preserve important context messages from the beginning
    for msg in messages[:3]:  # Keep first 3 messages (usually includes context)
        msg_size = len(msg.get("content", ""))
        trimmed.append(msg)
        chars_used += msg_size

    # Add messages from the end (most recent) until we hit the limit
    for msg in reversed(messages[3:]):
        msg_size = len(msg.get("content", ""))
        if chars_used + msg_size <= max_chars:
            trimmed.insert(len(trimmed) - len(messages[:3]), msg)
            chars_used += msg_size

    return trimmed if trimmed else messages[:1]  # Always return at least one message


def estimate_tokens(text: str) -> int:
    """Estimate token count for text (rough approximation).

    Uses simple heuristic: approximately 4 characters per token.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // 4


def build_message_context(
    user_message: str,
    channel_context: str | None = None,
    thread_context: str | None = None,
) -> str:
    """Build rich context string from various sources.

    Args:
        user_message: The actual user message
        channel_context: Optional channel-level context
        thread_context: Optional thread-level context

    Returns:
        Formatted context string for inclusion in prompts
    """
    parts = []

    if channel_context:
        parts.append(f"Channel context:\n{channel_context}")

    if thread_context:
        parts.append(f"Thread context:\n{thread_context}")

    if user_message:
        parts.append(f"User message:\n{user_message}")

    return "\n\n".join(parts)
