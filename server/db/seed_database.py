import sqlite3
import hashlib
from datetime import date
import os
from server.db.utils import hash_password

# Абсолютный путь к базе данных
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "server", "database.db")


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Удаляем старые данные
    cur.executescript("""
        DELETE FROM student_group_relationships;
        DELETE FROM grade_from_teacher_to_student;
        DELETE FROM grade_from_student_to_teacher;
        DELETE FROM study_groups;
        DELETE FROM students;
        DELETE FROM teachers;
        DELETE FROM admins;
    """)

    # === Админы ===
    cur.execute("INSERT INTO admins (login, password, name) VALUES (?, ?, ?)",
                ("admin", hash_password("admin"), "Админ Один"))

    # === Преподаватели ===
    cur.execute("""
        INSERT INTO teachers (login, password, name, email, phone)
        VALUES (?, ?, ?, ?, ?)
    """, ("teacher", hash_password("teacher"), "Иванов Иван", "ivan@example.com", "1234567890"))
    teacher1_id = cur.lastrowid

    cur.execute("""
        INSERT INTO teachers (login, password, name, email, phone)
        VALUES (?, ?, ?, ?, ?)
    """, ("teacher2", hash_password("pass2"), "Петров Петр", "petr@example.com", "0987654321"))
    teacher2_id = cur.lastrowid

    # === Ученики ===
    cur.execute("""
        INSERT INTO students (login, password, name, clas, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("student", hash_password("student"), "Алексей", "10A", "alex@example.com", "111222333"))
    student1_id = cur.lastrowid

    cur.execute("""
        INSERT INTO students (login, password, name, clas, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("student2", hash_password("pass2"), "Мария", "10A", "masha@example.com", "444555666"))
    student2_id = cur.lastrowid

    # === Учебные группы ===
    cur.execute("INSERT INTO study_groups (name, subject, teacher_id) VALUES (?, ?, ?)",
                ("Алгебра 10A", "Алгебра", teacher1_id))
    group_id = cur.lastrowid

    # === Привязка учеников к группе ===
    cur.executemany("""
        INSERT INTO student_group_relationships (student_id, group_id)
        VALUES (?, ?)
    """, [(student1_id, group_id), (student2_id, group_id)])

    # === Оценки преподавателя ученикам ===
    today = date.today().isoformat()
    cur.execute("""
        INSERT INTO grade_from_teacher_to_student
        (teacher_id, student_id, date, attendance, participation, effort, respect)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (teacher1_id, student1_id, today, 9, 8, 10, 9))

    # === Оценки ученика преподавателю ===
    cur.execute("""
        INSERT INTO grade_from_student_to_teacher
        (student_id, teacher_id, date, interest, teaching, comfort, respect)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student1_id, teacher1_id, today, 10, 9, 9, 10))

    conn.commit()
    conn.close()
    print("✅ База данных заполнена тестовыми данными.")

seed()
