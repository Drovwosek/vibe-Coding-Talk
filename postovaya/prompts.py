from pathlib import Path
from string import Formatter


AGENTS_DIR = Path(__file__).resolve().parent / "agents"
EDITABLE_PROMPTS = {
    "post_generation": {
        "title": "Генерация поста",
        "filename": "post_generation_prompt.md",
        "placeholders": {
            "venue_name": "Север",
            "venue_description": "Городское бистро",
            "venue_voice": "тёплый",
            "venue_positioning": "городское бистро рядом с офисами",
            "audience_name": "Офисные команды",
            "audience_description": "работают рядом",
            "audience_needs": "быстрый обед",
            "topic": "Новое обеденное меню",
            "post_style": "короткий анонс",
            "materials": "Будни, с 12:00 до 16:00",
        },
    },
    "venue_research": {
        "title": "Исследование заведения",
        "filename": "venue_research_prompt.md",
        "placeholders": {
            "name": "Север",
            "hint": "Москва, ресторан",
        },
    },
}


def load_prompt_template(name):
    return (AGENTS_DIR / name).read_text(encoding="utf-8").strip()


def validate_prompt_template(template, placeholders):
    try:
        used = {
            field_name.split(".", 1)[0].split("[", 1)[0]
            for _, field_name, _, _ in Formatter().parse(template)
            if field_name
        }
        unknown = sorted(used - set(placeholders))
        if unknown:
            raise ValueError("Неизвестные плейсхолдеры: " + ", ".join(unknown))
        template.format(**placeholders)
    except KeyError as error:
        raise ValueError("Не хватает плейсхолдера: " + str(error))
    except ValueError as error:
        raise ValueError("Ошибка шаблона промпта: " + str(error))


def editable_prompt_payload(key, config):
    return {
        "key": key,
        "title": config["title"],
        "filename": config["filename"],
        "content": load_prompt_template(config["filename"]),
    }


def get_editable_prompt_templates():
    return {
        "prompts": [
            editable_prompt_payload(key, config)
            for key, config in EDITABLE_PROMPTS.items()
        ]
    }


def update_editable_prompt_template(payload):
    key = text(payload.get("key"), 80)
    config = EDITABLE_PROMPTS.get(key)
    if not config:
        raise ValueError("Неизвестный промпт.")
    content = payload.get("content")
    if not isinstance(content, str):
        raise ValueError("Передайте текст промпта.")
    if not content.strip():
        raise ValueError("Промпт не может быть пустым.")
    if len(content) > 60_000:
        raise ValueError("Промпт слишком длинный.")
    validate_prompt_template(content, config["placeholders"])
    (AGENTS_DIR / config["filename"]).write_text(content.rstrip() + "\n", encoding="utf-8")
    return {"prompt": editable_prompt_payload(key, config)}


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
