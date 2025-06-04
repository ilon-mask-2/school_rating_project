# server/routes/teacher_routes.py

from flask import Blueprint, request, jsonify
import sqlite3
from server.config import DATABASE
from datetime import date, timedelta
import base64
from server.db.utils import get_db, limiter, token_required

teacher_bp = Blueprint("teacher", __name__)

@teacher_bp.route("/<int:teacher_id>/grade-options", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_teacher_grade_options(teacher_id):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Проверка существования преподавателя
        cursor.execute("SELECT name FROM teachers WHERE id = ?", (teacher_id,))
        teacher = cursor.fetchone()
        if not teacher:
            return jsonify({"error": "Teacher not found"}), 404

        # Получение всех уникальных дат, когда ему ставили оценки
        cursor.execute("""
            SELECT DISTINCT date
            FROM grade_from_student_to_teacher
            WHERE teacher_id = ?
            ORDER BY date DESC
        """, (teacher_id,))
        dates = [row["date"] for row in cursor.fetchall() if row["date"]]

    return jsonify({
        "teacher_name": teacher["name"],
        "dates": dates
    })

@teacher_bp.route("/<int:teacher_id>/average-ratings", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_teacher_average_ratings(teacher_id):
    date_from = request.args.get("from", "0000-00-00")
    date_to = request.args.get("to", "9999-12-31")

    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("SELECT id FROM teachers WHERE id = ?", (teacher_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Teacher not found"}), 404

        query = """
            SELECT AVG(interest) as interest,
                   AVG(teaching) as teaching,
                   AVG(comfort) as comfort,
                   AVG(respect) as respect
            FROM grade_from_student_to_teacher
            WHERE teacher_id = ?
              AND date BETWEEN ? AND ?
        """
        params = [teacher_id, date_from, date_to]

        cursor.execute(query, params)
        row = cursor.fetchone()

    if not row or all(row[key] is None for key in row.keys()):
        return jsonify({})  # Нет оценок

    # Считаем оценки и итог
    ratings = {k: round(row[k], 2) if row[k] is not None else 0 for k in ["interest", "teaching", "comfort", "respect"]}
    ratings["overall"] = round(sum(ratings.values()) / 4, 2)

    return jsonify(ratings)

@teacher_bp.route("/<int:teacher_id>/groups", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_teacher_groups(teacher_id):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("SELECT * FROM study_groups WHERE teacher_id = ?", (teacher_id,))
        groups = [dict(row) for row in cursor.fetchall()]

    return jsonify(groups)

@teacher_bp.route("/<int:teacher_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_teacher_account(teacher_id):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, name, login, phone, email, photo
            FROM teachers
            WHERE id = ?
        """, (teacher_id,))
        row = cursor.fetchone()

    if not row:
        return jsonify({"error": "Teacher not found"}), 404

    # Преобразуем фото в base64, если оно есть
    photo_base64 = base64.b64encode(row["photo"]).decode('utf-8') if row["photo"] else None

    return jsonify({
        "id": row["id"],
        "name": row["name"],
        "login": row["login"],
        "phone": row["phone"],
        "email": row["email"],
        "photo": photo_base64
    })

@teacher_bp.route('/rate-student', methods=['POST'])
@token_required
@limiter.limit("20 per minute")
def rate_student():
    data = request.get_json()

    required = ["teacher_id", "student_id", "attendance", "participation", "effort", "respect"]
    if not all(data.get(k) is not None for k in required):
        return jsonify({"error": "Не все поля заполнены"}), 400

    # Определяем начало текущей недели (понедельник)
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    week_date = start_of_week.strftime("%Y-%m-%d")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO grade_from_teacher_to_student
        (teacher_id, student_id, date, attendance, participation, effort, respect)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["teacher_id"],
        data["student_id"],
        week_date,
        data["attendance"],
        data["participation"],
        data["effort"],
        data["respect"]
    ))

    conn.commit()

    return jsonify({
        "status": "success",
        "stored_week_date": week_date
    })
