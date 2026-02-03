from datetime import datetime
from app import db
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'customer'
    balance = db.Column(db.Float, default=0)  # INR for customers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Security questions (for customers)
    q1 = db.Column(db.String(200))
    q2 = db.Column(db.String(200))
    q3 = db.Column(db.String(200))
    a1_hash = db.Column(db.String(128))
    a2_hash = db.Column(db.String(128))
    a3_hash = db.Column(db.String(128))
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def set_answer(self, idx, answer):
        h = bcrypt.hashpw(answer.strip().lower().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if idx == 1: self.a1_hash = h
        elif idx == 2: self.a2_hash = h
        else: self.a3_hash = h
    
    def check_answer(self, idx, answer):
        h = getattr(self, f'a{idx}_hash')
        if not h: return False
        return bcrypt.checkpw(answer.strip().lower().encode('utf-8'), h.encode('utf-8'))
    
    def to_dict(self):
        d = {'id': self.id, 'username': self.username, 'role': self.role, 'created_at': self.created_at.isoformat() if self.created_at else None}
        if self.role == 'customer':
            d['balance'] = self.balance
            d['q1'] = self.q1
            d['q2'] = self.q2
            d['q3'] = self.q3
        return d


class Flight(db.Model):
    __tablename__ = 'flights'
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), unique=True, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    economy_price = db.Column(db.Float, nullable=False)  # INR per seat
    business_price = db.Column(db.Float, nullable=False)
    economy_seats = db.Column(db.Integer, default=60)
    business_seats = db.Column(db.Integer, default=20)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id, 'flight_number': self.flight_number,
            'source': self.source, 'destination': self.destination,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'economy_price': self.economy_price, 'business_price': self.business_price,
            'economy_seats': self.economy_seats, 'business_seats': self.business_seats
        }


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    trip_type = db.Column(db.String(20), nullable=False)  # 'one_way' or 'return'
    travel_class = db.Column(db.String(20), nullable=False)  # economy or business
    num_passengers = db.Column(db.Integer, nullable=False)
    date_depart = db.Column(db.Date, nullable=False)
    date_return = db.Column(db.Date, nullable=True)
    seats = db.Column(db.String(500), nullable=True)  # JSON e.g. ["12A","12B"]
    meal_preference = db.Column(db.String(20), nullable=True)  # veg / non_veg
    extra_baggage_kg = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='confirmed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    flight = db.relationship('Flight', backref=db.backref('bookings', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id, 'user_id': self.user_id, 'flight_id': self.flight_id,
            'trip_type': self.trip_type, 'travel_class': self.travel_class,
            'num_passengers': self.num_passengers,
            'date_depart': self.date_depart.isoformat() if self.date_depart else None,
            'date_return': self.date_return.isoformat() if self.date_return else None,
            'seats': self.seats, 'meal_preference': self.meal_preference,
            'extra_baggage_kg': self.extra_baggage_kg, 'total_amount': self.total_amount,
            'status': self.status, 'created_at': self.created_at.isoformat() if self.created_at else None,
            'flight': self.flight.to_dict() if self.flight else None
        }
