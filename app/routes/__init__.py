from app.routes.auth import auth_bp
from app.routes.flights import flights_bp
from app.routes.bookings import bookings_bp
from app.routes.admin import admin_bp

__all__ = ['auth_bp', 'flights_bp', 'bookings_bp', 'admin_bp']
