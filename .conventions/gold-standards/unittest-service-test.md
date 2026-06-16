# Unittest Service Test

Pattern: tests use standard-library unittest, patch environment per test, and mock network calls at the urllib.request.urlopen boundary.

~~~python
class OpenAIServiceTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_demo_mode_without_api_key(self):
        result = generate_post(PAYLOAD)
        self.assertTrue(result["demo"])
        self.assertIn("Демо-черновик", result["text"])
        self.assertNotIn("OPENAI_API_KEY", result["text"])

    @patch("postovaya.openai_service.urllib.request.urlopen")
    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}, clear=True)
    def test_generates_with_groq_responses_api(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps({"output": [{
            "type": "message",
            "content": [{"type": "output_text", "text": "Готовый пост"}],
        }]}).encode("utf-8")

        result = generate_post(PAYLOAD)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.groq.com/openai/v1/responses")
        self.assertEqual(result["provider"], "groq")
~~~

Add tests beside the behavior they protect. Keep fixtures in tests/fixtures.py when multiple test files need the same payload.
