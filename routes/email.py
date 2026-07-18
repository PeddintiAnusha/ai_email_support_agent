from flask import (Blueprint, current_app, flash, redirect, render_template,
                    request, url_for)
from flask_login import current_user, login_required

from models.email import AIReply
from services.ai_service import AIService
from services.email_service import EmailService
from utils.helpers import is_valid_email

email_bp = Blueprint("email", __name__)


def get_ai_service() -> AIService:
    return AIService(
        api_key=current_app.config.get("OPENAI_API_KEY", ""),
        model=current_app.config.get("OPENAI_MODEL", "gpt-4o-mini"),
    )


@email_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("email.dashboard"))
    return render_template("index.html")


@email_bp.route("/dashboard")
@login_required
def dashboard():
    stats = EmailService.dashboard_stats(current_user.id)
    return render_template("dashboard.html", stats=stats)


@email_bp.route("/inbox")
@login_required
def inbox():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip() or None
    status = request.args.get("status") or None
    category = request.args.get("category") or None
    priority = request.args.get("priority") or None

    pagination = EmailService.list_emails(
        current_user.id, search=search, status=status,
        category=category, priority=priority, page=page,
        per_page=current_app.config.get("EMAILS_PER_PAGE", 10),
    )
    return render_template(
        "inbox.html", pagination=pagination, emails=pagination.items,
        search=search or "", status=status, category=category, priority=priority,
    )


@email_bp.route("/compose", methods=["GET", "POST"])
@login_required
def compose():
    if request.method == "POST":
        receiver = request.form.get("receiver", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not is_valid_email(receiver):
            flash("Please enter a valid recipient email address.", "danger")
        elif not subject or not body:
            flash("Subject and message body are required.", "danger")
        else:
            EmailService.create_email(
                user_id=current_user.id,
                sender=current_user.email,
                receiver=receiver,
                subject=subject,
                body=body,
                direction="outbound",
            )
            flash("Email sent successfully.", "success")
            return redirect(url_for("email.inbox"))

    return render_template("compose.html")


@email_bp.route("/email/<int:email_id>")
@login_required
def view_email(email_id):
    email = EmailService.get_email(email_id, user_id=current_user.id)
    if not email:
        flash("Email not found.", "danger")
        return redirect(url_for("email.inbox"))

    latest_reply = (
        AIReply.query.filter_by(email_id=email.id).order_by(AIReply.created_at.desc()).first()
    )
    return render_template("email.html", email=email, latest_reply=latest_reply)


@email_bp.route("/email/<int:email_id>/delete", methods=["POST"])
@login_required
def delete_email(email_id):
    email = EmailService.get_email(email_id, user_id=current_user.id)
    if not email:
        flash("Email not found.", "danger")
    else:
        EmailService.delete_email(email)
        flash("Email deleted.", "info")
    return redirect(url_for("email.inbox"))


@email_bp.route("/email/<int:email_id>/important", methods=["POST"])
@login_required
def toggle_important(email_id):
    email = EmailService.get_email(email_id, user_id=current_user.id)
    if email:
        EmailService.mark_important(email, not email.is_important)
        flash("Email updated.", "success")
    return redirect(request.referrer or url_for("email.inbox"))


@email_bp.route("/history")
@login_required
def history():
    pagination = EmailService.list_emails(
        current_user.id, status="replied", page=request.args.get("page", 1, type=int),
        per_page=current_app.config.get("EMAILS_PER_PAGE", 10),
    )
    return render_template("inbox.html", pagination=pagination, emails=pagination.items,
                            search="", status="replied", category=None, priority=None,
                            history_view=True)


# ----------------------------------------------------------------------
# Demo helper: simulate an inbound customer email being received, running
# it through the AI classification pipeline automatically. Handy for
# testing the AI module without wiring up a real inbound mail server.
# ----------------------------------------------------------------------
@email_bp.route("/simulate-inbound", methods=["GET", "POST"])
@login_required
def simulate_inbound():
    if request.method == "POST":
        sender = request.form.get("sender", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not is_valid_email(sender) or not subject or not body:
            flash("Please fill in a valid sender email, subject, and body.", "danger")
            return redirect(url_for("email.simulate_inbound"))

        ai = get_ai_service()
        analysis = ai.analyze_email(subject, body)

        email = EmailService.create_email(
            user_id=current_user.id,
            sender=sender,
            receiver=current_user.email,
            subject=subject,
            body=body,
            direction="inbound",
            category=analysis["category"],
            priority=analysis["priority"],
            sentiment=analysis["sentiment"],
            is_spam=analysis["is_spam"],
        )
        flash("Simulated customer email received and analyzed by AI.", "success")
        return redirect(url_for("email.view_email", email_id=email.id))

    return render_template("compose.html", simulate=True)
