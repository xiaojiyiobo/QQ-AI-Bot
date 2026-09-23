import re

from core.message import IncomingMessage

IMAGE_PATTERN = re.compile(r"\[CQ:image,([^\]]+)\]")


def parse_qq_message(event: dict) -> IncomingMessage | None:
    if event.get("post_type") != "message":
        return None
    if event.get("message_type") != "private":
        return None

    user_id = int(event["user_id"])
    raw_message = event.get("raw_message", "").strip()
    if not raw_message:
        return None

    match = IMAGE_PATTERN.search(raw_message)
    image_file = None

    if match:
        fields: dict[str, str] = {}
        for item in match.group(1).split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                fields[key] = value
        image_file = fields.get("file")

    text = IMAGE_PATTERN.sub("", raw_message).strip()

    return IncomingMessage(
        platform="qq",
        user_id=user_id,
        text=text,
        image_file=image_file,
    )
