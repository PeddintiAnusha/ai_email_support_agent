from datetime import datetime

from models import db


class Email(db.Model):
    __tablename__ = "emails"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    sender = db.Column(db.String(150), nullable=False)      # customer email address
    receiver = db.Column(db.String(150), nullable=False)     # support inbox address
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default="pending")     # pending | replied | archived
    priority = db.Column(db.String(10), default="Medium")    # High | Medium | Low
    category = db.Column(db.String(50), default="General Query")
    sentiment = db.Column(db.String(20), default="Neutral")  # Positive | Negative | Neutral
    is_spam = db.Column(db.Boolean, default=False)
    is_important = db.Column(db.Boolean, default=False)
    direction = db.Column(db.String(10), default="inbound")  # inbound | outbound

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ai_replies = db.relationship(
        "AIReply", backref="email", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "priority": self.priority,
            "category": self.category,
            "sentiment": self.sentiment,
            "is_spam": self.is_spam,
            "is_important": self.is_important,
            "direction": self.direction,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Email {self.id} {self.subject!r}>"


class AIReply(db.Model):
    __tablename__ = "ai_replies"

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey("emails.id"), nullable=False)

    generated_reply = db.Column(db.Text, nullable=False)
    edited_reply = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def final_text(self):
        return self.edited_reply if self.edited_reply else self.generated_reply

    def to_dict(self):
        return {
            "id": self.id,
            "email_id": self.email_id,
            "generated_reply": self.generated_reply,
            "edited_reply": self.edited_reply,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
