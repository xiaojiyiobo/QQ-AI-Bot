# QQ AI Bot — AI/Agent Working Notes

## Purpose
Private QQ AI assistant for the owner and a very small number of trusted users. This repository is intended to remain simple, modular, and easy to deploy. Do not turn it into a public SaaS unless explicitly requested.

## Current validated capabilities
- QQ private messages through NapCat + OneBot 11 WebSocket.
- Text chat with provider abstraction.
- Gemini provider using Google's native GenAI SDK.
- Mistral provider using the Conversations API with built-in `web_search`.
- Image understanding with the provider abstraction.
- Per-platform/per-user in-memory conversation memory, currently 10 turns.
- Content filtering from `config/content_filter.json`.
- First-use `/help` message and image-then-question flow.
- Local admin page at `/admin/` for basic provider/model configuration.

## Current architecture
`platform adapter -> core handler -> AIManager -> provider`

QQ is the only implemented platform. Future platforms must be added as adapters; do not couple platform-specific behavior into `core` or `ai`.

AI providers live under `src/ai/providers/`. Add future providers by implementing `AIProvider` and registering them in `src/ai/manager.py`.

## Admin foundation
- `src/web/app.py` runs FastAPI and the QQ bot in the same process.
- `src/web/admin.py` contains admin routes.
- `src/web/config.py` owns `.env` configuration read/write logic.
- `src/web/templates/` and `src/web/static/` contain the minimal UI.
- Admin binds to `127.0.0.1:8080` by default. Do not expose it to the public Internet without authentication and explicit user approval.
- API keys are never displayed in the UI; only configured/not-configured status is shown.
- Saving provider/model settings writes `.env`; a process restart is currently required for the new provider/model to take effect.

## Important configuration
- `AI_PROVIDER=gemini|mistral`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `MISTRAL_API_KEY`
- `MISTRAL_MODEL`
- `MISTRAL_VISION_MODEL`
- `ONEBOT_WS_URL`
- `CONTENT_FILTER_CONFIG`

Never print, commit, or expose API keys. Never copy secret values into logs, README files, tests, screenshots, or chat responses.

## Development rules
1. Read this file before modifying the project.
2. Inspect the real files and runtime state before assuming architecture or configuration.
3. Prefer small, reversible changes and validate each stage before continuing.
4. Do not add future platform integrations merely to demonstrate extensibility.
5. Keep provider-specific code inside provider modules.
6. Keep secrets in `.env`; `.env` must never be committed.
7. Do not replace working behavior unless there is a concrete reason and a test/validation path.
8. Temporary test scripts belong in the sandbox or should be removed after validation.
9. Before deployment, add Linux/Docker support without changing the validated local behavior.
10. When changing startup behavior, test that exactly one bot instance is running to avoid duplicate QQ replies.

## Current run
From the project root, `run.bat` launches `src/main.py`. `AI_PROVIDER` selects the provider.

The application starts both the admin HTTP server and the QQ bot. Admin URL locally: `http://127.0.0.1:8080/admin/`.

## Deployment direction
Target deployment is a Linux S20M or VPS. Docker is planned, but should be introduced only after the current local version is stable and the admin foundation is validated.
