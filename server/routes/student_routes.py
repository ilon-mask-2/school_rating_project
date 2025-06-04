# server/routes/student_routes.py
from flask import Blueprint, request, jsonify
import sqlite3
from server.config import DATABASE
from datetime import date
import base64
from server.db.utils import limiter, token_required
student_bp = Blueprint("student", __name__)

# 🔹 Получить доступные фильтры (даты, учителя)
@student_bp.route("/<int:student_id>/grade-options", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_student_grade_options(student_id):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({"error": "Student not found"}), 404

        cursor.execute("""
            SELECT DISTINCT date
            FROM grade_from_teacher_to_student
            WHERE student_id = ?
            ORDER BY date DESC
        """, (student_id,))
        dates = [row["date"] for row in cursor.fetchall() if row["date"]]

        cursor.execute("""
            SELECT DISTINCT t.name
            FROM grade_from_teacher_to_student r
            JOIN teachers t ON r.teacher_id = t.id
            WHERE r.student_id = ?
            ORDER BY t.name
        """, (student_id,))
        teachers = [row["name"] for row in cursor.fetchall()]

    return jsonify({
        "student_name": student["name"],
        "dates": dates,
        "teachers": teachers
    })


# 🔹 Получить средние оценки ученика за период и/или по преподавателю
@student_bp.route("/<int:student_id>/average-ratings", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_student_average_ratings(student_id):
    date_from = request.args.get("from", "0000-00-00")
    date_to = request.args.get("to", "9999-12-31")
    teacher_name = request.args.get("teacher", "All")

    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("SELECT id FROM students WHERE id = ?", (student_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Student not found"}), 404

        query = """
            SELECT AVG(r.attendance) as attendance,
                   AVG(r.participation) as participation,
                   AVG(r.effort) as effort,
                   AVG(r.respect) as respect
            FROM grade_from_teacher_to_student r
            JOIN teachers t ON r.teacher_id = t.id
            WHERE r.student_id = ?
              AND r.date BETWEEN ? AND ?
        """
        params = [student_id, date_from, date_to]

        if teacher_name != "All":
            query += " AND t.name = ?"
            params.append(teacher_name)

        cursor.execute(query, params)
        row = cursor.fetchone()

    if not row or all(row[key] is None for key in row.keys()):
        return jsonify({})  # Нет оценок

    ratings = {k: round(row[k], 2) if row[k] is not None else 0 for k in ["attendance", "participation", "effort", "respect"]}
    ratings["overall"] = round(sum(ratings.values()) / 4, 2)

    return jsonify(ratings)


# 🔹 Получить детальные оценки ученика
@student_bp.route("/<int:student_id>/detailed-ratings", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_student_detailed_ratings(student_id):
    date_from = request.args.get("from", "0000-00-00")
    date_to = request.args.get("to", "9999-12-31")
    teacher_name = request.args.get("teacher", "All")

    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("SELECT id FROM students WHERE id = ?", (student_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Student not found"}), 404

        query = """
            SELECT t.name as teacher_name,
                   r.date,
                   r.attendance, r.participation, r.effort, r.respect
            FROM grade_from_teacher_to_student r
            JOIN teachers t ON r.teacher_id = t.id
            WHERE r.student_id = ?
              AND r.date BETWEEN ? AND ?
        """
        params = [student_id, date_from, date_to]

        if teacher_name != "All":
            query += " AND t.name = ?"
            params.append(teacher_name)

        query += " ORDER BY r.date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

    result = [{
        "teacher": row["teacher_name"],
        "date": row["date"],
        "attendance": row["attendance"],
        "participation": row["participation"],
        "effort": row["effort"],
        "respect": row["respect"]
    } for row in rows]

    return jsonify(result)


# 🔹 Ученик оценивает преподавателя
@student_bp.route("/rate-teacher", methods=["POST"])
@token_required
@limiter.limit("20 per minute")
def rate_teacher():
    data = request.json
    required = ["student_id", "teacher_id", "interest", "teaching", "comfort", "respect"]

    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    today = date.today().isoformat()

    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            INSERT OR REPLACE INTO grade_from_student_to_teacher
            (student_id, teacher_id, date, interest, teaching, comfort, respect)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["student_id"],
            data["teacher_id"],
            today,
            data["interest"],
            data["teaching"],
            data["comfort"],
            data["respect"]
        ))
        db.commit()

    return jsonify({"status": "success", "date": today})


# 🔹 Получить аккаунт ученика
@student_bp.route("/<int:student_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_student_account(student_id):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, name, clas, login, phone, email, photo
            FROM students
            WHERE id = ?
        """, (student_id,))
        row = cursor.fetchone()

    if not row:
        return jsonify({"error": "Student not found"}), 404

    photo_base64 = base64.b64encode(row["photo"]).decode('utf-8') if row["photo"] else None

    return jsonify({
        "id": row["id"],
        "name": row["name"],
        "class": row["clas"],  # возвращаем как "class", но из поля "clas"
        "login": row["login"],
        "phone": row["phone"],
        "email": row["email"],
        "photo": photo_base64
    })