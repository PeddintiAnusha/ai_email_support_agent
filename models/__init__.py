from flask_sqlalchemy import SQLAlchemy

# Single shared SQLAlchemy instance used across the whole app.
# Imported by app.py (for init_app) and by models/routes/services (for queries).
db = SQLAlchemy()
