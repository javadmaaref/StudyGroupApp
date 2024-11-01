# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.routes import auth_bp, groups_bp, sessions_bp  # Remove main_bp from here
    app.register_blueprint(auth_bp)  # The root route '/' is now in auth_bp
    app.register_blueprint(groups_bp)
    app.register_blueprint(sessions_bp)

    return app