# Decisions

## Stack

Use Python's standard HTTP server plus framework-free HTML, CSS, and JavaScript.

Reason: the machine already has Python 3.9 but no Node.js runtime. This keeps the first version runnable without dependency installation while preserving a clear boundary between browser UI and server-side AI access.

## Storage

Store profiles and drafts in `localStorage`. Keep uploaded images in memory as object URLs.

Audience profiles belong to one venue through `venueId`. Legacy global audiences are copied to each existing venue during browser-side migration so no saved portrait is lost. The server validates the venue/audience relationship on every generation request.

Reason: the first release is single-user and local-first. Images can be large, so silently persisting them in local storage would be unreliable.

## AI integration

Use an OpenAI-compatible Responses API from the server. Post generation supports OpenRouter (`OPENROUTER_API_KEY`), Groq (`GROQ_API_KEY`), or OpenAI (`OPENAI_API_KEY`); when multiple keys are present, `AI_PROVIDER` selects one. OpenRouter defaults to `openrouter/free`, while Groq defaults to `openai/gpt-oss-20b`, so the MVP can run on a free developer tier.

Venue research remains on OpenAI because it uses the hosted `web_search` tool and strict structured output. Findings remain a preview until the marketer confirms them. Sources and uncertainties are stored with the profile so inferred brand context is not presented as unquestioned truth.

## Post formats

Use venue-specific content formats rather than target character counts. Researched profiles receive formats inferred from their positioning and voice; older and manually created profiles fall back to a generic restaurant content set.

## Publishing

Provide copy-to-clipboard, not Telegram Bot API integration.

Reason: direct publishing introduces channel authorization and operational risk that is not part of the core problem for release one.

## VPN box delivery

Expose the VPN as two centered downloads, one for Windows and one for Mac, and generate per-platform zip packages on the server from a provided OpenVPN profile.

Reason: the user asked for a boxy, low-friction MVP for a very small audience. A download-only front door keeps the surface area tiny while still giving a single, obvious action.

## Code organization

Keep the zero-dependency runtime, but separate responsibilities by module. Browser storage, API access, and generic utilities live outside the UI coordinator. Python prompt validation, OpenAI integration, and HTTP transport live in separate package modules. Tests import the owning modules directly; `server.py` remains only a compatibility entry point.
