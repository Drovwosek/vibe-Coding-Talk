# Testing Checks

- Run the suite with:

~~~bash
python3 -m unittest discover -s tests -v
~~~

- Use unittest.TestCase; do not add pytest-only patterns without adding and documenting the dependency.
- Patch environment with @patch.dict(os.environ, ..., clear=True) for provider selection tests.
- Mock network at postovaya.openai_service.urllib.request.urlopen; do not call real AI providers in tests.
- Put shared request payloads in tests/fixtures.py.
- For prompt changes, assert both required business context and safety instructions remain present in the rendered prompt.
- For validation changes, assert the localized ValueError message contains the key Russian word the UI/user needs.
