# Backend Anti-Patterns

## HTTP handlers doing product logic

BAD: build prompts, choose providers, or parse model responses directly inside AppHandler.do_POST.

GOOD: add a pure handler in postovaya/prompts.py or postovaya/openai_service.py, then register it in the route table.

## Unbounded payload fields

BAD:

~~~python
topic = payload.get("topic")
materials = payload.get("materials")
~~~

GOOD:

~~~python
topic = text(payload.get("topic"), 500)
materials = text(payload.get("materials"), 12000)
~~~

## Silent cross-venue audience use

BAD: accept any audience.id selected by the browser.

GOOD: validate venue.id == audience.venueId on the backend before building a prompt.

## Leaking provider internals to users

BAD: return raw API errors or stack traces.

GOOD: catch provider errors, truncate noisy details with text(message, 500), and return localized errors through send_json.
