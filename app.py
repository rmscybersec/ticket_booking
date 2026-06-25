from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from models import db, User, Event, Booking
from datetime import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from security import admin_required

#Création de l'application Flask
app = Flask(__name__)

#Configuration de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Configuration de la clé secrète
app.config['JWT_SECRET_KEY'] = 'A9f$3kL!92@xP0#qT7vB1zM8rW4sE6ZxYt9Qw2'
jwt = JWTManager(app)

#Initialisation
db.init_app(app)
bcrypt = Bcrypt(app)

#Route simple pour renvoyer à la page de connexion
@app.route('/')
def home():
    return render_template('login.html')

#ROUTE : Ajouter un utilisateur
@app.route('/add_user', methods=['POST'])
def add_user():
#Récupération des données envoyées en JSON
    data = request.get_json()

#Création d'un nouvel utilisateur
    new_user = User(
        name=data['name'],
        email=data['email'],
        password_hash=bcrypt.generate_password_hash(data['password']).decode('utf-8'),
        role=data.get('role', 'user')
    )

#Ajout à la base de données
    db.session.add(new_user)
    db.session.commit()

#Réponse envoyée au client
    return jsonify({"message": "Utilisateur créé avec succès"}), 201

#ROUTE : Ajouter un événement
@app.route('/add_event', methods=['POST'])
@jwt_required()
@admin_required
def add_event():
#Récupération des données envoyées en JSON
    data = request.get_json()

#Conversion de la date (string en datetime)
    event_date = datetime.strptime(data['date'], "%Y-%m-%d %H:%M:%S")

#Création d'un nouvel événement
    new_event = Event(
        title=data['title'],
        description=data['description'],
        date=event_date,  # format : "2025-06-01 19:00:00"
        capacity=data['capacity'],
        available_seats=data['capacity'],  #au début, toutes les places sont dispo
        price=data['price'],
        category=data.get('category', 'Autre')
    )

#Ajout à la base de données
    db.session.add(new_event)
    db.session.commit()

#Réponse envoyée au client
    return jsonify({"message": "Événement créé avec succès"}), 201

#ROUTE : Réserver un événement
@app.route('/book_event', methods=['POST'])
@jwt_required()
def book_event():
    data = request.get_json()

#Vérifier que event_id est présent
    if "event_id" not in data or not data["event_id"]:
        return jsonify({"Erreur": "event_id manquant dans la requête"}), 400

#Récupération de l'utilisateur connecté via le token
    user_id = get_jwt_identity()

#Récupération de l'ID de l'événement depuis le JSON
    event_id = int(data.get('event_id'))
    quantity = data.get('quantity', 1)

#Vérifier si l'utilisateur existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"Erreur": "Utilisateur introuvable"}), 404

#Vérifier si l'événement existe
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"Erreur": "Événement introuvable"}), 404

#Vérifier s'il reste des places
    if event.available_seats < quantity:
        return jsonify({"Erreur": "Pas assez de places disponibles"}), 400

#Vérifier que la quantité est valide
    if quantity <= 0:
        return jsonify({"Erreur": "La quantité doit être supérieure à 0"}), 400

#Créer la réservation
    new_booking = Booking(
        user_id=user_id,
        event_id=event_id,
        quantity=quantity,
        booking_date=datetime.now(),
        status="confirmé"
    )

#Mettre à jour les places restantes
    event.available_seats -= quantity

#Sauvegarder dans la base
    db.session.add(new_booking)
    db.session.commit()

    return jsonify({"message": "Réservation effectuée avec succès"}), 201

#ROUTE : Liste des utilisateurs
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    result = []

    for u in users:
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role
        })

    return jsonify(result), 200

#ROUTE : Obtenir un utilisateur par ID
@app.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
#Récupération de l'utilisateur connecté
    current_user_id = get_jwt_identity()

#Vérification si l'utilisateur existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"Erreur": "Utilisateur introuvable"}), 404

#Vérification que l'utilisateur connecté demande son propre profil
    if int(current_user_id) != user_id:
        return jsonify({"Erreur": "Accès refusé"}), 403

#Retourner les infos de l'utilisateur
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }), 200

