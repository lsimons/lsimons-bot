from slack_bolt.async_app import AsyncApp

from .app_home_opened import app_home_opened


def register(app: AsyncApp) -> None:
    _ = app.event("app_home_opened")(app_home_opened)
