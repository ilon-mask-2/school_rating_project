from flask import Blueprint, request, jsonify
import sqlite3
from server.config import DATABASE
from server.db.utils import hash_password  # предполагается, что ты вынес хеш-функцию сюда
from server.db.utils import is_safe_input, limiter, generate_token
auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("20 per minute")
def login():
    try:
        data = request.get_json()
        print("🔐 Пришел login-запрос:", data)

        login = data.get('login')
        password = data.get('password')
        role = data.get('role')

        print(f"▶️ login={login}, role={role}")
        
        db = get_db()  # ← Здесь чаще всего и падает!
        print("✅ Соединение с БД установлено")

    if not is_safe_input(login, allow_spaces=False) or not is_safe_input(password, allow_spaces=False):
        return jsonify({"error": "Недопустимые символы"}), 400

    if role not in ('student', 'teacher', 'admin'):
        return jsonify({'status': 'error', 'message': 'Invalid role'}), 400

    table_map = {
        'student': 'students',
        'teacher': 'teachers',
        'admin': 'admins'
    }
    table = table_map[role]
    name_field = 'name' if role != 'admin' else None

    query = f"SELECT * FROM {table} WHERE login = ? AND password = ?"
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        result = db.execute(query, (login, password)).fetchone()

    print("=== 📡 LOGIN REQUEST RECEIVED ===")
    print("Login:", login)
    print("Password:", password)
    print("Role:", role)
    print("Query used:", query)
    print("Result:", result)

    if result:
        token = generate_token(result['id'], role)
        response = {
            'status': 'success',
            'id': result['id'],
            'token': token
        }
        if name_field:
            response['name'] = result[name_field]
        return jsonify(response)
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    except Exception as e:
        print("❌ Ошибка авторизации:", str(e))
        return jsonify({"error": "internal error", "details": str(e)}), 500

@auth_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Слишком много попыток. Подождите немного и попробуйте снова."), 429

@auth_bp.route("/teachers", methods=["GET"])
def get_all_teachers_simple():
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        cursor.execute("SELECT id, name FROM teachers ORDER BY name")
        teachers = [dict(row) for row in cursor.fetchall()]
    return jsonify(teachers)
