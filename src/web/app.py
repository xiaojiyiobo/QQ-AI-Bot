from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from bot.qq.messages import parse_qq_message
from bot.qq.onebot import QQOneBot
from core.handlers import MessageHandler
from web.admin import router

platform = QQOneBot()


async def bot_loop(app: FastAPI, handler: MessageHandler) -> None:
    delays = (2, 5, 10, 30)
    attempt = 0
    while True:
        try:
            app.state.onebot_status = "connecting"
            print(f"Connecting to {platform.ws_url} ...")
            async with platform.connect() as ws:
                app.state.onebot_status = "connected"
                app.state.last_error = None
                attempt = 0
                print("Connected. Waiting for QQ messages...")
                try:
                    await ws.send(json.dumps({"action": "get_status", "params": {}, "echo": "qq-ai-bot-status"}))
                except Exception:
                    pass
                async for raw in ws:
                    try:
                        event = json.loads(raw)
                        if event.get("echo") == "qq-ai-bot-status":
                            app.state.qq_online = bool((event.get("data") or {}).get("online"))
                            continue
                        app.state.last_message_at = datetime.now().isoformat(timespec="seconds")
                        await handler.handle(event, parse_qq_message)
                    except Exception as exc:
                        app.state.last_error = f"{type(exc).__name__}: message handling failed"
                        print(f"[BOT EVENT ERROR] type={type(exc).__name__}")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            app.state.onebot_status = "disconnected"
            app.state.qq_online = None
            app.state.last_error = f"{type(exc).__name__}: OneBot connection failed"
            delay = delays[min(attempt, len(delays) - 1)]
            attempt += 1
            print(f"[ONEBOT] Disconnected: type={type(exc).__name__}; retry in {delay}s")
            await asyncio.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bot_status = "starting"
    app.state.onebot_status = "disconnected"
    app.state.qq_online = None
    app.state.last_message_at = None
    app.state.last_error = None
    task: asyncio.Task | None = None

    async def stop_bot() -> None:
        nonlocal task
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            task = None
        app.state.bot_status = "stopped"
        app.state.onebot_status = "disconnected"

    async def start_bot() -> None:
        nonlocal task
        await stop_bot()
        load_dotenv(os.getenv("CONFIG_FILE_PATH", ".env"), override=True)
        try:
            handler = MessageHandler(platform=platform)
        except RuntimeError as exc:
            app.state.bot_status = "disabled"
            app.state.last_error = str(exc)
            print(f"[AI] Bot disabled: {exc}")
            print("[AI] Admin panel remains available; configure the API key and restart the bot.")
            return
        except Exception as exc:
            app.state.bot_status = "error"
            app.state.last_error = f"{type(exc).__name__}: initialization failed"
            print(f"[BOT] Initialization failed: type={type(exc).__name__}")
            return
        app.state.bot_status = "running"
        task = asyncio.create_task(bot_loop(app, handler), name="qq-bot")

    app.state.start_bot = start_bot
    app.state.stop_bot = stop_bot
    await start_bot()
    try:
        yield
    finally:
        await stop_bot()


app = FastAPI(title="QQ AI Bot Admin", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(router)


@app.get("/health")
async def health(request: Request):
    return JSONResponse({
        "status": "ok",
        "bot": getattr(request.app.state, "bot_status", "unknown"),
        "onebot": getattr(request.app.state, "onebot_status", "unknown"),
        "qq_online": getattr(request.app.state, "qq_online", None),
        "last_message_at": getattr(request.app.state, "last_message_at", None),
        "last_error": getattr(request.app.state, "last_error", None),
    })


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
