import os

from ai.base import AIProvider
from ai.providers.gemini import GeminiProvider
from ai.providers.mistral import MistralProvider


def create_provider() -> AIProvider:
    provider_name = os.getenv("AI_PROVIDER", "gemini").strip().lower()

    providers: dict[str, type[AIProvider]] = {
        "gemini": GeminiProvider,
        "mistral": MistralProvider,
    }

    provider_class = providers.get(provider_name)
    if provider_class is None:
        supported = ", ".join(sorted(providers))
        raise RuntimeError(
            f"Unsupported AI_PROVIDER={provider_name!r}. "
            f"Supported providers: {supported}"
        )

    return provider_class()


class AIManager:
    def __init__(self) -> None:
        self.provider = create_provider()
        self.provider_name = self.provider.name

    async def chat(self, messages: list[dict[str, str]]) -> str:
        return await self.provider.chat(messages)

    async def vision(
        self,
        image_data: bytes,
        mime_type: str,
        prompt: str,
    ) -> str:
        return await self.provider.vision(
            image_data,
            mime_type,
            prompt,
        )