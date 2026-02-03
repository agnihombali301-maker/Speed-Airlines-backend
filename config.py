import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'speed-airlines-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///speed_airlines.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'speed-airlines-jwt-secret-key-2026-at-least-32-bytes-long'
    DEFAULT_CUSTOMER_BALANCE = 10000000  # INR
