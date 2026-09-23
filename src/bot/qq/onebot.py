import json
import mimetypes
import os
import urllib.request
import uuid
from contextlib import asynccontextmanager

import websockets
from dotenv import load_dotenv

load_dotenv()


class QQOneBot:
    platform_name = "qq"

    def __init__(self) -> None:
        self.ws_url = os.getenv("ONEBOT_WS_URL", "ws://127.0.0.1:6700")

    @asynccontextmanager
    async def connect(self):
        async with websockets.connect(self.ws_url) as ws:
            yield ws

    async def events(self, ws):
        async for raw in ws:
            yield json.loads(raw)

    async def send_text(self, user_id: int, message: str) -> None:
        echo = f"qq-ai-bot-reply-{uuid.uuid4().hex}"

        async with websockets.connect(self.ws_url) as ws:
            await ws.send(json.dumps({
                "action": "send_msg",
                "params": {
                    "message_type": "private",
                    "user_id": user_id,
                    "message": message,
                },
                "echo": echo,
            }, ensure_ascii=False))

            async for raw in ws:
                result = json.loads(raw)
                if result.get("echo") == echo:
                    if result.get("retcode") != 0:
                        raise RuntimeError(f"OneBot send_msg failed: {result}")
                    return

        raise RuntimeError("OneBot send_msg response timeout")

    async def get_image(self, file_id: str) -> tuple[bytes, str]:
        echo = f"get-image-{uuid.uuid4().hex}"

        async with websockets.connect(self.ws_url) as ws:
            await ws.send(json.dumps({
                "action": "get_image",
                "params": {"file": file_id},
                "echo": echo,
            }, ensure_ascii=False))

            async for raw in ws:
                result = json.loads(raw)
                if result.get("echo") != echo:
                    continue

                if result.get("retcode") != 0 or result.get("status") != "ok":
                    raise RuntimeError(f"NapCat get_image failed: {result}")

                data = result.get("data") or {}
                path = data.get("file") or data.get("path")
                url = data.get("url")
                file_name = data.get("file_name") or path or ""
                guessed_mime = mimetypes.guess_type(file_name)[0]

                if path and os.path.isfile(path):
                    with open(path, "rb") as f:
                        image_data = f.read()
                    return (
                        image_data,
                        guessed_mime or data.get("type") or "image/jpeg",
                    )

                if url:
                    with urllib.request.urlopen(url, timeout=30) as response:
                        image_data = response.read()
                        response_mime = (
                            response.headers.get("Content-Type", "image/jpeg")
                            .split(";")[0]
                            .strip()
                        )
                    return (
                        image_data,
                        guessed_mime or response_mime or "image/jpeg",
                    )

                raise RuntimeError(
                    f"NapCat get_image returned no usable path/url: {data}"
                )

        raise RuntimeError("NapCat get_image response timeout")
