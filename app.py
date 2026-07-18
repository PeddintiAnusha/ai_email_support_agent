import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from config import config_map
from models import db
from models.user import User

load_dotenv()


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # Ensure the database/ and uploads/ folders exist
    os.makedirs(os.path.join(app.root_path, "database"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ---- extensions ----
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ---- blueprints ----
    from routes.auth import auth_bp
    from routes.email import email_bp
    from routes.ai import ai_bp

    app.register_blueprint(email_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ai_bp)

    # ---- template context ----
    from utils.helpers import priority_badge_class, sentiment_badge_class

    @app.context_processor
    def inject_helpers():
        return dict(
            priority_badge_class=priority_badge_class,
            sentiment_badge_class=sentiment_badge_class,
        )

    # ---- error handlers ----
    @app.errorhandler(404)
    def not_found(e):
        return "Page not found.", 404

    # ---- create tables on first run ----
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True), host="0.0.0.0", port=5000)
