from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()

# Configuración de la base de datos
def init_db(app):
    # Render da un DATABASE_URL tipo "postgres://..."
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///connectivity_monitor.db")

    # Fix: SQLAlchemy requiere "postgresql://"
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()


# ---------- MODELOS ----------

class Site(db.Model):
    __tablename__ = "sites"
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), unique=True, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_checked = db.Column(db.DateTime)
    last_status = db.Column(db.String(50))
    response_time = db.Column(db.Float)
    last_error = db.Column(db.Text)

    history = db.relationship("CheckHistory", backref="site", lazy=True)


class CheckHistory(db.Model):
    __tablename__ = "check_history"
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("sites.id"), nullable=False)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)
    response_time = db.Column(db.Float)
    error_message = db.Column(db.Text)
