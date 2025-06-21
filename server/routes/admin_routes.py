# server/routes/admin_routes.py

from flask import Blueprint, request, jsonify
import sqlite3
from server.config import DATABASE
import base64
from server.db.utils import get_db, is_safe_input, token_required, limiter, hash_password

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/group-members/<int:group_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_group_members(group_id):
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("""
            SELECT students.id, students.name, students.clas, students.email, students.phone
            FROM students
            JOIN student_group_relationships ON students.id = student_group_relationships.student_id
            WHERE student_group_relationships.group_id = ?
            ORDER BY students.name
        """, (group_id,))

        students = [dict(row) for row in cursor.fetchall()]
    return jsonify(students)

@admin_bp.route("/accounts", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def admin_get_accounts():
    role = request.args.get("role", "All")
    name = request.args.get("name", "").strip().lower()
    student_class = request.args.get("class", "").strip()
    group = request.args.get("group", "").strip()
    subject = request.args.get("subject", "").strip()

    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        result = []

        # === STUDENTS ===
        if role in ("All", "student"):
            query = "SELECT id, name, 'student' AS role FROM students WHERE 1=1"
            params = []

            if name:
                query += " AND LOWER(name) LIKE ?"
                params.append(f"%{name}%")

            if student_class:
                query += " AND clas = ?"
                params.append(student_class)

            cursor.execute(query, params)
            result.extend(cursor.fetchall())

        # === TEACHERS ===
        if role in ("All", "teacher"):
            query = "SELECT id, name, 'teacher' AS role FROM teachers WHERE 1=1"
            params = []

            if name:
                query += " AND LOWER(name) LIKE ?"
                params.append(f"%{name}%")

            if subject:
                query += """
                    AND id IN (
                        SELECT teacher_id FROM study_groups WHERE LOWER(subject) LIKE ?
                    )
                """
                params.append(f"%{subject.lower()}%")

            cursor.execute(query, params)
            result.extend(cursor.fetchall())

        # === ADMINS ===
        if role in ("All", "admin") and not (subject or student_class or group):
            query = "SELECT id, login AS name, 'admin' AS role FROM admins"
            params = []
            if name:
                query += " WHERE LOWER(login) LIKE ?"
                params.append(f"%{name}%")

            cursor.execute(query, params)
            result.extend(cursor.fetchall())

        # === ФИЛЬТР ПО ГРУППЕ ===
        if group:
            group_ids = set()

            cursor.execute("""
                SELECT student_id FROM student_group_relationships
                JOIN study_groups ON student_group_relationships.group_id = study_groups.id
                WHERE study_groups.name LIKE ?
            """, (f"%{group}%",))
            student_ids = {row["student_id"] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT teacher_id FROM study_groups WHERE name LIKE ?
            """, (f"%{group}%",))
            teacher_ids = {row["teacher_id"] for row in cursor.fetchall()}

            group_ids = student_ids.union(teacher_ids)
            result = [r for r in result if r["id"] in group_ids]

        return jsonify([
            {"id": row["id"], "name": row["name"], "role": row["role"]}
            for row in result
        ])

@admin_bp.route("/filter-options", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_filter_options():
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        # Предметы
        cursor.execute("SELECT DISTINCT subject FROM study_groups ORDER BY subject ASC")
        subjects = [row["subject"] for row in cursor.fetchall() if row["subject"]]

        # Классы
        cursor.execute("SELECT DISTINCT clas FROM students ORDER BY clas ASC")
        classes = [row["clas"] for row in cursor.fetchall() if row["clas"]]

        # Группы
        cursor.execute("SELECT DISTINCT name FROM study_groups ORDER BY name ASC")
        groups = [row["name"] for row in cursor.fetchall() if row["name"]]

    return jsonify({
        "subjects": subjects,
        "classes": classes,
        "groups": groups
    })

@admin_bp.route("/students_get/<int:student_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_student(student_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Основная информация
    cur.execute("""
        SELECT id, name, clas AS class, login, email, phone, photo
        FROM students
        WHERE id = ?
    """, (student_id,))
    student = cur.fetchone()
    if not student:
        return jsonify({"error": "Ученик не найден"}), 404

    student_data = dict(student)

    # Фото в base64
    if student_data["photo"]:
        student_data["photo"] = base64.b64encode(student_data["photo"]).decode("utf-8")

    # Учебные группы
    cur.execute("""
        SELECT sg.name
        FROM study_groups sg
        JOIN student_group_relationships sgr ON sg.id = sgr.group_id
        WHERE sgr.student_id = ?
    """, (student_id,))
    student_data["groups"] = [row["name"] for row in cur.fetchall()]

    # Преподаватели и предметы
    cur.execute("""
        SELECT DISTINCT sg.subject, t.name
        FROM teachers t
        JOIN study_groups sg ON sg.teacher_id = t.id
        JOIN student_group_relationships sgr ON sg.id = sgr.group_id
        WHERE sgr.student_id = ?
    """, (student_id,))
    student_data["teachers"] = [
        f"{row['subject']} ({row['name']})" for row in cur.fetchall()
    ]

    return jsonify(student_data)

@admin_bp.route("/students_del/<int:student_id>", methods=["DELETE"])
@token_required
@limiter.limit("20 per minute")
def delete_student(student_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка, существует ли ученик
    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cur.fetchone()
    if not student:
        return jsonify({"error": "Ученик не найден"}), 404

    # Удаляем ученика и все связи
    cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
    cur.execute("DELETE FROM student_group_relationships WHERE student_id = ?", (student_id,))
    cur.execute("DELETE FROM student_teacher_ratings WHERE student_id = ?", (student_id,))
    cur.execute("DELETE FROM teacher_student_ratings WHERE student_id = ?", (student_id,))
    conn.commit()

    return jsonify({
        "status": "deleted",
        "id": student_id,
        "name": student["name"]
    })

@admin_bp.route("/students_put/<int:student_id>", methods=["PUT"])
@token_required
@limiter.limit("20 per minute")
def update_student(student_id):
    data = request.get_json()

    required_fields = ["name", "class", "login", "email", "phone"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    photo = data.get("photo")
    if photo:
        try:
            photo = base64.b64decode(photo)
        except Exception:
            return jsonify({"error": "Invalid photo format"}), 400
    else:
        photo = None

    password = data.get("password")
    if password:
        import hashlib
        password = hash_password(password)

    with sqlite3.connect(DATABASE) as db:
        if password:
            db.execute("""
                UPDATE students
                SET name = ?, clas = ?, login = ?, password = ?, email = ?, phone = ?, photo = ?
                WHERE id = ?
            """, (data["name"], data["class"], data["login"], password, data["email"], data["phone"], photo, student_id))
        else:
            db.execute("""
                UPDATE students
                SET name = ?, clas = ?, login = ?, email = ?, phone = ?, photo = ?
                WHERE id = ?
            """, (data["name"], data["class"], data["login"], data["email"], data["phone"], photo, student_id))
        db.commit()

    return jsonify({"status": "success", "id": student_id})


@admin_bp.route("/teachers_get/<int:teacher_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_teacher(teacher_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Получаем основную информацию о преподавателе
    cur.execute("""
        SELECT id, name, login, email, phone, photo
        FROM teachers
        WHERE id = ?
    """, (teacher_id,))
    teacher = cur.fetchone()
    if not teacher:
        return jsonify({"error": "Преподаватель не найден"}), 404

    teacher_data = dict(teacher)

    # Преобразуем фото в base64
    if teacher_data["photo"]:
        teacher_data["photo"] = base64.b64encode(teacher_data["photo"]).decode("utf-8")

    # Группы, которые ведёт преподаватель
    cur.execute("""
        SELECT name
        FROM study_groups
        WHERE teacher_id = ?
        ORDER BY name
    """, (teacher_id,))
    teacher_data["groups"] = [row["name"] for row in cur.fetchall()]

    return jsonify(teacher_data)


@admin_bp.route("/teachers_put/<int:teacher_id>", methods=["PUT"])
@token_required
@limiter.limit("20 per minute")
def update_teacher(teacher_id):
    data = request.get_json()

    required_fields = ["name", "login", "email", "phone"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    photo = data.get("photo")
    if photo:
        try:
            photo = base64.b64decode(photo)
        except Exception:
            return jsonify({"error": "Invalid photo format"}), 400
    else:
        photo = None

    password = data.get("password")
    if password:
        password = hash_password(password)

    with sqlite3.connect(DATABASE) as db:
        if password:
            db.execute("""
                UPDATE teachers
                SET name = ?, login = ?, password = ?, email = ?, phone = ?, photo = ?
                WHERE id = ?
            """, (data["name"], data["login"], password, data["email"], data["phone"], photo, teacher_id))
        else:
            db.execute("""
                UPDATE teachers
                SET name = ?, login = ?, email = ?, phone = ?, photo = ?
                WHERE id = ?
            """, (data["name"], data["login"], data["email"], data["phone"], photo, teacher_id))
        db.commit()

    return jsonify({"status": "success", "id": teacher_id})

@admin_bp.route("/teachers_del/<int:teacher_id>", methods=["DELETE"])
@token_required
@limiter.limit("20 per minute")
def delete_teacher(teacher_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка, существует ли преподаватель
    cur.execute("SELECT * FROM teachers WHERE id = ?", (teacher_id,))
    teacher = cur.fetchone()
    if not teacher:
        return jsonify({"error": "Преподаватель не найден"}), 404

    # Удаление оценок, выставленных ученикам
    cur.execute("DELETE FROM grade_from_teacher_to_student WHERE teacher_id = ?", (teacher_id,))
    # Удаление оценок, полученных от учеников
    cur.execute("DELETE FROM grade_from_student_to_teacher WHERE teacher_id = ?", (teacher_id,))
    # Удаление учебных групп, закреплённых за этим преподавателем
    cur.execute("DELETE FROM study_groups WHERE teacher_id = ?", (teacher_id,))
    # Удаление самого преподавателя
    cur.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))

    conn.commit()

    return jsonify({
        "status": "deleted",
        "id": teacher_id,
        "name": teacher["name"]
    })

@admin_bp.route("/admins_get/<int:admin_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_admin(admin_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, login, name FROM admins WHERE id = ?", (admin_id,))
    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Админ не найден"}), 404

    return jsonify(dict(row))

@admin_bp.route("/admins_put/<int:admin_id>", methods=["PUT"])
@token_required
@limiter.limit("20 per minute")
def update_admin(admin_id):
    data = request.get_json()
    login = data.get("login", "").strip()
    password = data.get("password", "").strip()

    if not is_safe_input(login, allow_spaces=False) or (password and not is_safe_input(password, allow_spaces=False)):
        return jsonify({"error": "Недопустимые символы"}), 400
    if not login:
        return jsonify({"error": "Логин обязателен"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка существования администратора
    cur.execute("SELECT * FROM admins WHERE id = ?", (admin_id,))
    existing = cur.fetchone()
    if not existing:
        return jsonify({"error": "Админ не найден"}), 404

    # Хеширование пароля, если он был передан
    if password:
        hashed_password = hash_password(password)
        cur.execute("""
            UPDATE admins
            SET login = ?, password = ?
            WHERE id = ?
        """, (login, hashed_password, admin_id))
    else:
        cur.execute("""
            UPDATE admins
            SET login = ?
            WHERE id = ?
        """, (login, admin_id))

    conn.commit()

    # Возврат обновлённых данных
    cur.execute("SELECT id, login FROM admins WHERE id = ?", (admin_id,))
    updated_admin = dict(cur.fetchone())
    return jsonify({
        "status": "success",
        "admin": updated_admin
    }) 


@admin_bp.route("/admins_del/<int:admin_id>", methods=["DELETE"])
@token_required
@limiter.limit("20 per minute")
def delete_admin(admin_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка существования админа
    cur.execute("SELECT * FROM admins WHERE id = ?", (admin_id,))
    admin = cur.fetchone()
    if not admin:
        return jsonify({"error": "Админ не найден"}), 404

    # Удаление
    cur.execute("DELETE FROM admins WHERE id = ?", (admin_id,))
    conn.commit()

    return jsonify({
        "status": "deleted",
        "id": admin_id,
        "login": admin["login"]
    })

@admin_bp.route("/students", methods=["POST"])
@token_required
@limiter.limit("20 per minute")
def create_student():
    data = request.get_json()
    required = ["name", "class", "login", "password"]

    if not all(data.get(k) for k in required):
        return jsonify({"error": "Заполните все обязательные поля"}), 400

    name = data["name"].strip()
    student_class = data["class"].strip().upper()
    login = data["login"].strip()
    password = data["password"].strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    photo_base64 = data.get("photo")
    if not is_safe_input(login, allow_spaces=False) or not is_safe_input(password, allow_spaces=False):
        return jsonify({"error": "Недопустимые символы"}), 400
    # Декодируем фото
    try:
        photo_blob = base64.b64decode(photo_base64) if photo_base64 else None
    except Exception:
        return jsonify({"error": "Ошибка при декодировании фото"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка: занят ли логин?
    cur.execute("SELECT id FROM students WHERE login = ?", (login,))
    if cur.fetchone():
        return jsonify({"error": "Логин уже занят"}), 409

    # Вставка нового ученика
    cur.execute("""
        INSERT INTO students (name, clas, login, password, email, phone, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, student_class, login, password, email, phone, photo_blob))
    conn.commit()

    new_id = cur.lastrowid

    return jsonify({
        "status": "created",
        "id": new_id,
        "name": name,
        "class": student_class
    })

@admin_bp.route("/teachers", methods=["POST"])
@token_required
@limiter.limit("20 per minute")
def create_teacher():
    data = request.get_json()
    required = ["name", "login", "password"]

    if not all(data.get(k) for k in required):
        return jsonify({"error": "Заполните все обязательные поля"}), 400

    name = data["name"].strip()
    login = data["login"].strip()
    password = data["password"].strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    photo_base64 = data.get("photo")
    if not is_safe_input(login, allow_spaces=False) or not is_safe_input(password, allow_spaces=False):
        return jsonify({"error": "Недопустимые символы"}), 400
    # Декодирование изображения
    try:
        photo_blob = base64.b64decode(photo_base64) if photo_base64 else None
    except Exception:
        return jsonify({"error": "Ошибка при декодировании фото"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка на занятый логин
    cur.execute("SELECT id FROM teachers WHERE login = ?", (login,))
    if cur.fetchone():
        return jsonify({"error": "Логин уже занят"}), 409

    # Вставка нового преподавателя
    cur.execute("""
        INSERT INTO teachers (name, login, password, email, phone, photo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, login, password, email, phone, photo_blob))
    conn.commit()

    teacher_id = cur.lastrowid

    return jsonify({
        "status": "created",
        "id": teacher_id,
        "name": name
    })

@admin_bp.route("/admins", methods=["POST"])
@token_required
@limiter.limit("20 per minute")
def create_admin():
    data = request.get_json()
    required = ["name", "login", "password"]

    # Проверка на наличие всех обязательных полей
    if not all(data.get(k) for k in required):
        return jsonify({"error": "Заполните имя, логин и пароль"}), 400

    name = data["name"].strip()
    login = data["login"].strip()
    password = data["password"].strip()

    # Валидация полей
    if not is_safe_input(name) or not is_safe_input(login, allow_spaces=False) or not is_safe_input(password, allow_spaces=False):
        return jsonify({"error": "Недопустимые символы"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка уникальности логина
    cur.execute("SELECT id FROM admins WHERE login = ?", (login,))
    if cur.fetchone():
        return jsonify({"error": "Логин уже занят"}), 409

    # Вставка нового администратора
    cur.execute("""
        INSERT INTO admins (name, login, password)
        VALUES (?, ?, ?)
    """, (name, login, password))
    conn.commit()

    admin_id = cur.lastrowid

    return jsonify({
        "status": "created",
        "id": admin_id,
        "login": login,
        "name": name
    })

@admin_bp.route("/groups", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_all_groups():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Основные данные по группам
    cur.execute("""
        SELECT 
            sg.id,
            sg.name,
            sg.subject,
            t.name AS teacher_name,
            (
                SELECT COUNT(*) 
                FROM student_group_relationships 
                WHERE group_id = sg.id
            ) AS student_count
        FROM study_groups sg
        LEFT JOIN teachers t ON sg.teacher_id = t.id
        ORDER BY sg.name
    """)
    base_groups = cur.fetchall()

    # Все участники групп
    cur.execute("""
        SELECT sgr.group_id, s.name
        FROM student_group_relationships sgr
        JOIN students s ON sgr.student_id = s.id
        ORDER BY s.name
    """)
    student_map = {}
    for row in cur.fetchall():
        student_map.setdefault(row["group_id"], []).append(row["name"])

    # Сбор финального списка
    groups = []
    for row in base_groups:
        groups.append({
            "id": row["id"],
            "name": row["name"],
            "subject": row["subject"],
            "teacher": row["teacher_name"] or "—",
            "student_count": row["student_count"],
            "students": student_map.get(row["id"], [])
        })

    return jsonify(groups)

@admin_bp.route("/group-filter-options", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_group_filter_options():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Уникальные предметы
    cur.execute("SELECT DISTINCT subject FROM study_groups ORDER BY subject ASC")
    subjects = [row["subject"] for row in cur.fetchall() if row["subject"]]

    # Все преподаватели (имена)
    cur.execute("SELECT name FROM teachers ORDER BY name ASC")
    teachers = [row["name"] for row in cur.fetchall()]

    # Все ученики (имена)
    cur.execute("SELECT name FROM students ORDER BY name ASC")
    students = [row["name"] for row in cur.fetchall()]

    return jsonify({
        "subjects": subjects,
        "teachers": teachers,
        "students": students
    })

@admin_bp.route("/groups/<int:group_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_group_details(group_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Основная информация о группе
    cur.execute("""
        SELECT sg.id, sg.name, sg.subject, t.name AS teacher
        FROM study_groups sg
        LEFT JOIN teachers t ON sg.teacher_id = t.id
        WHERE sg.id = ?
    """, (group_id,))
    group = cur.fetchone()
    if not group:
        return jsonify({"error": "Группа не найдена"}), 404

    group_data = {
        "id": group["id"],
        "name": group["name"],
        "subject": group["subject"],
        "teacher": group["teacher"] or "—"
    }

    # Участники группы
    cur.execute("""
        SELECT s.id, s.name, s.clas
        FROM students s
        JOIN student_group_relationships sgr ON s.id = sgr.student_id
        WHERE sgr.group_id = ?
        ORDER BY s.name ASC
    """, (group_id,))
    students = [dict(row) for row in cur.fetchall()]
    group_data["students"] = students

    return jsonify(group_data)

@admin_bp.route("/group-edit-options", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_group_edit_options():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Учителя
    cur.execute("SELECT name FROM teachers ORDER BY name")
    teachers = [row["name"] for row in cur.fetchall()]

    # Уникальные классы
    cur.execute("SELECT DISTINCT clas FROM students ORDER BY clas")
    classes = [row["clas"] for row in cur.fetchall()]

    # Ученики (с классом для отображения)
    cur.execute("SELECT name, clas FROM students ORDER BY name")
    students = [f"{row['name']} | {row['clas']}" for row in cur.fetchall()]

    return jsonify({
        "teachers": teachers,
        "classes": classes,
        "students": students
    })

@admin_bp.route("/groups/<int:group_id>", methods=["PUT"])
@token_required
@limiter.limit("20 per minute")
def update_group(group_id):
    data = request.get_json()
    name = data.get("name", "").strip()
    teacher_name = data.get("teacher", "").strip()

    if not name:
        return jsonify({"error": "Название группы обязательно"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка существования группы
    cur.execute("SELECT id FROM study_groups WHERE id = ?", (group_id,))
    if not cur.fetchone():
        return jsonify({"error": "Группа не найдена"}), 404

    # Получение ID преподавателя
    teacher_id = None
    if teacher_name:
        cur.execute("SELECT id FROM teachers WHERE name = ?", (teacher_name,))
        teacher_row = cur.fetchone()
        if not teacher_row:
            return jsonify({"error": "Преподаватель не найден"}), 400
        teacher_id = teacher_row["id"]

    # Обновление группы
    cur.execute("""
        UPDATE study_groups
        SET name = ?, teacher_id = ?
        WHERE id = ?
    """, (name, teacher_id, group_id))
    conn.commit()

    return jsonify({
        "status": "updated",
        "group_id": group_id,
        "name": name,
        "teacher_id": teacher_id
    })

@admin_bp.route("/groups/<int:group_id>/add-student", methods=["POST"])
@token_required
@limiter.limit("20 per minute")
def add_student_to_group(group_id):
    data = request.get_json()
    student_name = data.get("student_name", "").strip()

    if not student_name:
        return jsonify({"error": "Имя ученика обязательно"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка существования группы
    cur.execute("SELECT id FROM study_groups WHERE id = ?", (group_id,))
    if not cur.fetchone():
        return jsonify({"error": "Группа не найдена"}), 404

    # Поиск ID ученика
    cur.execute("SELECT id FROM students WHERE name = ?", (student_name,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "Ученик не найден"}), 404

    student_id = row["id"]

    # Проверка: не состоит ли уже в группе
    cur.execute("""
        SELECT 1 FROM student_group_relationships
        WHERE student_id = ? AND group_id = ?
    """, (student_id, group_id))
    if cur.fetchone():
        return jsonify({
            "status": "already exists",
            "student_id": student_id
        }), 200

    # Добавление
    cur.execute("""
        INSERT INTO student_group_relationships (student_id, group_id)
        VALUES (?, ?)
    """, (student_id, group_id))
    conn.commit()

    return jsonify({
        "status": "added",
        "student_id": student_id,
        "group_id": group_id
    })

@admin_bp.route("/groups/<int:group_id>/remove-student", methods=["POST"])
@token_required
@limiter.limit("20 per minute")
def remove_student_from_group(group_id):
    data = request.get_json()
    student_id = data.get("student_id")

    if not student_id:
        return jsonify({"error": "student_id обязателен"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Проверка существования связи
    cur.execute("""
        SELECT 1 FROM student_group_relationships
        WHERE student_id = ? AND group_id = ?
    """, (student_id, group_id))
    if not cur.fetchone():
        return jsonify({"error": "Связь не найдена"}), 404

    # Удаление связи
    cur.execute("""
        DELETE FROM student_group_relationships
        WHERE student_id = ? AND group_id = ?
    """, (student_id, group_id))
    conn.commit()

    return jsonify({
        "status": "removed",
        "student_id": student_id,
        "group_id": group_id
    })

@admin_bp.route("/groups", methods=["POST"])
@token_required
@limiter.limit("20 per minute")
def create_group():
    data = request.get_json()
    name = data.get("name", "").strip()
    subject = data.get("subject", "").strip()
    teacher_name = data.get("teacher", "").strip()

    if not name or not subject:
        return jsonify({"error": "Название и предмет обязательны"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Получаем ID преподавателя по имени
    teacher_id = None
    if teacher_name:
        cur.execute("SELECT id FROM teachers WHERE name = ?", (teacher_name,))
        teacher_row = cur.fetchone()
        if not teacher_row:
            return jsonify({"error": "Преподаватель не найден"}), 400
        teacher_id = teacher_row["id"]

    # Вставка группы
    cur.execute("""
        INSERT INTO study_groups (name, subject, teacher_id)
        VALUES (?, ?, ?)
    """, (name, subject, teacher_id))
    conn.commit()

    group_id = cur.lastrowid

    return jsonify({
        "status": "created",
        "id": group_id,
        "name": name,
        "subject": subject,
        "teacher_id": teacher_id
    })

@admin_bp.route("/student-ratings/filters", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_student_rating_filters():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Даты
    cur.execute("""
        SELECT DISTINCT date 
        FROM grade_from_teacher_to_student 
        WHERE date IS NOT NULL
        ORDER BY date DESC
    """)
    dates = [row["date"] for row in cur.fetchall()]

    # Преподаватели
    cur.execute("""
        SELECT DISTINCT t.name 
        FROM teachers t
        JOIN grade_from_teacher_to_student g ON t.id = g.teacher_id
        ORDER BY t.name
    """)
    teachers = [row["name"] for row in cur.fetchall()]

    # Классы
    cur.execute("""
        SELECT DISTINCT clas 
        FROM students 
        WHERE clas IS NOT NULL
        ORDER BY clas
    """)
    classes = [row["clas"] for row in cur.fetchall()]

    # Учебные группы
    cur.execute("""
        SELECT DISTINCT name 
        FROM study_groups 
        WHERE name IS NOT NULL
        ORDER BY name
    """)
    groups = [row["name"] for row in cur.fetchall()]

    return jsonify({
        "dates": dates,
        "teachers": teachers,
        "classes": classes,
        "groups": groups
    })

@admin_bp.route("/student-ratings", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_student_ratings():
    args = request.args
    date_from = args.get("date_from", "0000-00-00")
    date_to = args.get("date_to", "9999-12-31")
    teacher = args.get("teacher", "All")
    class_ = args.get("class", "All")
    group = args.get("group", "All")
    sort = args.get("sort", "overall")
    order = args.get("order", "desc").upper()

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Основной SELECT
    query = """
        SELECT s.id, s.name, s.clas AS class,
               ROUND(AVG(r.attendance), 2) AS attendance,
               ROUND(AVG(r.participation), 2) AS participation,
               ROUND(AVG(r.effort), 2) AS effort,
               ROUND(AVG(r.respect), 2) AS respect,
               ROUND(AVG((r.attendance + r.participation + r.effort + r.respect) / 4.0), 2) AS overall
        FROM grade_from_teacher_to_student r
        JOIN students s ON r.student_id = s.id
        JOIN teachers t ON r.teacher_id = t.id
    """

    # Условия
    conditions = ["r.date BETWEEN ? AND ?"]
    params = [date_from, date_to]

    if teacher != "All":
        conditions.append("t.name = ?")
        params.append(teacher)

    if class_ != "All":
        conditions.append("s.clas = ?")
        params.append(class_)

    if group != "All":
        query += """
            JOIN student_group_relationships sgr ON s.id = sgr.student_id
            JOIN study_groups sg ON sgr.group_id = sg.id
        """
        conditions.append("sg.name = ?")
        params.append(group)

    # WHERE + GROUP + ORDER
    query += " WHERE " + " AND ".join(conditions)
    query += " GROUP BY s.id"

    # Сортировка
    if sort not in ("attendance", "participation", "effort", "respect", "overall"):
        sort = "overall"
    if order not in ("ASC", "DESC"):
        order = "DESC"

    query += f" ORDER BY {sort} {order}"

    cur.execute(query, params)
    rows = cur.fetchall()

    return jsonify([dict(row) for row in rows])

@admin_bp.route("/student-id-by-name", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_student_id_by_name():
    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({"error": "Не указано имя"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id FROM students WHERE name = ?", (name,))
    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Ученик не найден"}), 404

    return jsonify({"id": row["id"], "name": name})

@admin_bp.route("/teacher-ratings", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_teacher_ratings():
    args = request.args
    date_from = args.get("date_from", "0000-00-00")
    date_to = args.get("date_to", "9999-12-31")
    teacher_name = args.get("teacher", "All")
    sort = args.get("sort", "overall")
    order = args.get("order", "DESC").upper()

    # Безопасная сортировка
    if sort not in ("interest", "teaching", "comfort", "respect", "overall"):
        sort = "overall"
    if order not in ("ASC", "DESC"):
        order = "DESC"

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Основной запрос
    query = """
        SELECT t.id, t.name,
               ROUND(AVG(g.interest), 2) AS interest,
               ROUND(AVG(g.teaching), 2) AS teaching,
               ROUND(AVG(g.comfort), 2) AS comfort,
               ROUND(AVG(g.respect), 2) AS respect,
               ROUND(AVG((g.interest + g.teaching + g.comfort + g.respect)/4.0), 2) AS overall
        FROM grade_from_student_to_teacher g
        JOIN teachers t ON g.teacher_id = t.id
        WHERE g.date BETWEEN ? AND ?
    """
    params = [date_from, date_to]

    if teacher_name != "All":
        query += " AND t.name = ?"
        params.append(teacher_name)

    query += f" GROUP BY t.id ORDER BY {sort} {order}"

    cur.execute(query, params)
    rows = cur.fetchall()

    return jsonify([dict(row) for row in rows])

@admin_bp.route("/teacher-id-by-name", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def get_teacher_id_by_name():
    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({"error": "Имя не указано"}), 400

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id FROM teachers WHERE name = ?", (name,))
    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Преподаватель не найден"}), 404

    return jsonify({"id": row["id"], "name": name})

@admin_bp.route("/student-detailed-ratings/<int:student_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def admin_student_detailed_ratings(student_id):
    date_from = request.args.get("date_from", "0000-00-00")
    date_to = request.args.get("date_to", "9999-12-31")
    teacher = request.args.get("teacher", "All")

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT t.name AS teacher,
               r.date,
               r.attendance,
               r.participation,
               r.effort,
               r.respect
        FROM grade_from_teacher_to_student r
        JOIN teachers t ON r.teacher_id = t.id
        WHERE r.student_id = ? AND r.date BETWEEN ? AND ?
    """
    params = [student_id, date_from, date_to]

    if teacher != "All":
        query += " AND t.name = ?"
        params.append(teacher)

    query += " ORDER BY r.date DESC"

    cur.execute(query, params)
    rows = cur.fetchall()

    return jsonify([dict(row) for row in rows])

@admin_bp.route("/teacher-detailed-ratings/<int:teacher_id>", methods=["GET"])
@token_required
@limiter.limit("20 per minute")
def admin_teacher_detailed_ratings(teacher_id):
    date_from = request.args.get("date_from", "0000-00-00")
    date_to = request.args.get("date_to", "9999-12-31")
    group = request.args.get("group", "All")

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT s.name AS student,
               sg.name AS "group",
               r.date,
               r.interest,
               r.teaching,
               r.comfort,
               r.respect
        FROM grade_from_student_to_teacher r
        JOIN students s ON r.student_id = s.id
        JOIN student_group_relationships sgr ON sgr.student_id = s.id
        JOIN study_groups sg ON sgr.group_id = sg.id
        WHERE r.teacher_id = ?
          AND sg.teacher_id = r.teacher_id
          AND r.date BETWEEN ? AND ?
    """
    params = [teacher_id, date_from, date_to]

    if group != "All":
        query += " AND sg.name = ?"
        params.append(group)

    query += " ORDER BY r.date DESC"

    try:
        cur.execute(query, params)
        rows = cur.fetchall()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "SQL execution failed", "details": str(e)}), 500

@admin_bp.route("/init-demo-data", methods=["POST"])
def init_demo_data():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Очистка
        cursor.execute("DELETE FROM student_teacher_ratings")
        cursor.execute("DELETE FROM teacher_student_ratings")
        cursor.execute("DELETE FROM students")
        cursor.execute("DELETE FROM teachers")
        cursor.execute("DELETE FROM admins")

        # === Ученики ===
        students = [
            ("Alice Ivanova", "alice", "pass123", "10A"),
            ("Bob Petrov", "bob", "pass123", "10A"),
            ("Clara Novak", "clara", "pass123", "10B"),
            ("Dima Sokolov", "dima", "pass123", "10B"),
        ]
        cursor.executemany(
            "INSERT INTO students (name, login, password, class) VALUES (?, ?, ?, ?)",
            students
        )

        # === Преподаватели ===
        teachers = [
            ("Mr. Smith", "smith", "pass123", "Math"),
            ("Mrs. Adams", "adams", "pass123", "Physics"),
        ]
        cursor.executemany(
            "INSERT INTO teachers (name, login, password, subject) VALUES (?, ?, ?, ?)",
            teachers
        )

        # === Администраторы ===
        admins = [
            ("Admin 1", "admin1", "admin123"),
            ("Admin 2", "admin2", "admin123"),
        ]
        cursor.executemany(
            "INSERT INTO admins (name, login, password) VALUES (?, ?, ?)",
            admins
        )

        # === Оценки студент → преподаватель ===
        ratings_st = [
            (1, 1, "2025-06-01", 5, 5, 5, 5, "Отличный учитель!"),
            (2, 1, "2025-06-02", 4, 4, 3, 4, "Хорошо объясняет."),
            (3, 2, "2025-06-02", 5, 5, 4, 5, "Очень интересно."),
            (4, 2, "2025-06-03", 3, 3, 3, 4, "Можно лучше."),
            (1, 2, "2025-06-04", 4, 5, 4, 4, "Понравился подход."),
        ]
        cursor.executemany(
            """INSERT INTO student_teacher_ratings 
               (student_id, teacher_id, date, interest, respect, comfort, teaching, comment) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ratings_st
        )

        # === Оценки преподаватель → студент ===
        ratings_ts = [
            (1, 1, "2025-06-01", 5, "Всегда активна"),
            (1, 2, "2025-06-02", 4, "Хорошая работа"),
            (2, 1, "2025-06-03", 3, "Есть куда расти"),
            (3, 2, "2025-06-04", 5, "Очень сильная ученица"),
            (4, 2, "2025-06-05", 4, "Хорошее понимание материала"),
        ]
        cursor.executemany(
            """INSERT INTO teacher_student_ratings 
               (teacher_id, student_id, date, grade, comment) 
               VALUES (?, ?, ?, ?, ?)""",
            ratings_ts
        )

        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "All demo data inserted"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@admin_bp.route("/init-db-and-seed", methods=["POST"])
def init_db_and_seed():
    import sqlite3
    import os
    import hashlib

    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    try:
        DB_PATH = os.path.join(os.path.dirname(__file__), "../db/database.db")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Удаление таблиц
        cursor.executescript("""
        DROP TABLE IF EXISTS students;
        DROP TABLE IF EXISTS teachers;
        DROP TABLE IF EXISTS admins;
        DROP TABLE IF EXISTS study_groups;
        DROP TABLE IF EXISTS student_group_relationships;
        DROP TABLE IF EXISTS student_teacher_ratings;
        DROP TABLE IF EXISTS teacher_student_ratings;
        """)

        # Создание таблиц
        cursor.executescript("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            class TEXT,
            email TEXT,
            phone TEXT
        );
        CREATE TABLE teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            subject TEXT,
            email TEXT,
            phone TEXT
        );
        CREATE TABLE admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT
        );
        CREATE TABLE study_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            teacher_id INTEGER,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        );
        CREATE TABLE student_group_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            study_group_id INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (study_group_id) REFERENCES study_groups(id)
        );
        CREATE TABLE student_teacher_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            interest INTEGER,
            teaching INTEGER,
            comfort INTEGER,
            respect INTEGER,
            comment TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        );
        CREATE TABLE teacher_student_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            clarity INTEGER,
            behavior INTEGER,
            diligence INTEGER,
            comment TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
        """)

        # Студенты
        students = [
            ("Галкин Александр", "alexg", hash_password("12345"), "11A", "alexg@example.com", "+972501234567"),
            ("Ирина Котова", "irinak", hash_password("password123"), "10Б", "irinak@example.com", "+972502345678"),
            ("Семен Иванов", "semivan", hash_password("qwerty"), "11A", "semivan@example.com", "+972503456789"),
            ("Мария Ли", "mariali", hash_password("mypwd"), "10Б", "mariali@example.com", "+972504567890"),
        ]
        cursor.executemany("""
            INSERT INTO students (name, login, password, class, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, students)

        # Преподаватели
        teachers = [
            ("Томи Танака", "tomit", hash_password("teachme"), "Математика", "tomit@example.com", "+972505678901"),
            ("Йони", "yoniy", hash_password("pass456"), "Кибербезопасность", "yoniy@example.com", "+972506789012"),
            ("Лев Шмидт", "levs", hash_password("abc123"), "Физика", "levs@example.com", "+972507890123"),
        ]
        cursor.executemany("""
            INSERT INTO teachers (name, login, password, subject, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, teachers)

        # Админ
        admins = [
            ("Admin", "admin1", hash_password("adminpass"), "admin@example.com", "+972508901234"),
        ]
        cursor.executemany("""
            INSERT INTO admins (name, login, password, email, phone)
            VALUES (?, ?, ?, ?, ?)
        """, admins)

        # Группы
        groups = [
            ("Группа 1", 1),  # Томи
            ("Группа 2", 2),  # Йони
        ]
        cursor.executemany("""
            INSERT INTO study_groups (name, teacher_id)
            VALUES (?, ?)
        """, groups)

        # Студент-группа
        student_group_relationships = [
            (1, 1), (2, 2), (3, 1), (4, 2),
        ]
        cursor.executemany("""
            INSERT INTO student_group_relationships (student_id, study_group_id)
            VALUES (?, ?)
        """, student_group_relationships)

        # Оценки студент → преподаватель
        ratings_st = [
            (1, 1, 5, 5, 5, 5, "Прекрасно объясняет!", "2025-06-01"),
            (2, 1, 4, 4, 4, 4, "Хороший преподаватель", "2025-06-02"),
            (3, 2, 3, 3, 3, 3, "Можно лучше", "2025-06-03"),
            (4, 3, 5, 5, 5, 5, "Очень круто", "2025-06-04"),
            (1, 2, 4, 5, 4, 4, "Неплохо", "2025-06-05"),
        ]
        cursor.executemany("""
            INSERT INTO student_teacher_ratings
            (student_id, teacher_id, interest, teaching, comfort, respect, comment, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ratings_st)

        # Оценки преподаватель → студент
        ratings_ts = [
            (1, 1, 5, 5, 5, "Отличный ученик", "2025-06-01"),
            (2, 2, 4, 4, 4, "Хорошо старается", "2025-06-02"),
            (3, 3, 3, 3, 3, "Средне", "2025-06-03"),
            (1, 4, 5, 5, 5, "Очень умная", "2025-06-04"),
            (3, 2, 4, 4, 4, "Подходит серьёзно", "2025-06-05"),
        ]
        cursor.executemany("""
            INSERT INTO teacher_student_ratings
            (teacher_id, student_id, clarity, behavior, diligence, comment, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ratings_ts)

        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "База создана и заполнена данными"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

