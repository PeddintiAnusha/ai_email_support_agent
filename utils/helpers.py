"""Small shared helper functions used across routes/services."""

import re
from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(address: str) -> bool:
    return bool(address) and bool(EMAIL_REGEX.match(address.strip()))


def is_strong_password(password: str) -> bool:
    """Minimum: 6+ chars. Kept simple for a student/demo project."""
    return bool(password) and len(password) >= 6


def priority_badge_class(priority: str) -> str:
    return {
        "High": "badge-danger",
        "Medium": "badge-warning",
        "Low": "badge-success",
    }.get(priority, "badge-secondary")


def sentiment_badge_class(sentiment: str) -> str:
    return {
        "Positive": "badge-success",
        "Negative": "badge-danger",
        "Neutral": "badge-secondary",
    }.get(sentiment, "badge-secondary")


def admin_required(view_func):
    """Route decorator restricting access to admin-role users."""

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("email.dashboard"))
        return view_func(*args, **kwargs)

    return wrapped


def truncate(text: str, length: int = 80) -> str:
    text = text or ""
    return text if len(text) <= length else text[:length].rsplit(" ", 1)[0] + "..."