#ROUTE : Mettre à jour un utilisateur
@app.route('/user/update/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
#Récupération de l'utilisateur connecté
    current_user_id = get_jwt_identity()

#Vérification que l'utilisateur met à jour son propre profil
    if int(current_user_id) != user_id:
        return jsonify({"Erreur": "Accès refusé"}), 403

#Récupération de l'utilisateur
    user = User.query.get(user_id)
    if not user:
        return jsonify({"Erreur": "Utilisateur introuvable"}), 404

    data = request.get_json()

#Mise à jour des champs
    if "name" in data:
        user.name = data["name"]

    if "email" in data:
        user.email = data["email"]

    if "password" in data:
        user.password = generate_password_hash(data["password"])

    db.session.commit()

    return jsonify({"message": "Utilisateur mis à jour avec succès"}), 200

#ROUTE : Suppression d'un utilisateur
@app.route('/user/delete/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
#Récupération de l'utilisateur connecté
    current_user_id = get_jwt_identity()

#Vérification que l'utilisateur supprime son propre compte
    if int(current_user_id) != user_id:
        return jsonify({"Erreur": "Accès refusé"}), 403

#Récupération de l'utilisateur
    user = User.query.get(user_id)
    if not user:
        return jsonify({"Erreur": "Utilisateur introuvable"}), 404

#Suppression d'abord de toutes les réservations de cet utilisateur
    bookings = Booking.query.filter_by(user_id=user_id).all()
    for booking in bookings:
        db.session.delete(booking)

#Suppression de l'utilisateur
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "Utilisateur et réservations associés supprimés avec succès"}), 200

#ROUTE : Liste des événements
@app.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    result = []

    for e in events:
        result.append({
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.date,
            "capacity": e.capacity,
            "available_seats": e.available_seats,
            "price": e.price,
            "category": e.category
        })

    return jsonify(result), 200

#ROUTE : Liste des réservations
@app.route('/bookings', methods=['GET'])
def get_bookings():
    bookings = Booking.query.all()
    result = []

    for b in bookings:
        result.append({
            "id": b.id,
            "user_id": b.user_id,
            "event_id": b.event_id
        })

    return jsonify(result), 200

#ROUTE : Voir les réservations de l'utilisateur connecté
@app.route('/my_bookings', methods=['GET'])
@jwt_required()
def my_bookings():
#Récupération de l'utilisateur connecté
    user_id = get_jwt_identity()

#Rechercher toutes ses réservations
    bookings = Booking.query.filter_by(user_id=user_id).all()

    result = []
    for b in bookings:
        event = Event.query.get(b.event_id)
        result.append({
            "booking_id": b.id,
            "event_title": event.title,
            "event_date": event.date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": b.status,
            "quantity": b.quantity
        })

    return jsonify(result), 200

#ROUTE : Obtenir une réservation par ID
@app.route('/booking/<int:booking_id>', methods=['GET'])
@jwt_required()
def get_booking(booking_id):
#Récupération de l'utilisateur connecté
    user_id = get_jwt_identity()

#Recherche de la réservation
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"Erreur": "Réservation introuvable"}), 404

#Vérification que l'utilisateur est propriétaire de la réservation
    if booking.user_id != int(user_id):
        return jsonify({"Erreur": "Accès refusé"}), 403

#Retour des infos de la réservation
    return jsonify({
        "booking_id": booking.id,
        "event_id": booking.event_id,
        "quantity": booking.quantity,
        "booking_date": booking.booking_date,
        "status": booking.status
    }), 200

#ROUTE : Supprimer une réservation
@app.route('/booking/delete/<int:booking_id>', methods=['DELETE'])
@jwt_required()
def delete_booking(booking_id):
#Récupération de l'utilisateur connecté
    user_id = get_jwt_identity()

#Rechercher la réservation
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"Erreur": "Réservation introuvable"}), 404

#Vérification que l'utilisateur est propriétaire de la réservation
    if booking.user_id != int(user_id):
        return jsonify({"Erreur": "Accès refusé"}), 403

#Récupération de l'événement associé pour remettre les places
    event = Event.query.get(booking.event_id)
    if event:
        event.available_seats += booking.quantity

#changement du statut de la réservation pour annulé
    booking.status = "annulé"

    db.session.commit()

    return jsonify({"message": "Réservation annulée avec succès"}), 200

#ROUTE : Enregistrement
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

#vérification si le courriel existe déjà
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"Erreur": "Courriel déjà utilisé"}), 400

#hashage du mot de passe
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

#création de l'utilisateur
    new_user = User(
        name=data['name'],
        email=data['email'],
        password_hash=hashed_password,
        role=data.get('role', 'user')
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Utilisateur créé avec succès"}), 201

#ROUTE : login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

#Vérification si l'utilisateur existe
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({"Erreur": "Utilisateur introuvable"}), 404

#Vérification du mot de passe
    if not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({"Erreur": "Mot de passe incorrect"}), 401

#Génération un token JWT
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Connexion réussie",
        "access_token": access_token,
        "user_id": user.id,
        "name": user.name,
        "role": user.role
    }), 200

#ROUTE : Obtenir un événement par ID
@app.route('/event/<int:event_id>', methods=['GET'])
def get_event(event_id):
#Recherche de l'événement dans la base
    event = Event.query.get(event_id)

