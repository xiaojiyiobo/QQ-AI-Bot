from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from bot.qq.messages import parse_qq_message
from bot.qq.onebot import QQOneBot
from core.handlers import MessageHandler
from web.admin import router


platform = QQOneBot()


async def bot_loop(handler: MessageHandler) -> None:
    print(f"Connecting to {platform.ws_url} ...")
    async with platform.connect() as ws:
        print("Connected. Waiting for QQ messages...")
        async for event in platform.events(ws):
            await handler.handle(event, parse_qq_message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bot_status = "starting"
    task: asyncio.Task | None = None

    try:
        handler = MessageHandler(platform=platform)
    except RuntimeError as exc:
        app.state.bot_status = "disabled"
        print(f"[AI] Bot disabled: {exc}")
        print("[AI] Admin panel will remain available. Configure the API key and restart the bot to enable QQ AI features.")
    except Exception as exc:
        app.state.bot_status = "error"
        print(f"[BOT] Initialization failed: type={type(exc).__name__}")
        print("[BOT] Admin panel will remain available; fix the configuration and restart the bot.")
    else:
        app.state.bot_status = "running"
        task = asyncio.create_task(bot_loop(handler), name="qq-bot")

    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        app.state.bot_status = "stopped"


app = FastAPI(title="QQ AI Bot Admin", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(router)


async def serve() -> None:
    host = os.getenv("ADMIN_HOST", "127.0.0.1")
    port = int(os.getenv("ADMIN_PORT", "8080"))
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    print(f"Admin panel: http://{host}:{port}/admin/")
    await server.serve()


async def main() -> None:
    await serve()


if __name__ == "__main__":
    asyncio.run(main())
