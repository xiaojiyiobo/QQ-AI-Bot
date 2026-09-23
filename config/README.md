# Local configuration

Create a local `.env` file from `.env.example` and fill in the API keys you actually use.

- `GEMINI_API_KEY` — required when `AI_PROVIDER=gemini`.
- `MISTRAL_API_KEY` — required when `AI_PROVIDER=mistral`.
- Keep `.env` local; it is intentionally ignored by Git.
- Never paste API keys into source code, README files, tests, screenshots, Git commits, or chat logs.
