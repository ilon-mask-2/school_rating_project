import hashlib
import sqlite3
from flask import g
from server.config import DATABASE
import re

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# server/db/utils.py
import jwt
import datetime
from functools import wraps
from flask import request

SECRET_KEY = 'your_super_secret_key'  # Надёжно храни! Не показывай никому


def get_db():
    """Получить соединение с базой данных, сохранить в g."""
    if '_database' not in g:
        g._database = sqlite3.connect(DATABASE)
        g._database.row_factory = sqlite3.Row
    return g._database

def close_connection(exception=None):
    """Закрыть соединение при завершении запроса."""
    db = g.pop('_database', None)
    if db is not None:
        db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()



def is_safe_input(text, allow_spaces=True):
    """
    Проверка: безопасен ли текст. Разрешены только буквы, цифры и стандартные символы.
    """
    allowed_chars = r"^[a-zA-Z0-9@._-]+$" if not allow_spaces else r"^[a-zA-Z0-9 @._-]+$"
    return re.match(allowed_chars, text) is not None


# === Генерация токена ===
def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# === Проверка токена ===
def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# === Защита маршрутов ===
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({'error': 'Недействительный формат токена'}), 403
        print("🔐 HEADER:", auth_header)
        token = auth_header.split(" ")[1]  # ⬅ достаём сам JWT без "Bearer"
        data = verify_token(token)
        if not data:
            return jsonify({'error': 'Недействительный или истёкший токен'}), 403

        request.user = data  # можно использовать: request.user["user_id"], request.user["role"]
        return f(*args, **kwargs)
    return decorated


app = Flask(__name__)

# Инициализация лимитера (по IP)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])