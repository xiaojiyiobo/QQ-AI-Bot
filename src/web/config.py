from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


class ConfigManager:
    def __init__(self, env_path: str | Path = ".env") -> None:
        self.env_path = Path(env_path)

    def values(self) -> dict[str, str]:
        values = dotenv_values(self.env_path)
        return {key: value or "" for key, value in values.items() if key}

    def safe_view(self) -> dict[str, str | bool]:
        values = self.values()
        return {
            "provider": values.get("AI_PROVIDER", "gemini"),
            "gemini_model": values.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            "mistral_model": values.get("MISTRAL_MODEL", "mistral-small-latest"),
            "mistral_vision_model": values.get("MISTRAL_VISION_MODEL", "ministral-14b-2512"),
            "onebot_ws_url": values.get("ONEBOT_WS_URL", "ws://127.0.0.1:6700"),
            "napcat_webui_url": values.get("NAPCAT_WEBUI_BROWSER_URL", "http://127.0.0.1:6099/webui/"),
            "content_filter_config": values.get("CONTENT_FILTER_CONFIG", "config/content_filter.json"),
            "gemini_key_configured": bool(values.get("GEMINI_API_KEY")),
            "mistral_key_configured": bool(values.get("MISTRAL_API_KEY")),
        }

    def update(self, provider: str, gemini_model: str, mistral_model: str, mistral_vision_model: str) -> None:
        provider = provider.strip().lower()
        if provider not in {"gemini", "mistral"}:
            raise ValueError("Provider must be gemini or mistral")

        original = self.env_path.read_text(encoding="utf-8") if self.env_path.exists() else ""
        lines = original.splitlines()
        updates = {
            "AI_PROVIDER": provider,
            "GEMINI_MODEL": gemini_model.strip(),
            "MISTRAL_MODEL": mistral_model.strip(),
            "MISTRAL_VISION_MODEL": mistral_vision_model.strip(),
        }
        seen: set[str] = set()
        output: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                output.append(line)
                continue
            key = line.split("=", 1)[0].strip()
            if key in updates:
                output.append(f"{key}={updates[key]}")
                seen.add(key)
            else:
                output.append(line)
        for key, value in updates.items():
            if key not in seen:
                output.append(f"{key}={value}")
        self.env_path.write_text("\n".join(output) + "\n", encoding="utf-8")
