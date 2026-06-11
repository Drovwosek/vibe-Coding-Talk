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

    return f"""Подготовь один готовый пост для Telegram на русском языке.

Заведение:
- Название: {text(venue.get('name'), 120)}
- Описание и особенности: {text(venue.get('description'), 1200) or 'не указаны'}
- Голос бренда: {text(venue.get('voice'), 600) or 'дружелюбный, конкретный, без канцелярита'}
- Позиционирование: {text(venue.get('positioning'), 800) or 'не указано'}

Целевой сегмент:
- Название: {text(audience.get('name'), 120)}
- Кто эти люди: {text(audience.get('description'), 1200) or 'не указано'}
- Что для них важно: {text(audience.get('needs'), 800) or 'не указано'}

Задача публикации:
- Тема или инфоповод: {topic}
- Формат публикации: {post_style}

Материалы маркетолога:
{materials or 'Дополнительные материалы не приложены.'}

Требования:
1. Сразу выдай только финальный текст поста, без комментариев и заголовков от себя.
2. Опирайся только на предоставленные факты. Не придумывай цены, даты, адреса, состав блюд или условия акции.
3. Сделай начало заметным в ленте, но не используй кликбейт.
4. Покажи релевантную сегменту пользу через конкретику.
5. Используй короткие абзацы, подходящие для Telegram.
6. Эмодзи допустимы умеренно. Хэштеги добавляй только если они действительно полезны, не более трех.
7. Призыв к действию добавляй только если он естественно следует из темы и материалов.
8. Не упоминай, что текст создан ИИ."""


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

