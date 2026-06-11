import unittest

from postovaya.prompts import build_prompt
from tests.fixtures import PAYLOAD


class PromptTests(unittest.TestCase):
    def test_prompt_contains_business_context(self):
        prompt = build_prompt(PAYLOAD)
        self.assertIn("Север", prompt)
        self.assertIn("Офисные команды", prompt)
        self.assertIn("Новое обеденное меню", prompt)
        self.assertIn("Афиша: короткий хук", prompt)
        self.assertIn("Не придумывай", prompt)
        self.assertNotIn("Желаемая длина", prompt)

    def test_topic_is_required(self):
        payload = dict(PAYLOAD, topic="")
        with self.assertRaisesRegex(ValueError, "тему"):
            build_prompt(payload)

    def test_input_is_bounded(self):
        payload = dict(PAYLOAD, materials="x" * 13000)
        self.assertLess(len(build_prompt(payload)), 15000)

    def test_audience_must_belong_to_venue(self):
        payload = dict(PAYLOAD, audience={**PAYLOAD["audience"], "venueId": "venue-2"})
        with self.assertRaisesRegex(ValueError, "не относится"):
            build_prompt(payload)


if __name__ == "__main__":
    unittest.main()

