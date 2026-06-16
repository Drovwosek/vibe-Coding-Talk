# Python Prompt Validation

Pattern: sanitize external payloads at the boundary, validate relationships explicitly, and build prompts from editable markdown templates.

~~~python
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
    if not topic:
        raise ValueError("Укажите тему публикации.")
~~~

New prompt inputs should follow the same model: normalize strings with length limits, fail with clear Russian messages, and keep prompt text in postovaya/agents/*.md.
