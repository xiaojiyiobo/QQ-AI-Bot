from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from web.config import ConfigManager

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
config = ConfigManager()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    host = request.headers.get("host", "127.0.0.1:8080").split(":", 1)[0]
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    view = config.safe_view()
    view["napcat_webui_url"] = f"{scheme}://{host}:6099/webui/"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "config": view,
            "bot_status": getattr(request.app.state, "bot_status", "unknown"),
            "onebot_status": getattr(request.app.state, "onebot_status", "unknown"),
            "qq_online": getattr(request.app.state, "qq_online", None),
            "last_message_at": getattr(request.app.state, "last_message_at", None),
            "last_error": getattr(request.app.state, "last_error", None),
        },
    )


@router.post("/config")
async def save_config(
    request: Request,
    provider: str = Form(...),
    gemini_model: str = Form(...),
    mistral_model: str = Form(...),
    mistral_vision_model: str = Form(...),
    gemini_api_key: str = Form(""),
    mistral_api_key: str = Form(""),
    restart: str = Form("0"),
):
    config.update(provider, gemini_model, mistral_model, mistral_vision_model, gemini_api_key, mistral_api_key)
    load_dotenv(config.env_path, override=True)
    if restart == "1":
        await request.app.state.start_bot()
    return RedirectResponse("/admin/?saved=1", status_code=303)
