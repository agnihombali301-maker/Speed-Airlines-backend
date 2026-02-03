from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173'], supports_credentials=True)
    db.init_app(app)

    from app.routes import auth_bp, flights_bp, bookings_bp, admin_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(flights_bp, url_prefix='/api/flights')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    with app.app_context():
        db.create_all()
        from app.seed import seed_database
        seed_database()

    return app
