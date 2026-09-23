import asyncio
import base64
import json
import os
import urllib.error
import urllib.request

from ai.base import AIProvider


class MistralProvider(AIProvider):
    name = "mistral"

    def __init__(self) -> None:
        api_key = os.getenv("MISTRAL_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "MISTRAL_API_KEY is not configured. Add it to .env."
            )

        self.model = os.getenv(
            "MISTRAL_MODEL",
            "mistral-small-latest",
        ).strip()

        self.vision_model = os.getenv(
            "MISTRAL_VISION_MODEL",
            "ministral-14b-2512",
        ).strip()

        self.timeout = 90

    def _request(self, endpoint: str, payload: dict) -> dict:
        request = urllib.request.Request(
            f"https://api.mistral.ai/v1/{endpoint}",
            data=json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={
                "Authorization": (
                    f"Bearer {os.environ['MISTRAL_API_KEY']}"
                ),
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                return json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.HTTPError as exc:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )
            raise RuntimeError(
                f"Mistral API HTTP {exc.code}: {body[:1000]}"
            ) from exc

    @staticmethod
    def _message_text(response: dict) -> str:
        for output in response.get("outputs", []):
            if output.get("type") != "message.output":
                continue

            content = output.get("content", "")

            if isinstance(content, str) and content.strip():
                return content.strip()

            if isinstance(content, list):
                parts: list[str] = []

                for item in content:
                    if item.get("type") in {
                        "text",
                        "output_text",
                    }:
                        text = item.get("text", "")
                        if text:
                            parts.append(text)

                if parts:
                    return "".join(parts).strip()

        raise RuntimeError(
            "Mistral returned no message text."
        )

    @staticmethod
    def _chat_messages(
        messages: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        result = []

        for message in messages:
            role = message.get("role", "user")

            if role not in {
                "system",
                "user",
                "assistant",
            }:
                role = "user"

            result.append(
                {
                    "role": role,
                    "content": message.get(
                        "content",
                        "",
                    ),
                }
            )

        return result

    def _chat_sync(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        payload = {
            "model": self.model,
            "inputs": self._chat_messages(messages),
            "tools": [
                {
                    "type": "web_search",
                }
            ],
            "store": False,
        }

        print(
            f"[AI mistral] "
            f"model={self.model} "
            f"web_search=enabled"
        )

        response = self._request(
            "conversations",
            payload,
        )

        used_search = any(
            output.get("type") == "tool.execution"
            and output.get("name") == "web_search"
            for output in response.get(
                "outputs",
                [],
            )
        )

        print(
            f"[AI mistral] "
            f"web_search_used={used_search}"
        )

        return self._message_text(response)

    def _vision_sync(
        self,
        image_data: bytes,
        mime_type: str,
        prompt: str,
    ) -> str:
        encoded = base64.b64encode(
            image_data
        ).decode("ascii")

        image_url = (
            f"data:{mime_type};base64,{encoded}"
        )

        payload = {
            "model": self.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": image_url,
                        },
                    ],
                }
            ],
        }

        print(
            f"[AI mistral IMAGE] "
            f"model={self.vision_model}"
        )

        response = self._request(
            "chat/completions",
            payload,
        )

        choices = response.get(
            "choices",
            [],
        )

        if not choices:
            raise RuntimeError(
                "Mistral vision returned no choices."
            )

        content = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )

        if (
            isinstance(content, str)
            and content.strip()
        ):
            return content.strip()

        raise RuntimeError(
            "Mistral vision returned no text."
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        return await asyncio.to_thread(
            self._chat_sync,
            messages,
        )

    async def vision(
        self,
        image_data: bytes,
        mime_type: str,
        prompt: str,
    ) -> str:
        return await asyncio.to_thread(
            self._vision_sync,
            image_data,
            mime_type,
            prompt,
        )