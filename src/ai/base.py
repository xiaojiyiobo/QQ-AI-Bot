from abc import ABC, abstractmethod


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def vision(self, image_data: bytes, mime_type: str, prompt: str) -> str:
        raise NotImplementedError
