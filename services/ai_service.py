"""
AI Service
==========
Wraps all LLM-powered features for the support agent:
  - generate_reply()      -> professional reply draft
  - summarize_email()     -> short summary
  - analyze_sentiment()   -> Positive / Negative / Neutral
  - classify_email()      -> Complaint / Refund / Technical Issue / Payment / Shipping / General Query
  - detect_spam()         -> True / False
  - predict_priority()    -> High / Medium / Low
  - analyze_email()       -> runs all of the above in one call (used by routes/ai.py)

If config.OPENAI_API_KEY is empty, every method falls back to a lightweight
rule-based / keyword implementation so the whole project runs out of the box
without any external API key or cost. Swap in a real key and it automatically
starts using the OpenAI API instead.
"""

import re

try:
    from openai import OpenAI
except ImportError:  # library not installed yet
    OpenAI = None


class AIService:
    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key) if (api_key and OpenAI) else None

    # ------------------------------------------------------------------
    # Core LLM call helper
    # ------------------------------------------------------------------
    def _chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        if not self.client:
            return ""  # signals caller to use the mock fallback
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:  # network / auth / rate-limit errors
            print(f"[ai_service] OpenAI call failed, using fallback: {exc}")
            return ""

    # ------------------------------------------------------------------
    # 1. Reply generation
    # ------------------------------------------------------------------
    def generate_reply(self, subject: str, body: str, customer_name: str = "Customer") -> str:
        system_prompt = (
            "You are a professional customer support executive. "
            "Read the email carefully, then generate a polite, helpful reply. "
            "Keep the response under 150 words. Be friendly and professional. "
            "Sign off as 'Support Team'."
        )
        user_prompt = f"Customer: {customer_name}\nSubject: {subject}\nEmail:\n{body}"

        reply = self._chat(system_prompt, user_prompt, max_tokens=300)
        if reply:
            return reply
        return self._mock_reply(subject, body, customer_name)

    def _mock_reply(self, subject: str, body: str, customer_name: str) -> str:
        category = self.classify_email(subject, body)
        opening = f"Dear {customer_name}," if customer_name else "Hello,"
        templates = {
            "Complaint": "We're sorry to hear about the trouble you've experienced. "
                         "We take this seriously and are looking into it right away.",
            "Refund": "Thank you for reaching out about your refund. We're reviewing your "
                      "request and will process it as quickly as possible.",
            "Technical Issue": "Thanks for reporting this issue. Our technical team is "
                                "looking into it, and we'll update you shortly with a fix.",
            "Payment": "Thank you for contacting us about your payment. We're checking the "
                       "details on our end and will confirm shortly.",
            "Shipping": "Thanks for your patience regarding your shipment. We're tracking "
                        "the delivery status and will keep you updated.",
            "General Query": "Thank you for reaching out. We've received your message and "
                              "our team will get back to you with the details you need.",
        }
        body_text = templates.get(category, templates["General Query"])
        return (
            f"{opening}\n\nThank you for contacting us regarding \"{subject}\". "
            f"{body_text}\n\nIf you have any further questions, feel free to reply to "
            f"this email.\n\nBest regards,\nSupport Team"
        )

    # ------------------------------------------------------------------
    # 2. Summarization
    # ------------------------------------------------------------------
    def summarize_email(self, body: str) -> str:
        system_prompt = "Summarize the following customer email in one or two short sentences."
        summary = self._chat(system_prompt, body, max_tokens=80)
        if summary:
            return summary
        return self._mock_summary(body)

    @staticmethod
    def _mock_summary(body: str) -> str:
        clean = re.sub(r"\s+", " ", body).strip()
        if len(clean) <= 140:
            return clean
        return clean[:140].rsplit(" ", 1)[0] + "..."

    # ------------------------------------------------------------------
    # 3. Sentiment analysis
    # ------------------------------------------------------------------
    NEGATIVE_WORDS = {
        "angry", "bad", "worst", "terrible", "awful", "disappointed", "refund",
        "broken", "issue", "problem", "complaint", "delay", "delayed", "not working",
        "frustrated", "unhappy", "poor", "horrible", "cancel", "scam", "waste",
    }
    POSITIVE_WORDS = {
        "thank", "thanks", "great", "good", "love", "excellent", "awesome",
        "happy", "appreciate", "wonderful", "amazing", "pleased", "fantastic",
    }

    def analyze_sentiment(self, body: str) -> str:
        system_prompt = (
            "Classify the sentiment of this customer email as exactly one word: "
            "Positive, Negative, or Neutral."
        )
        result = self._chat(system_prompt, body, max_tokens=5)
        if result:
            for label in ("Positive", "Negative", "Neutral"):
                if label.lower() in result.lower():
                    return label
        return self._mock_sentiment(body)

    def _mock_sentiment(self, body: str) -> str:
        text = body.lower()
        neg_hits = sum(1 for w in self.NEGATIVE_WORDS if w in text)
        pos_hits = sum(1 for w in self.POSITIVE_WORDS if w in text)
        if neg_hits > pos_hits:
            return "Negative"
        if pos_hits > neg_hits:
            return "Positive"
        return "Neutral"

    # ------------------------------------------------------------------
    # 4. Classification
    # ------------------------------------------------------------------
    CATEGORY_KEYWORDS = {
        "Refund": ["refund", "money back", "reimburse"],
        "Complaint": ["complaint", "unhappy", "disappointed", "worst", "terrible"],
        "Technical Issue": ["error", "bug", "not working", "crash", "issue", "broken", "login"],
        "Payment": ["payment", "charged", "invoice", "billing", "card declined"],
        "Shipping": ["shipping", "delivery", "package", "tracking", "shipment", "courier"],
    }

    def classify_email(self, subject: str, body: str) -> str:
        system_prompt = (
            "Classify this customer email into exactly one category: "
            "Complaint, Refund, Technical Issue, Payment, Shipping, or General Query. "
            "Reply with only the category name."
        )
        result = self._chat(system_prompt, f"{subject}\n{body}", max_tokens=8)
        if result:
            for label in self.CATEGORY_KEYWORDS:
                if label.lower() in result.lower():
                    return label
            if "general" in result.lower():
                return "General Query"
        return self._mock_classify(subject, body)

    def _mock_classify(self, subject: str, body: str) -> str:
        text = f"{subject} {body}".lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(k in text for k in keywords):
                return category
        return "General Query"

    # ------------------------------------------------------------------
    # 5. Spam detection
    # ------------------------------------------------------------------
    SPAM_KEYWORDS = [
        "lottery", "winner", "click here", "free money", "viagra", "crypto giveaway",
        "act now", "congratulations you", "wire transfer", "casino", "bitcoin investment",
    ]

    def detect_spam(self, subject: str, body: str) -> bool:
        system_prompt = "Is this email spam? Reply with only 'Yes' or 'No'."
        result = self._chat(system_prompt, f"{subject}\n{body}", max_tokens=3)
        if result:
            return result.strip().lower().startswith("y")
        return self._mock_spam(subject, body)

    def _mock_spam(self, subject: str, body: str) -> bool:
        text = f"{subject} {body}".lower()
        return any(k in text for k in self.SPAM_KEYWORDS)

    # ------------------------------------------------------------------
    # 6. Priority prediction
    # ------------------------------------------------------------------
    HIGH_PRIORITY_WORDS = {
        "urgent", "immediately", "asap", "emergency", "critical", "not working",
        "down", "angry", "legal", "lawsuit", "cancel my account",
    }
    LOW_PRIORITY_WORDS = {"just wondering", "no rush", "whenever", "curious"}

    def predict_priority(self, subject: str, body: str, sentiment: str = None) -> str:
        system_prompt = (
            "Rate the priority of this customer email as exactly one word: "
            "High, Medium, or Low."
        )
        result = self._chat(system_prompt, f"{subject}\n{body}", max_tokens=5)
        if result:
            for label in ("High", "Medium", "Low"):
                if label.lower() in result.lower():
                    return label
        return self._mock_priority(subject, body, sentiment)

    def _mock_priority(self, subject: str, body: str, sentiment: str = None) -> str:
        text = f"{subject} {body}".lower()
        if any(w in text for w in self.HIGH_PRIORITY_WORDS) or sentiment == "Negative":
            return "High"
        if any(w in text for w in self.LOW_PRIORITY_WORDS):
            return "Low"
        return "Medium"

    # ------------------------------------------------------------------
    # Convenience: run every AI feature in one shot (used when a new
    # inbound email is received/composed)
    # ------------------------------------------------------------------
    def analyze_email(self, subject: str, body: str) -> dict:
        sentiment = self.analyze_sentiment(body)
        category = self.classify_email(subject, body)
        is_spam = self.detect_spam(subject, body)
        priority = self.predict_priority(subject, body, sentiment)
        summary = self.summarize_email(body)
        return {
            "sentiment": sentiment,
            "category": category,
            "is_spam": is_spam,
            "priority": priority,
            "summary": summary,
        }
