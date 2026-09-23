from dataclasses import dataclass


@dataclass(slots=True)
class IncomingMessage:
    platform: str
    user_id: int
    text: str = ""
    image_file: str | None = None
