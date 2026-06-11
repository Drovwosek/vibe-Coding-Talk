import os
import unittest
from unittest.mock import patch

from postovaya.openai_service import (
    extract_output_text,
    extract_sources,
    generate_post,
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

    @patch.dict(os.environ, {}, clear=True)
    def test_demo_mode_without_api_key(self):
        result = generate_post(PAYLOAD)
        self.assertTrue(result["demo"])
        self.assertIn("Демо-черновик", result["text"])

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

