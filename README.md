# Telegram Post Studio

Local-first MVP for restaurant marketers who prepare audience-specific Telegram posts.

## What it does

- stores restaurant and audience profiles in the browser;
- keeps separate audience portraits for every venue and validates that relationship during generation;
- researches a venue from its name using sourced OpenAI web search and saves only after review;
- accepts a topic and source materials;
- offers venue-specific post formats instead of arbitrary target lengths;
- generates a Russian Telegram post with OpenRouter, Groq, OpenAI Responses API, or Apinet chat completions;
- keeps an optional image attached to the draft without sending it to AI;
- supports manual editing, copying, and draft history;
- works in demo mode when no API key is configured.

## Run

Python 3.9+ is the only runtime dependency.

```bash
cd /Users/kaban/codex/Projects/telegram-post-studio
export OPENAI_API_KEY="your-key"
python3 server.py
```

Open <http://127.0.0.1:8765>.

Optional configuration:

```bash
export OPENAI_MODEL="gpt-5.5"
export PORT="8765"
```

If you want to use the Apinet endpoint from your curl example, set:

```bash
export APINET_API_KEY="your-key"
export APINET_MODEL="qwen3-vl-plus"
export APINET_BASE_URL="https://apinet.cloud/v1"
export AI_PROVIDER="apinet"
python3 server.py
```

For free-tier post generation, use Groq instead:

```bash
export GROQ_API_KEY="your-key"
export GROQ_MODEL="openai/gpt-oss-20b"
python3 server.py
```

If Groq signup is unavailable, OpenRouter provides a free-model router:

```bash
export OPENROUTER_API_KEY="your-key"
export OPENROUTER_MODEL="openrouter/free"
python3 server.py
```

Set `AI_PROVIDER=apinet` when you want the Apinet chat-completions endpoint, or
`AI_PROVIDER=openai`, `AI_PROVIDER=groq`, or `AI_PROVIDER=openrouter` when
multiple keys are configured. OpenRouter, Groq, Apinet, or OpenAI handles post generation;
venue research still requires `OPENAI_API_KEY`
because that workflow relies on OpenAI hosted web search and strict structured output.

Without `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `APINET_API_KEY`, or `OPENAI_API_KEY`, the app returns a clearly marked demo post so the full UI can still be tested.
Venue research requires `OPENAI_API_KEY` because it uses the Responses API `web_search` tool.

## Deploy to Timeweb Cloud

The repository includes a `Dockerfile` for Timeweb Cloud App Platform.

Create the application in Timeweb Cloud:

1. Open **App Platform** and add an application of type **Dockerfile**.
2. Connect the GitHub repository `Drovwosek/codex` and select branch `main`.
3. Leave the project directory empty because the `Dockerfile` is in the repository root.
4. Set the health-check path to `/api/health`. The Docker image also includes a Python-based healthcheck compatible with the slim base image.
5. For free-tier generation, add `OPENROUTER_API_KEY` as a secret and optionally set `OPENROUTER_MODEL`. Groq remains supported through `GROQ_API_KEY`, and Apinet can be used with `APINET_API_KEY` plus `APINET_MODEL`; add `OPENAI_API_KEY` only if venue research is required.
6. Enable automatic deployment for new commits in `main`.

App Platform reads port `8080` from the `Dockerfile`. It supplies HTTPS and a technical domain after the first deployment.

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Structure

```text
postovaya/
  prompts.py          prompt construction and request validation
  openai_service.py   Responses API integration and response parsing
  http_app.py         HTTP routes and static file serving
web/
  js/store.js         local data, defaults, and migrations
  js/api.js           browser API client
  js/utils.js         shared browser utilities
  app.js              UI rendering and event coordination
```

`server.py` is a small compatibility entry point, so the run command remains unchanged.

## MVP boundaries

- one marketer on one browser;
- Telegram only;
- no direct Telegram publishing;
- no accounts or cloud database;
- no AI image generation;
- image attachments are kept only for the current browser session.
