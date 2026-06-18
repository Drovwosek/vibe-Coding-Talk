import json
import os
import urllib.error
import urllib.request

from . import DEFAULT_GROQ_MODEL, DEFAULT_MODEL, DEFAULT_OPENROUTER_MODEL
from .prompts import VENUE_PROFILE_SCHEMA, build_prompt, load_prompt_template, text


def extract_output_text(response):
    parts = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def extract_chat_output_text(response):
    parts = []
    for choice in response.get("choices", []):
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content)
            continue
        if isinstance(content, list):
            for item in content:
                if isinstance(item, str) and item.strip():
                    parts.append(item)
                elif isinstance(item, dict) and item.get("text"):
                    parts.append(item["text"])
    return "\n".join(parts).strip()


def extract_sources(response):
    sources = []
    seen = set()
    for item in response.get("output", []):
        action = item.get("action") or {}
        for source in action.get("sources", []):
            url = text(source.get("url"), 1000)
            if not url or url in seen:
                continue
            seen.add(url)
            sources.append({"title": text(source.get("title"), 300) or url, "url": url})
    return sources[:12]


def api_request(url, api_key, body, provider, timeout=90):
    if not api_key:
        raise RuntimeError("Для этой функции подключите API-ключ провайдера.")
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(detail).get("error", {}).get("message", detail)
        except json.JSONDecodeError:
            message = detail
        raise RuntimeError(provider + " API: " + text(message, 500))
    except urllib.error.URLError as error:
        raise RuntimeError("Не удалось подключиться к " + provider + " API: " + str(error.reason))


def chat_completion_request(url, api_key, body, provider, timeout=90):
    return api_request(url, api_key, body, provider, timeout)


def openai_request(body, timeout=90):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Для этой функции подключите OPENAI_API_KEY.")
    return api_request(
        "https://api.openai.com/v1/responses", api_key, body, "OpenAI", timeout
    )


def apinet_request(body, timeout=90):
    api_key = os.environ.get("APINET_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Для этой функции подключите APINET_API_KEY.")
    base_url = os.environ.get("APINET_BASE_URL", "https://apinet.cloud/v1").strip()
    url = base_url.rstrip("/") + "/chat/completions"
    return chat_completion_request(url, api_key, body, "Apinet", timeout)


def generation_provider():
    requested = os.environ.get("AI_PROVIDER", "").strip().lower()
    if requested not in ("", "openai", "groq", "openrouter", "apinet"):
        raise RuntimeError("AI_PROVIDER должен быть openai, groq, openrouter или apinet.")

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    apinet_key = os.environ.get("APINET_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    provider = requested or (
        "openrouter" if openrouter_key else "groq" if groq_key else "apinet" if apinet_key else "openai"
    )

    if provider == "openrouter":
        return {
            "name": "openrouter",
            "key": openrouter_key,
            "model": os.environ.get(
                "OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL
            ).strip() or DEFAULT_OPENROUTER_MODEL,
            "url": "https://openrouter.ai/api/v1/responses",
            "kind": "responses",
        }
    if provider == "groq":
        return {
            "name": "groq",
            "key": groq_key,
            "model": os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL,
            "url": "https://api.groq.com/openai/v1/responses",
            "kind": "responses",
        }
    if provider == "apinet":
        return {
            "name": "apinet",
            "key": apinet_key,
            "model": os.environ.get("APINET_MODEL", "qwen3-vl-plus").strip() or "qwen3-vl-plus",
            "url": os.environ.get("APINET_BASE_URL", "https://apinet.cloud/v1").strip().rstrip("/")
            + "/chat/completions",
            "kind": "chat_completions",
        }
    return {
        "name": "openai",
        "key": openai_key,
        "model": os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        "url": "https://api.openai.com/v1/responses",
        "kind": "responses",
    }


def research_venue(payload):
    name = text(payload.get("name"), 160)
    hint = text(payload.get("hint"), 500)
    if not name:
        raise ValueError("Укажите название заведения.")
    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    prompt = load_prompt_template("venue_research_prompt.md").format(
        name=name,
        hint=hint or "не указана",
    )
    result = openai_request({
        "model": model,
        "reasoning": {"effort": "medium"},
        "tools": [{"type": "web_search"}],
        "tool_choice": "auto",
        "include": ["web_search_call.action.sources"],
        "instructions": load_prompt_template("venue_research_instructions.md"),
        "input": prompt,
        "text": {"format": {
            "type": "json_schema", "name": "venue_profile", "strict": True,
            "schema": VENUE_PROFILE_SCHEMA,
        }},
    }, timeout=120)
    output = extract_output_text(result)
    if not output:
        raise RuntimeError("Исследование не вернуло профиль заведения.")
    try:
        profile = json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError("Не удалось разобрать профиль заведения.")
    return {"profile": profile, "sources": extract_sources(result), "model": model}


def demo_post(payload):
    venue = text((payload.get("venue") or {}).get("name"), 120)
    audience = text((payload.get("audience") or {}).get("name"), 120)
    topic = text(payload.get("topic"), 500)
    materials = text(payload.get("materials"), 400)
    detail = materials.splitlines()[0] if materials else "Добавьте факты в материалы, чтобы пост стал точнее."
    return (
        f"Демо-черновик для «{venue}»\n\n"
        f"{topic}\n\n"
        f"Этот пост ориентирован на аудиторию «{audience}». {detail}\n\n"
        "Проверьте факты и уточните детали перед публикацией."
    )


def generate_post(payload):
    prompt = build_prompt(payload)
    provider = generation_provider()
    if not provider["key"]:
        return {"text": demo_post(payload), "demo": True, "model": None}

    instructions = load_prompt_template("post_generation_instructions.md")
    if provider["kind"] == "chat_completions":
        result = apinet_request({
            "model": provider["model"],
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt},
            ],
        })
        output = extract_chat_output_text(result)
    else:
        result = api_request(provider["url"], provider["key"], {
            "model": provider["model"],
            "reasoning": {"effort": "low"},
            "instructions": instructions,
            "input": prompt,
        }, provider["name"].title())
        output = extract_output_text(result)
    if not output:
        raise RuntimeError("Модель не вернула текст публикации.")
    return {
        "text": output,
        "demo": False,
        "model": provider["model"],
        "provider": provider["name"],
    }
