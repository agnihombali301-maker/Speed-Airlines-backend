from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import User, Flight, Booking
from app.utils import require_user

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
def list_users():
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    if payload.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@admin_bp.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def user_ops(user_id):
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    if payload.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    target = User.query.get_or_404(user_id)
    if request.method == 'GET':
        return jsonify(target.to_dict())
    if request.method == 'DELETE':
        if target.role == 'admin':
            return jsonify({'error': 'Cannot delete admin'}), 400
        db.session.delete(target)
        db.session.commit()
        return jsonify({'message': 'User deleted'})
    data = request.get_json() or {}
    if 'balance' in data and target.role == 'customer':
        target.balance = float(data['balance'])
    if 'username' in data:
        target.username = str(data['username']).strip()
    db.session.commit()
    return jsonify(target.to_dict())

@admin_bp.route('/flights', methods=['POST'])
def create_flight():
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    if payload.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json()
    flight_number = (data.get('flight_number') or '').strip()
    source = (data.get('source') or '').strip()
    destination = (data.get('destination') or '').strip()
    dep = data.get('departure_time')
    arr = data.get('arrival_time')
    economy_price = float(data.get('economy_price', 0))
    business_price = float(data.get('business_price', 0))
    economy_seats = int(data.get('economy_seats', 60))
    business_seats = int(data.get('business_seats', 20))
    if not all([flight_number, source, destination, dep, arr]):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        dep_dt = datetime.fromisoformat(dep.replace('Z', '+00:00'))
        arr_dt = datetime.fromisoformat(arr.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid datetime format'}), 400
    if Flight.query.filter_by(flight_number=flight_number).first():
        return jsonify({'error': 'Flight number already exists'}), 409
    f = Flight(flight_number=flight_number, source=source, destination=destination,
               departure_time=dep_dt, arrival_time=arr_dt, economy_price=economy_price,
               business_price=business_price, economy_seats=economy_seats, business_seats=business_seats)
    db.session.add(f)
    db.session.commit()
    return jsonify(f.to_dict()), 201

@admin_bp.route('/flights/<int:flight_id>', methods=['PUT', 'DELETE'])
def flight_ops(flight_id):
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    if payload.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    flight = Flight.query.get_or_404(flight_id)
    if request.method == 'DELETE':
        db.session.delete(flight)
        db.session.commit()
        return jsonify({'message': 'Flight deleted'})
    data = request.get_json() or {}
    for key in ['source', 'destination', 'economy_price', 'business_price', 'economy_seats', 'business_seats']:
        if key in data:
            setattr(flight, key, data[key])
    if 'departure_time' in data:
        flight.departure_time = datetime.fromisoformat(data['departure_time'].replace('Z', '+00:00'))
    if 'arrival_time' in data:
        flight.arrival_time = datetime.fromisoformat(data['arrival_time'].replace('Z', '+00:00'))
    db.session.commit()
    return jsonify(flight.to_dict())

@admin_bp.route('/bookings/<int:booking_id>', methods=['PUT', 'DELETE'])
def booking_ops(booking_id):
    user, payload, err = require_user()
    if err:
        return err[0], err[1]
    if payload.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    b = Booking.query.get_or_404(booking_id)
    if request.method == 'DELETE':
        u = User.query.get(b.user_id)
        if u:
            u.balance += b.total_amount
        fl = Flight.query.get(b.flight_id)
        if fl:
            if b.travel_class == 'economy':
                fl.economy_seats += b.num_passengers
            else:
                fl.business_seats += b.num_passengers
        db.session.delete(b)
        db.session.commit()
        return jsonify({'message': 'Booking cancelled'})
    data = request.get_json() or {}
    if 'status' in data:
        b.status = data['status']
    db.session.commit()
    return jsonify(b.to_dict())
