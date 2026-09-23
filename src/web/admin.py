from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from web.config import ConfigManager

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
config = ConfigManager()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "config": config.safe_view(),
            "bot_status": getattr(request.app.state, "bot_status", "unknown"),
            "saved": False,
        },
    )


@router.post("/config")
async def save_config(
    provider: str = Form(...),
    gemini_model: str = Form(...),
    mistral_model: str = Form(...),
    mistral_vision_model: str = Form(...),
):
    config.update(provider, gemini_model, mistral_model, mistral_vision_model)
    return RedirectResponse("/admin/?saved=1", status_code=303)
