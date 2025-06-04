import sqlite3
from server.config import DATABASE

def init_db():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
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
        db.commit()
        print("✅ База данных инициализирована.")

if __name__ == "__main__":
    init_db()