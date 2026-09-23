from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from bot.qq.messages import parse_qq_message
from bot.qq.onebot import QQOneBot
from core.handlers import MessageHandler
from web.admin import router


platform = QQOneBot()
handler = MessageHandler(platform=platform)


async def bot_loop() -> None:
    print(f"Connecting to {platform.ws_url} ...")
    async with platform.connect() as ws:
        print("Connected. Waiting for QQ messages...")
        async for event in platform.events(ws):
            await handler.handle(event, parse_qq_message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(bot_loop(), name="qq-bot")
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


app = FastAPI(title="QQ AI Bot Admin", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(router)


async def serve() -> None:
    host = "127.0.0.1"
    port = 8080
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    print(f"Admin panel: http://{host}:{port}/admin/")
    await server.serve()


async def main() -> None:
    await serve()


if __name__ == "__main__":
    asyncio.run(main())
