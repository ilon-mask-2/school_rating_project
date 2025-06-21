import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🧹 Удаление старых таблиц...")
    cursor.executescript("""
        DROP TABLE IF EXISTS grade_from_student_to_teacher;
        DROP TABLE IF EXISTS grade_from_teacher_to_student;
        DROP TABLE IF EXISTS student_group_relationships;
        DROP TABLE IF EXISTS study_groups;
        DROP TABLE IF EXISTS students;
        DROP TABLE IF EXISTS teachers;
        DROP TABLE IF EXISTS admins;
    """)

    print("📦 Создание таблиц...")
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            clas TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            photo BLOB
        );

        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            photo BLOB
        );

        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS study_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            teacher_id INTEGER,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS student_group_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES study_groups (id) ON DELETE CASCADE,
            UNIQUE(student_id, group_id)
        );

        CREATE TABLE IF NOT EXISTS grade_from_teacher_to_student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            attendance INTEGER CHECK(attendance BETWEEN 1 AND 10),
            participation INTEGER CHECK(participation BETWEEN 1 AND 10),
            effort INTEGER CHECK(effort BETWEEN 1 AND 10),
            respect INTEGER CHECK(respect BETWEEN 1 AND 10),
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id) ON DELETE CASCADE,
            UNIQUE(student_id, teacher_id, date)
        );

        CREATE TABLE IF NOT EXISTS grade_from_student_to_teacher (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            interest INTEGER CHECK(interest BETWEEN 1 AND 10),
            teaching INTEGER CHECK(teaching BETWEEN 1 AND 10),
            comfort INTEGER CHECK(comfort BETWEEN 1 AND 10),
            respect INTEGER CHECK(respect BETWEEN 1 AND 10),
            FOREIGN KEY (teacher_id) REFERENCES teachers (id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            UNIQUE(teacher_id, student_id, date)
        );
    """)

    print("👩‍🎓 Добавление студентов...")
    students = [
        ("Галкин Александр", "11A", "alexg", "12345", "alexg@mail.com", "0501234567", None),
        ("Ирина Котова", "10Б", "irinak", "password123", "irinak@mail.com", "0507654321", None),
        ("Семен Иванов", "11A", "semivan", "qwerty", "semivan@mail.com", "0505555555", None),
        ("Мария Ли", "10Б", "mariali", "mypwd", "mariali@mail.com", "0509999999", None),
    ]
    cursor.executemany("""
        INSERT INTO students (name, clas, login, password, email, phone, photo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, students)

    print("👨‍🏫 Добавление преподавателей...")
    teachers = [
        ("Томи Танака", "tomit", "teachme", "tomit@mail.com", "0521111111", None),
        ("Йони", "yoniy", "pass456", "yoniy@mail.com", "0522222222", None),
        ("Лев Шмидт", "levs", "abc123", "levs@mail.com", "0523333333", None),
    ]
    cursor.executemany("""
        INSERT INTO teachers (name, login, password, email, phone, photo)
        VALUES (?, ?, ?, ?, ?, ?)
    """, teachers)

    print("🛡️ Добавление администратора...")
    cursor.execute("""
        INSERT INTO admins (login, password, name)
        VALUES (?, ?, ?)
    """, ("admin1", "adminpass", "Админ"))

    print("📘 Создание учебных групп...")
    cursor.execute("SELECT id FROM teachers WHERE name = 'Йони'")
    yoni_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM teachers WHERE name = 'Томи Танака'")
    tomi_id = cursor.fetchone()[0]

    groups = [
        ("Кибер-А", "Кибербезопасность", yoni_id),
        ("Физика-11A", "Физика", tomi_id),
    ]
    cursor.executemany("""
        INSERT INTO study_groups (name, subject, teacher_id)
        VALUES (?, ?, ?)
    """, groups)

    print("🔗 Привязка студентов к группам...")
    cursor.execute("SELECT id FROM students WHERE name = 'Галкин Александр'")
    alex_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM students WHERE name = 'Семен Иванов'")
    semen_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM students WHERE name = 'Мария Ли'")
    maria_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM study_groups WHERE name = 'Кибер-А'")
    cyber_group = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM study_groups WHERE name = 'Физика-11A'")
    physics_group = cursor.fetchone()[0]

    student_group_links = [
        (alex_id, cyber_group),
        (alex_id, physics_group),
        (semen_id, cyber_group),
        (maria_id, cyber_group),
    ]
    cursor.executemany("""
        INSERT INTO student_group_relationships (student_id, group_id)
        VALUES (?, ?)
    """, student_group_links)

    print("📝 Оценки преподавателей ученикам...")
    teacher_grades = [
        (alex_id, tomi_id, "2025-06-01", 8, 9, 10, 9),
        (semen_id, tomi_id, "2025-06-01", 7, 8, 9, 8),
    ]
    cursor.executemany("""
        INSERT INTO grade_from_teacher_to_student (
            student_id, teacher_id, date,
            attendance, participation, effort, respect
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, teacher_grades)

    print("📊 Оценки учеников преподавателям...")
    student_grades = [
        (tomi_id, alex_id, "2025-06-01", 10, 9, 9, 9),
        (tomi_id, semen_id, "2025-06-01", 9, 8, 8, 8),
    ]
    cursor.executemany("""
        INSERT INTO grade_from_student_to_teacher (
            teacher_id, student_id, date,
            interest, teaching, comfort, respect
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, student_grades)

    conn.commit()
    conn.close()
    print("✅ База данных успешно создана и заполнена.")

if __name__ == "__main__":
    seed_database()

