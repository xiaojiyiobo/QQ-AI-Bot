import time
from dataclasses import dataclass

from ai.manager import AIManager
from core.content_filter import ContentFilter
from core.memory import MemoryManager
from core.message import IncomingMessage


PENDING_IMAGE_SECONDS = 30

HELP_TEXT = """你好！我是你的 AI 助手。

💬 直接发送文字，就可以和我聊天。
🖼️ 如果要让我识别图片，请先发图片，再发文字问题。
📌 单独发送图片不会进行识别。

发送 /help 可以再次查看这份说明。"""


@dataclass(slots=True)
class PendingImage:
    data: bytes
    mime_type: str
    created_at: float


class MessageHandler:
    def __init__(self, platform) -> None:
        self.platform = platform
        self.ai = AIManager()
        self.content_filter = ContentFilter()
        self.memory = MemoryManager()
        self.pending_images: dict[int, PendingImage] = {}
        self.first_seen_users: set[int] = set()

        print(f"[AI] Provider: {self.ai.provider_name}")
        print("[MEMORY] Max turns per user: 10")

    async def handle(self, event: dict, parser) -> None:
        message = parser(event)
        if message is None:
            return

        user_id = message.user_id
        is_first_use = user_id not in self.first_seen_users
        if is_first_use:
            self.first_seen_users.add(user_id)

        if message.text == "/help" and message.image_file is None:
            await self.platform.send_text(user_id, HELP_TEXT)
            return

        if message.image_file:
            await self._handle_image(message, is_first_use)
            return

        if not message.text:
            return

        if is_first_use:
            await self.platform.send_text(user_id, HELP_TEXT)

        pending = self.pending_images.get(user_id)
        if pending:
            age = time.monotonic() - pending.created_at
            if age <= PENDING_IMAGE_SECONDS:
                del self.pending_images[user_id]
                print(f"[IMAGE QUESTION] {message.text}")
                reply = await self._ask_vision(pending, message.text)
            else:
                del self.pending_images[user_id]
                reply, success = await self._ask_text(user_id, message.text)
                if success:
                    self._remember_text(user_id, message.text, reply)
        else:
            reply, success = await self._ask_text(user_id, message.text)
            if success:
                self._remember_text(user_id, message.text, reply)

        reply = self.content_filter.apply(reply)
        await self.platform.send_text(user_id, reply)
        print(f"[BOT] {reply}")

    async def _handle_image(self, message: IncomingMessage, is_first_use: bool) -> None:
        try:
            image_data, mime_type = await self.platform.get_image(message.image_file)
            print(f"[IMAGE] Downloaded {len(image_data)} bytes ({mime_type})")
        except Exception as exc:
            print(f"[IMAGE DOWNLOAD ERROR] {exc}")
            return

        if message.text:
            print(f"[IMAGE QUESTION] {message.text}")
            reply = await self._ask_vision(
                PendingImage(image_data, mime_type, time.monotonic()),
                message.text,
            )
            reply = self.content_filter.apply(reply)
            await self.platform.send_text(message.user_id, reply)
            print(f"[BOT] {reply}")
            return

        if is_first_use:
            await self.platform.send_text(message.user_id, HELP_TEXT)

        self.pending_images[message.user_id] = PendingImage(
            image_data, mime_type, time.monotonic()
        )
        print(f"[IMAGE] Saved for follow-up question ({PENDING_IMAGE_SECONDS}s)")

    async def _ask_text(self, user_id: int, text: str) -> tuple[str, bool]:
        conversation = self.memory.get("qq", user_id)
        messages = conversation.history()
        messages.append({"role": "user", "content": text})

        try:
            reply = await self.ai.chat(messages)
            return reply, True
        except Exception as exc:
            print(f"[AI ERROR] type={type(exc).__name__}")
            print(f"[AI ERROR] code={getattr(exc, 'code', None)}")
            print(f"[AI ERROR] status={getattr(exc, 'status', None)}")
            print(f"[AI ERROR] status_code={getattr(exc, 'status_code', None)}")
            print(f"[AI ERROR] message={getattr(exc, 'message', None)}")
            print(f"[AI ERROR] details={getattr(exc, 'details', None)}")
            return "[AI 请求失败，请检查 API Key、模型和网络。]", False

    def _remember_text(self, user_id: int, user_text: str, reply: str) -> None:
        conversation = self.memory.get("qq", user_id)
        conversation.add("user", user_text)
        conversation.add("assistant", reply)
        print(f"[MEMORY] Stored turn for user {user_id}")

    async def _ask_vision(self, image: PendingImage, question: str) -> str:
        try:
            return await self.ai.vision(
                image.data,
                image.mime_type,
                question or "请描述一下这张图片，并告诉我图片中有什么。",
            )
        except Exception as exc:
            print(f"[AI IMAGE ERROR] {exc}")
            return "[AI 图片理解请求失败，请稍后重试。]"
