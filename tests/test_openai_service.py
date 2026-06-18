import json
import os
import unittest
from unittest.mock import patch

from postovaya.openai_service import (
    extract_chat_output_text,
    extract_output_text,
    extract_sources,
    generate_post,
    generation_provider,
    research_venue,
)
from tests.fixtures import PAYLOAD


class OpenAIServiceTests(unittest.TestCase):
    def test_extracts_all_message_text(self):
        response = {"output": [
            {"type": "reasoning", "content": []},
            {"type": "message", "content": [
                {"type": "output_text", "text": "Первая часть"},
                {"type": "output_text", "text": "Вторая часть"},
            ]},
        ]}
        self.assertEqual(extract_output_text(response), "Первая часть\nВторая часть")

    def test_extracts_chat_completion_text(self):
        response = {"choices": [
            {"message": {"content": "Привет"}},
            {"message": {"content": [{"text": "Мир"}]}},
        ]}
        self.assertEqual(extract_chat_output_text(response), "Привет\nМир")

    @patch.dict(os.environ, {}, clear=True)
    def test_demo_mode_without_api_key(self):
        result = generate_post(PAYLOAD)
        self.assertTrue(result["demo"])
        self.assertIn("Демо-черновик", result["text"])
        self.assertNotIn("OPENAI_API_KEY", result["text"])

    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}, clear=True)
    def test_uses_groq_when_its_key_is_configured(self):
        provider = generation_provider()
        self.assertEqual(provider["name"], "groq")
        self.assertEqual(provider["model"], "openai/gpt-oss-20b")

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=True)
    def test_uses_openrouter_free_router(self):
        provider = generation_provider()
        self.assertEqual(provider["name"], "openrouter")
        self.assertEqual(provider["model"], "openrouter/free")
        self.assertEqual(provider["url"], "https://openrouter.ai/api/v1/responses")

    @patch.dict(os.environ, {"APINET_API_KEY": "test-key"}, clear=True)
    def test_uses_apinet_when_its_key_is_configured(self):
        provider = generation_provider()
        self.assertEqual(provider["name"], "apinet")
        self.assertEqual(provider["model"], "qwen3-vl-plus")
        self.assertEqual(provider["url"], "https://apinet.cloud/v1/chat/completions")
        self.assertEqual(provider["kind"], "chat_completions")

    @patch("postovaya.openai_service.urllib.request.urlopen")
    @patch.dict(os.environ, {"APINET_API_KEY": "test-key", "AI_PROVIDER": "apinet"}, clear=True)
    def test_generates_with_apinet_chat_completions(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps({
            "choices": [{
                "message": {"content": "Готовый пост"},
            }]
        }).encode("utf-8")

        result = generate_post(PAYLOAD)

        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://apinet.cloud/v1/chat/completions")
        self.assertEqual(body["model"], "qwen3-vl-plus")
        self.assertEqual(body["messages"][0]["role"], "system")
        self.assertEqual(body["messages"][1]["role"], "user")
        self.assertEqual(result["text"], "Готовый пост")
        self.assertEqual(result["provider"], "apinet")

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
        self.assertEqual(result["text"], "Готовый пост")
        self.assertEqual(result["provider"], "groq")

    def test_extracts_unique_sources(self):
        response = {"output": [{"action": {"sources": [
            {"title": "Официальный сайт", "url": "https://example.com"},
            {"title": "Дубль", "url": "https://example.com"},
        ]}}]}
        self.assertEqual(extract_sources(response), [
            {"title": "Официальный сайт", "url": "https://example.com"}
        ])

    def test_research_requires_name(self):
        with self.assertRaisesRegex(ValueError, "название"):
            research_venue({"name": ""})


if __name__ == "__main__":
    unittest.main()
