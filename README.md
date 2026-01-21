# Slack Bot that automates part of Leo Simons' (lsimons) work at Schuberg Philis

This is a Python AI bot for Schuberg Philis Slack workspace, providing AI assistant capabilities integrated with Slack's Assistant API and LiteLLM proxy for LLM access.

![Screenshot of lsimons-bot](docs/screenshot.png)

# Setup for development

## Install Dependencies

* [slack cli](https://slack.dev/cli/)
* [uv](https://pypi.org/project/uv/)
* [basedpyright](https://pypi.org/project/basedpyright/)


```bash
uv python install
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## Configure Environment Variables

```bash
cp .env.exmaple .env
```

## Slack App Configuration

```bash
slack help
```

The `manifest.json` file is the initial config, but ongoing changes are made through the web settings:

```bash
slack app settings
```

# Development

See [AGENTS.md] for development guidelines, including:
- Project structure and organization
- Testing and code quality standards
- Git workflow and commit conventions

## Running the bot

```bash
uv run --env-file .env ./app.py
```

## Formatting, Linting, Tests

```bash
# Format code
uv run black .

# Run linting
uv run flake8 app.py lsimons_bot tests
uv run basedpyright app.py lsimons_bot

# Run all tests
uv run pytest .

# Run with coverage
uv run pytest . --cov=lsimons_bot
```

## Documentation

See [docs] for additional documentation:
- [docs/spec/000-shared-patterns.md] - Common code patterns
- [docs/spec/001-spec-based-development.md] - How to write and implement specs
- [docs/spec/002-slack-client.md] - Slack integration architecture

Reference docs for slack api:
- [async app docs](https://docs.slack.dev/tools/bolt-python/reference/async_app.html)
- [async web client docs](https://docs.slack.dev/tools/python-slack-sdk/reference/web/async_client.html)
- [slack api methods](https://api.slack.com/methods)

## License

See [LICENSE.md] for license information. The original Slack template is MIT licensed, while new code is private.
