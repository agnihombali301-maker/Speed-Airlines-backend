from flask import Blueprint, request, jsonify
from datetime import datetime, date
import json
from app import db
from app.models import Booking, Flight, User
from app.utils import require_user

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/', methods=['GET'])
def list_bookings():
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    if payload.get('role') == 'admin':
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    else:
        bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
    return jsonify([b.to_dict() for b in bookings])

@bookings_bp.route('/', methods=['POST'])
def create_booking():
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    if payload.get('role') != 'customer':
        return jsonify({'error': 'Only customers can book flights'}), 403
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid request body'}), 400
    flight_id = data.get('flight_id')
    trip_type = data.get('trip_type', 'one_way') or 'one_way'
    travel_class = data.get('travel_class', 'economy') or 'economy'
    try:
        num_passengers = int(data.get('num_passengers', 1))
        num_passengers = max(1, min(9, num_passengers))
    except (TypeError, ValueError):
        num_passengers = 1
    date_depart = data.get('date_depart')
    date_return = data.get('date_return') if trip_type == 'return' else None
    seats = data.get('seats', [])
    if not isinstance(seats, list):
        seats = []
    meal_preference = data.get('meal_preference', 'veg') or 'veg'
    try:
        extra_baggage_kg = int(data.get('extra_baggage_kg', 0))
        extra_baggage_kg = max(0, min(50, extra_baggage_kg))
    except (TypeError, ValueError):
        extra_baggage_kg = 0

    if not flight_id or not date_depart:
        return jsonify({'error': 'flight_id and date_depart required'}), 400
    flight = Flight.query.get(flight_id)
    if not flight:
        return jsonify({'error': 'Flight not found'}), 404
    try:
        d_depart = datetime.strptime(date_depart, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date_depart'}), 400
    d_return = None
    if date_return:
        try:
            d_return = datetime.strptime(date_return, '%Y-%m-%d').date()
        except ValueError:
            pass

    price_per = flight.economy_price if travel_class == 'economy' else flight.business_price
    base = price_per * num_passengers
    meal_charge = 500 * num_passengers if meal_preference else 0
    baggage_charge = 300 * extra_baggage_kg
    total_amount = base + meal_charge + baggage_charge
    if trip_type == 'return':
        total_amount *= 2

    if user.balance < total_amount:
        return jsonify({'error': 'Insufficient balance', 'required': total_amount, 'balance': user.balance}), 400
    avail = flight.economy_seats if travel_class == 'economy' else flight.business_seats
    if avail < num_passengers:
        return jsonify({'error': f'Not enough seats. Only {avail} available.'}), 400

    seats_str = json.dumps(seats) if isinstance(seats, list) else json.dumps([])
    booking = Booking(
        user_id=user.id, flight_id=flight.id, trip_type=trip_type, travel_class=travel_class,
        num_passengers=num_passengers, date_depart=d_depart, date_return=d_return,
        seats=seats_str, meal_preference=meal_preference, extra_baggage_kg=extra_baggage_kg,
        total_amount=total_amount, status='confirmed'
    )
    user.balance -= total_amount
    db.session.add(booking)
    if travel_class == 'economy':
        flight.economy_seats -= num_passengers
    else:
        flight.business_seats -= num_passengers
    db.session.commit()
    return jsonify({'message': 'Booking confirmed', 'booking': booking.to_dict(), 'new_balance': user.balance}), 201

@bookings_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    b = Booking.query.get_or_404(booking_id)
    if payload.get('role') != 'admin' and b.user_id != user.id:
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify(b.to_dict())
