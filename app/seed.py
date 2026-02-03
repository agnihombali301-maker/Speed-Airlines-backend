from datetime import datetime, timedelta
from app import db
from app.models import User, Flight

def seed_database():
    if User.query.filter_by(username='admin').first():
        return
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    
    bases = [
        ('Mumbai', 'Delhi', 4500, 12000),
        ('Delhi', 'Bangalore', 5500, 14000),
        ('Mumbai', 'London', 45000, 95000),
        ('Delhi', 'Dubai', 22000, 55000),
        ('Bangalore', 'Singapore', 18000, 42000),
        ('Chennai', 'Mumbai', 4000, 11000),
        ('Kolkata', 'Delhi', 5000, 13000),
        ('Hyderabad', 'Dubai', 20000, 48000),
        ('Mumbai', 'New York', 65000, 135000),
        ('Delhi', 'London', 42000, 90000),
    ]
    t = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    flight_num = 1
    # For each route, create a flight for each of the next 30 days so search always finds results
    for route_idx, (src, dest, ep, bp) in enumerate(bases):
        for day_offset in range(30):
            dep = t + timedelta(days=day_offset, hours=6 + (route_idx % 12), minutes=0)
            arr = dep + timedelta(hours=2 + (route_idx % 5))
            f = Flight(
                flight_number=f'SA{flight_num:03d}',
                source=src, destination=dest,
                departure_time=dep, arrival_time=arr,
                economy_price=ep, business_price=bp,
                economy_seats=60, business_seats=20
            )
            db.session.add(f)
            flight_num += 1
    db.session.commit()
