import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# สร้าง instance ของ SQLAlchemy และ Migrate
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name=None):
    """
    Application Factory Function
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    from app.config import config
    app.config.from_object(config[config_name])

    # Ensure DATABASE_URL is set in production
    if config_name == 'production' and not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise AssertionError('DATABASE_URL must be set for the production environment.')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Register error handlers
    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """Register error handlers for the app."""

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "success": False,
            "error": "Resource not found",
            "message": "The requested URL was not found on the server."
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Rollback the session in case of a database error
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error has occurred. Please try again later."
        }), 500
