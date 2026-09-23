import asyncio
import os

from google import genai
from google.genai import types

from ai.base import AIProvider


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. Copy .env.example to .env and set the key."
            )

        self.model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
        self.client = genai.Client(api_key=api_key)

    @staticmethod
    def _content(response) -> str:
        return (response.text or "").strip() or "(模型没有返回文本)"

    @staticmethod
    def _contents(messages: list[dict[str, str]]) -> list[types.Content]:
        contents: list[types.Content] = []

        for message in messages:
            role = message.get("role", "user")
            if role == "assistant":
                role = "model"
            elif role != "model":
                role = "user"

            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=message.get("content", ""))],
                )
            )

        return contents

    @staticmethod
    def _status_code(exc: Exception) -> int | None:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            status_code = getattr(
                getattr(exc, "response", None), "status_code", None
            )
        return status_code

    def _chat_sync(
        self,
        messages: list[dict[str, str]],
        use_search: bool = True,
    ) -> str:
        config = None
        if use_search:
            config = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=self._contents(messages),
            config=config,
        )
        return self._content(response)

    def _vision_sync(self, image_data: bytes, mime_type: str, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        types.Part.from_bytes(
                            data=image_data,
                            mime_type=mime_type,
                        ),
                    ],
                )
            ],
        )
        return self._content(response)

    async def chat(self, messages: list[dict[str, str]]) -> str:
        # Do not silently fall back to non-grounded generation.
        # If Google Search grounding fails, the caller must see the failure
        # rather than receiving an answer from the model's static knowledge.
        return await asyncio.to_thread(self._chat_sync, messages, True)

    async def vision(self, image_data: bytes, mime_type: str, prompt: str) -> str:
        max_attempts = 2

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"[AI {self.name} IMAGE] Attempt {attempt}/{max_attempts}")
                return await asyncio.to_thread(
                    self._vision_sync, image_data, mime_type, prompt
                )
            except Exception as exc:
                status_code = self._status_code(exc)

                if (
                    status_code not in {408, 429, 500, 502, 503, 504}
                    or attempt == max_attempts
                ):
                    raise

                delay = 2 ** attempt
                print(
                    f"[AI {self.name} IMAGE] Temporary error "
                    f"{status_code}, retrying in {delay}s..."
                )
                await asyncio.sleep(delay)

        raise RuntimeError("AI image request failed after retries")
