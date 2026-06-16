from pathlib import Path


AGENTS_DIR = Path(__file__).resolve().parent / "agents"


def load_prompt_template(name):
    return (AGENTS_DIR / name).read_text(encoding="utf-8").strip()


def text(value, limit):
    if value is None:
        return ""
    return str(value).strip()[:limit]


def validate_venue_audience(venue, audience):
    venue_id = text(venue.get("id"), 120)
    audience_venue_id = text(audience.get("venueId"), 120)
    if not venue_id:
        raise ValueError("У заведения отсутствует идентификатор.")
    if not audience_venue_id:
        raise ValueError("Аудитория не привязана к заведению.")
    if venue_id != audience_venue_id:
        raise ValueError("Выбранная аудитория не относится к этому заведению.")


def build_prompt(payload):
    venue = payload.get("venue") or {}
    audience = payload.get("audience") or {}
    topic = text(payload.get("topic"), 500)
    materials = text(payload.get("materials"), 12000)
    post_style = text(payload.get("postStyle"), 180) or "фирменная публикация"

    if not topic:
        raise ValueError("Укажите тему публикации.")
    if not text(venue.get("name"), 120):
        raise ValueError("Выберите заведение.")
    if not text(audience.get("name"), 120):
        raise ValueError("Выберите сегмент аудитории.")
    validate_venue_audience(venue, audience)

    return load_prompt_template("post_generation_prompt.md").format(
        venue_name=text(venue.get("name"), 120),
        venue_description=text(venue.get("description"), 1200) or "не указаны",
        venue_voice=text(venue.get("voice"), 600) or "дружелюбный, конкретный, без канцелярита",
        venue_positioning=text(venue.get("positioning"), 800) or "не указано",
        audience_name=text(audience.get("name"), 120),
        audience_description=text(audience.get("description"), 1200) or "не указано",
        audience_needs=text(audience.get("needs"), 800) or "не указано",
        topic=topic,
        post_style=post_style,
        materials=materials or "Дополнительные материалы не приложены.",
    )


VENUE_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "positioning": {"type": "string"},
        "voice": {"type": "string"},
        "known_facts": {"type": "array", "items": {"type": "string"}},
        "content_pillars": {"type": "array", "items": {"type": "string"}},
        "recommended_styles": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "name", "description", "positioning", "voice", "known_facts",
        "content_pillars", "recommended_styles", "uncertainties",
    ],
    "additionalProperties": False,
}
