from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from models import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
#Vérifier que la personne est connectée
        verify_jwt_in_request()
#Récupère l'ID de l'utilisateur connecté
        user_id = get_jwt_identity()
#Va chercher l'utilisateur dans la BD
        user = User.query.get(user_id)

        if not user or user.role != "admin": # Vérifie le rôle
            return jsonify({"Erreur": "Accès réservé aux administrateurs"}), 403

# Si admin → on laisse passer
        return fn(*args, **kwargs)
    return wrapper
