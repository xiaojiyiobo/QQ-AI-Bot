from dataclasses import dataclass


MAX_TURNS = 10


@dataclass(slots=True)
class ConversationMemory:
    messages: list[dict[str, str]]

    def __init__(self) -> None:
        self.messages = []

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        max_messages = MAX_TURNS * 2
        if len(self.messages) > max_messages:
            del self.messages[:-max_messages]

    def history(self) -> list[dict[str, str]]:
        return list(self.messages)


class MemoryManager:
    def __init__(self) -> None:
        self._conversations: dict[tuple[str, int], ConversationMemory] = {}

    def get(self, platform: str, user_id: int) -> ConversationMemory:
        key = (platform, user_id)
        if key not in self._conversations:
            self._conversations[key] = ConversationMemory()
        return self._conversations[key]
