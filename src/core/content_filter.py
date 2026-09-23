import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FilterRule:
    keyword: str
    action: str
    replacement: str = ""


class ContentFilter:
    """Filter text before it is sent back to a platform."""

    def __init__(self, config_path: str | None = None) -> None:
        default_path = (
            Path(__file__).resolve().parents[2]
            / "config"
            / "content_filter.json"
        )
        self.config_path = Path(
            config_path or os.getenv("CONTENT_FILTER_CONFIG", default_path)
        )
        self.enabled = False
        self.rules: list[FilterRule] = []
        self._load()

    def _load(self) -> None:
        if not self.config_path.is_file():
            return

        with self.config_path.open("r", encoding="utf-8-sig") as f:
            config = json.load(f)

        self.enabled = bool(config.get("enabled", False))
        rules: list[FilterRule] = []

        for item in config.get("rules", []):
            keyword = str(item.get("keyword", ""))
            action = str(item.get("action", "replace")).lower()
            replacement = str(item.get("replacement", ""))

            if not keyword or action not in {"replace", "mask", "remove"}:
                continue

            rules.append(FilterRule(keyword, action, replacement))

        # Match longer phrases first so a specific phrase is handled
        # before a shorter keyword contained inside it.
        self.rules = sorted(rules, key=lambda rule: len(rule.keyword), reverse=True)

    def apply(self, text: str) -> str:
        if not self.enabled or not text:
            return text

        result = text
        for rule in self.rules:
            pattern = re.escape(rule.keyword)
            if rule.action == "replace":
                result = re.sub(pattern, lambda _: rule.replacement, result, flags=re.IGNORECASE)
            elif rule.action == "remove":
                result = re.sub(pattern, "", result, flags=re.IGNORECASE)
            elif rule.action == "mask":
                replacement = rule.replacement or "xx"
                result = re.sub(pattern, lambda _: replacement, result, flags=re.IGNORECASE)

        return result
