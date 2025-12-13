import logging
from typing import Any

logger = logging.getLogger(__name__)


async def message(body: dict[str, Any]) -> None:
    event = body.get("event", {})
    text = event.get("text", "")
    logger.debug(">> message('%s',...)", text)

    # type = body.get("type", "")
    # if type in ["event_callback"]:
    #     logger.debug("ignoring %s message", type)
    #     return

    bot_id = event.get("bot_id", {})
    if bot_id:
        logger.debug("ignoring bot message")
        return

    logger.debug("todo handle message()")

    logger.debug("<< message()")
