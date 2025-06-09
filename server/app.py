import os
print("📦 APP.PY ЗАПУСТИЛСЯ")
print("📁 Содержимое /app/server/db:", os.listdir("server/db") if os.path.exists("server/db") else "❌ нет папки")
print("📄 Есть ли database.db:", os.path.exists("server/db/database.db"))

import sys
import os
from flask import jsonify

# 🔧 Добавляем корень проекта в PYTHONPATH до всех других импортов!
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask
from server.db.utils import get_db, close_connection  # ← теперь сработает
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Указываем backend через конфигурацию (вместо storage=)
app.config["RATELIMIT_STORAGE_URL"] = "memory://"

limiter = Limiter(
    key_func=get_remote_address
)
limiter.init_app(app)

# 📌 Импорты blueprint'ов (ПОСЛЕ app = Flask)
from server.routes.auth_routes import auth_bp
from server.routes.student_routes import student_bp
from server.routes.teacher_routes import teacher_bp
from server.routes.admin_routes import admin_bp

# 📌 Регистрация blueprint'ов
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(student_bp, url_prefix="/student")
app.register_blueprint(teacher_bp, url_prefix="/teacher")
app.register_blueprint(admin_bp, url_prefix="/admin")

# 🧹 Закрытие соединения с БД
@app.teardown_appcontext
def shutdown_session(exception=None):
    close_connection(exception)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify(error="Размер запроса превышает допустимый лимит (5 МБ)."), 413

# 🚀 Запуск приложения
if __name__ == "__main__":
    app.run(debug=True)
