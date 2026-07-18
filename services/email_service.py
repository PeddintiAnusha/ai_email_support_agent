"""
Email Service
=============
Business-logic layer that sits between routes and models for everything
related to Email / AIReply records. Keeping this logic out of routes/email.py
makes the route handlers thin and testable.
"""

from models import db
from models.email import AIReply, Email


class EmailService:

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    @staticmethod
    def create_email(user_id, sender, receiver, subject, body, direction="inbound",
                      category="General Query", priority="Medium", sentiment="Neutral",
                      is_spam=False):
        email = Email(
            user_id=user_id,
            sender=sender,
            receiver=receiver,
            subject=subject,
            body=body,
            direction=direction,
            category=category,
            priority=priority,
            sentiment=sentiment,
            is_spam=is_spam,
            status="pending" if direction == "inbound" else "replied",
        )
        db.session.add(email)
        db.session.commit()
        return email

    # ------------------------------------------------------------------
    # Read / query
    # ------------------------------------------------------------------
    @staticmethod
    def get_email(email_id, user_id=None):
        query = Email.query.filter_by(id=email_id)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.first()

    @staticmethod
    def list_emails(user_id, search=None, status=None, category=None,
                     priority=None, page=1, per_page=10):
        query = Email.query.filter_by(user_id=user_id, direction="inbound")

        if search:
            like = f"%{search}%"
            query = query.filter(
                db.or_(
                    Email.subject.ilike(like),
                    Email.body.ilike(like),
                    Email.sender.ilike(like),
                )
            )
        if status:
            query = query.filter_by(status=status)
        if category:
            query = query.filter_by(category=category)
        if priority:
            query = query.filter_by(priority=priority)

        query = query.order_by(Email.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def dashboard_stats(user_id):
        inbound = Email.query.filter_by(user_id=user_id, direction="inbound")
        return {
            "inbox_count": inbound.count(),
            "sent_count": Email.query.filter_by(user_id=user_id, direction="outbound").count(),
            "pending_count": inbound.filter_by(status="pending").count(),
            "urgent_count": inbound.filter_by(priority="High").count(),
            "recent_emails": inbound.order_by(Email.created_at.desc()).limit(5).all(),
        }

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    @staticmethod
    def mark_important(email, flag: bool = True):
        email.is_important = flag
        db.session.commit()
        return email

    @staticmethod
    def mark_status(email, status: str):
        email.status = status
        db.session.commit()
        return email

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    @staticmethod
    def delete_email(email):
        db.session.delete(email)
        db.session.commit()

    # ------------------------------------------------------------------
    # AI reply persistence
    # ------------------------------------------------------------------
    @staticmethod
    def save_ai_reply(email_id, generated_reply, summary=None):
        ai_reply = AIReply(email_id=email_id, generated_reply=generated_reply, summary=summary)
        db.session.add(ai_reply)
        db.session.commit()
        return ai_reply

    @staticmethod
    def update_ai_reply(ai_reply, edited_reply):
        ai_reply.edited_reply = edited_reply
        db.session.commit()
        return ai_reply

    @staticmethod
    def send_reply(email, ai_reply, user_id):
        """Marks the original email as replied and logs the outbound reply."""
        email.status = "replied"
        outbound = Email(
            user_id=user_id,
            sender=email.receiver,
            receiver=email.sender,
            subject=f"Re: {email.subject}",
            body=ai_reply.final_text(),
            direction="outbound",
            status="replied",
            category=email.category,
            priority=email.priority,
        )
        db.session.add(outbound)
        db.session.commit()
        return outbound
