"""
Basic unit tests for the rule-based fallback AI service and helpers.
Run with: python -m pytest tests/ -v   (or) python -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.ai_service import AIService
from utils.helpers import is_valid_email, is_strong_password


class TestAIServiceFallback(unittest.TestCase):
    def setUp(self):
        # No API key -> forces the rule-based fallback path
        self.ai = AIService(api_key="")

    def test_classify_refund(self):
        result = self.ai.classify_email("Refund request", "I want my money back please")
        self.assertEqual(result, "Refund")

    def test_classify_technical(self):
        result = self.ai.classify_email("App broken", "The app keeps crashing with an error")
        self.assertEqual(result, "Technical Issue")

    def test_sentiment_negative(self):
        result = self.ai.analyze_sentiment("This is terrible, I am so disappointed and angry")
        self.assertEqual(result, "Negative")

    def test_sentiment_positive(self):
        result = self.ai.analyze_sentiment("Thank you so much, great service, I love it!")
        self.assertEqual(result, "Positive")

    def test_spam_detection(self):
        self.assertTrue(self.ai.detect_spam("You are a WINNER", "Click here to claim your free money now!"))
        self.assertFalse(self.ai.detect_spam("Order issue", "My package has not arrived yet"))

    def test_priority_high_for_urgent(self):
        result = self.ai.predict_priority("URGENT", "This is an emergency, please help immediately")
        self.assertEqual(result, "High")

    def test_generate_reply_returns_text(self):
        reply = self.ai.generate_reply("Refund", "I need a refund for my order", "John")
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 10)

    def test_analyze_email_returns_all_keys(self):
        result = self.ai.analyze_email("Shipping delay", "My package delivery is very late")
        for key in ("sentiment", "category", "is_spam", "priority", "summary"):
            self.assertIn(key, result)


class TestHelpers(unittest.TestCase):
    def test_valid_email(self):
        self.assertTrue(is_valid_email("user@example.com"))
        self.assertFalse(is_valid_email("not-an-email"))

    def test_strong_password(self):
        self.assertTrue(is_strong_password("secret1"))
        self.assertFalse(is_strong_password("abc"))


if __name__ == "__main__":
    unittest.main()
