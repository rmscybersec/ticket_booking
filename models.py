# Import de l'extension SQLAlchemy pour gérer la base de données
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialisation de l'objet db (sera utilisé pour créer les tables)
db = SQLAlchemy()

#Table User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default='user')

#Table Event
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))

#Table Booking
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)

#Relation vers l'utilisateur
    user = db.relationship('User', backref='bookings', lazy=True)

#Relation vers l'évènement
    event = db.relationship('Event', backref='bookings', lazy=True)

#Statut de la réservation : confirmé, annulé, payé
    status = db.Column(db.String(20), default="confirmé")