#Si l'événement n'existe pas
    if not event:
        return jsonify({"Erreur": "Événement introuvable"}), 404

#Retourner les infos de l'événement
    return jsonify({
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "date": event.date,
        "capacity": event.capacity,
        "available_seats": event.available_seats,
        "price": event.price,
        "category": event.category
    }), 200

#ROUTE : Mettre à jour un événement
@app.route('/event/update/<int:event_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_event(event_id):
    data = request.get_json()

#Rechercher l'événement
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"Erreur": "Événement introuvable"}), 404

#Mise à jour des champs (seulement ceux fournis)
    if "title" in data:
        event.title = data["title"]

    if "description" in data:
        event.description = data["description"]

    if "date" in data:
        try:
            event.date = datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return jsonify({"Erreur": "Format de date invalide. Format attendu : YYYY-MM-DD HH:MM:SS"}), 400

    if "capacity" in data:
        # Ajuster les places disponibles si la capacité change
        difference = data["capacity"] - event.capacity
        event.capacity = data["capacity"]
        event.available_seats += difference
        if event.available_seats < 0:
            event.available_seats = 0

    if "price" in data:
        event.price = data["price"]

    if "category" in data:
        event.category = data["category"]

#Sauvegarde
    db.session.commit()

    return jsonify({"message": "Événement mis à jour avec succès"}), 200

#ROUTE : Supprimer un événement
@app.route('/event/delete/<int:event_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_event(event_id):
#Rechercher l'événement
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"Erreur": "Événement introuvable"}), 404

#Supprimer l'événement
    db.session.delete(event)
    db.session.commit()

    return jsonify({"message": "Événement supprimé avec succès"}), 200

#ROUTE ADMIN : Voir tous les utilisateurs
@app.route('/admin/users', methods=['GET'])
@jwt_required()      # L'admin doit être connecté
@admin_required      # Vérifie que le rôle = "admin"
def admin_get_users():
#Récupération de tous les utilisateurs dans la base
    users = User.query.all()

#Préparation d'une liste propre à retourner en JSON
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role
        })

#Retour de la liste complète
    return jsonify(result), 200

#ROUTE ADMIN : Voir tous les événements
@app.route('/admin/events', methods=['GET'])
@jwt_required()      # L'admin doit être connecté
@admin_required      # Vérifie que le rôle = "admin"
def admin_get_events():
#Récupération de tous les événements
    events = Event.query.all()

#Préparation de la réponse JSON
    result = []
    for e in events:
        result.append({
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.date,
            "capacity": e.capacity,
            "available_seats": e.available_seats,
            "price": e.price,
            "category": e.category
        })

#Retour de la liste complète
    return jsonify(result), 200

#ROUTE ADMIN : Voir toutes les réservations
@app.route('/admin/bookings', methods=['GET'])
@jwt_required()      # L'admin doit être connecté
@admin_required      # Vérifie que le rôle = "admin"
def admin_get_bookings():
#Récupération de toutes les réservations
    bookings = Booking.query.all()

#Préparation de la réponse JSON
    result = []
    for b in bookings:
        result.append({
            "id": b.id,
            "user_id": b.user_id,
            "event_id": b.event_id,
            "quantity": b.quantity,
            "booking_date": b.booking_date,
            "status": b.status
        })

#Retour de la liste complète
    return jsonify(result), 200

# Création des tables si elles n'existent pas encore
with app.app_context():
    db.create_all()

#ROUTE : Paiement pour une réservation
@app.route('/pay/<int:booking_id>', methods=['POST'])
@jwt_required()   #L'utilisateur doit être connecté
def pay_booking(booking_id):
#Récupération de l'utilisateur connecté
    user_id = get_jwt_identity()

#Récupération de la réservation
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"Erreur": "Réservation introuvable"}), 404

#Vérification que la réservation appartient à l'utilisateur
    if booking.user_id != int(user_id):
        return jsonify({"Erreur": "Accès refusé"}), 403

#Vérification si la réservation est déjà annulée
    if booking.status == "annulé":
        return jsonify({"Erreur": "Impossible de payer une réservation annulée"}), 400

#Vérification si la réservation est déjà payée
    if booking.status == "payé":
        return jsonify({"Erreur": "Cette réservation est déjà payée"}), 400

#Paiement : on change le statut
    booking.status = "payé"

#Sauvegarder dans la base
    db.session.commit()

    return jsonify({"message": "Paiement effectué avec succès"}), 200

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/events_page')
def events_page():
    return render_template('events.html')

@app.route('/my_bookings_page')
def my_bookings_page():
    return render_template('my_bookings.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

#Lancement de l'application en mode debug
if __name__ == '__main__':
    app.run(debug=True)