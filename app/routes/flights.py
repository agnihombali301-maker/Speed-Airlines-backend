from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, date, timedelta
from app import db
from app.models import Flight, User

flights_bp = Blueprint('flights', __name__)

@flights_bp.route('/', methods=['GET'])
def list_flights():
    source = request.args.get('source', '').strip()
    destination = request.args.get('destination', '').strip()
    date_str = request.args.get('date')
    q = Flight.query
    if source:
        q = q.filter(Flight.source.ilike(f'%{source}%'))
    if destination:
        q = q.filter(Flight.destination.ilike(f'%{destination}%'))
    if date_str:
        try:
            d = datetime.strptime(date_str, '%Y-%m-%d').date()
            q = q.filter(db.func.date(Flight.departure_time) == d)
        except ValueError:
            pass
    flights = q.order_by(Flight.departure_time).all()
    return jsonify([f.to_dict() for f in flights])

@flights_bp.route('/<int:flight_id>', methods=['GET'])
def get_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    return jsonify(flight.to_dict())

@flights_bp.route('/destinations', methods=['GET'])
def destinations():
    sources = db.session.query(Flight.source).distinct().all()
    dests = db.session.query(Flight.destination).distinct().all()
    return jsonify({
        'sources': [s[0] for s in sources],
        'destinations': [d[0] for d in dests]
    })
