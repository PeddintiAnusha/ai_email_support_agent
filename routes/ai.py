from flask import (Blueprint, current_app, flash, jsonify, redirect,
                    render_template, request, url_for)
from flask_login import current_user, login_required

from models import db
from models.email import AIReply
from services.ai_service import AIService
from services.email_service import EmailService

ai_bp = Blueprint("ai", __name__)


def get_ai_service() -> AIService:
    return AIService(
        api_key=current_app.config.get("OPENAI_API_KEY", ""),
        model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
    )


@ai_bp.route("/email/<int:email_id>/ai-reply", methods=["GET"])
@login_required
def ai_reply_page(email_id):
    email = EmailService.get_email(email_id, user_id=current_user.id)
    if not email:
        flash("Email not found.", "danger")
        return redirect(url_for("email.inbox"))

    latest_reply = (
        AIReply.query.filter_by(email_id=email.id).order_by(AIReply.created_at.desc()).first()
    )
    return render_template("ai_reply.html", email=email, latest_reply=latest_reply)


@ai_bp.route("/api/generate_reply", methods=["POST"])
@login_required
def api_generate_reply():
    """POST { email_id } -> generates + stores a new AI reply draft."""
    data = request.get_json(silent=True) or request.form
    email_id = data.get("email_id")
    email = EmailService.get_email(email_id, user_id=current_user.id)
    if not email:
        return jsonify({"success": False, "error": "Email not found"}), 404

    ai = get_ai_service()
    customer_name = email.sender.split("@")[0].replace(".", " ").title()
    reply_text = ai.generate_reply(email.subject, email.body, customer_name)
    summary = ai.summarize_email(email.body)

    ai_reply = EmailService.save_ai_reply(email.id, reply_text, summary=summary)

    return jsonify({
        "success": True,
        "ai_reply_id": ai_reply.id,
        "generated_reply": ai_reply.generated_reply,
        "summary": ai_reply.summary,
    })


@ai_bp.route("/api/edit_reply", methods=["POST"])
@login_required
def api_edit_reply():
    """POST { ai_reply_id, edited_reply } -> saves the agent's edited text."""
    data = request.get_json(silent=True) or request.form
    ai_reply_id = data.get("ai_reply_id")
    edited_text = (data.get("edited_reply") or "").strip()

    ai_reply = AIReply.query.get(ai_reply_id)
    if not ai_reply or not edited_text:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    EmailService.update_ai_reply(ai_reply, edited_text)
    return jsonify({"success": True, "edited_reply": ai_reply.edited_reply})


@ai_bp.route("/api/send_reply", methods=["POST"])
@login_required
def api_send_reply():
    """POST { email_id, ai_reply_id } -> marks email replied, logs outbound msg."""
    data = request.get_json(silent=True) or request.form
    email_id = data.get("email_id")
    ai_reply_id = data.get("ai_reply_id")

    email = EmailService.get_email(email_id, user_id=current_user.id)
    ai_reply = AIReply.query.get(ai_reply_id)
    if not email or not ai_reply:
        return jsonify({"success": False, "error": "Invalid request"}), 404

    EmailService.send_reply(email, ai_reply, current_user.id)
    return jsonify({"success": True, "redirect": url_for("email.inbox")})


@ai_bp.route("/api/summary/<int:email_id>", methods=["GET"])
@login_required
def api_summary(email_id):
    email = EmailService.get_email(email_id, user_id=current_user.id)
    if not email:
        return jsonify({"success": False, "error": "Email not found"}), 404
    ai = get_ai_service()
    return jsonify({"success": True, "summary": ai.summarize_email(email.body)})


@ai_bp.route("/api/feedback", methods=["POST"])
@login_required
def api_feedback():
    from models.email import Feedback

    data = request.get_json(silent=True) or request.form
    rating = int(data.get("rating", 0))
    comments = data.get("comments", "")

    if not (1 <= rating <= 5):
        return jsonify({"success": False, "error": "Rating must be 1-5"}), 400

    fb = Feedback(user_id=current_user.id, rating=rating, comments=comments)
    db.session.add(fb)
    db.session.commit()
    return jsonify({"success": True})
