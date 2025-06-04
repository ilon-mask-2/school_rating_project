import sqlite3
from server.config import DATABASE  # Убедись, что путь правильный и config.py доступен


def print_all_tables():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Получаем список всех таблиц
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cur.fetchall()]

    if not tables:
        print("❌ В базе данных нет таблиц.")
        return

    for table in tables:
        print(f"\n📌 Таблица: {table}")
        try:
            # Получаем информацию о столбцах
            cur.execute(f"PRAGMA table_info({table})")
            columns_info = cur.fetchall()
            columns = [col["name"] for col in columns_info if col["type"].upper() != "BLOB"]

            if not columns:
                print("  (в таблице только BLOB-поля)")
                continue

            # Получаем строки без BLOB-полей
            cur.execute(f"SELECT {', '.join(columns)} FROM {table}")
            rows = cur.fetchall()

            if not rows:
                print("  (пусто)")
                continue

            # Заголовки
            print("  " + " | ".join(columns))
            print("  " + "-" * 40)

            for row in rows:
                print("  " + " | ".join(str(row[col]) for col in columns))
        except Exception as e:
            print(f"  ⚠ Ошибка при выводе таблицы {table}: {e}")

    conn.close()


def print_all_tables1():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Получаем список всех таблиц
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cur.fetchall()]

    if not tables:
        print("❌ В базе данных нет таблиц.")
        return

    for table in tables:
        print(f"\n📌 Таблица: {table}")
        try:
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            if not rows:
                print("  (пусто)")
                continue

            # Заголовки
            print("  " + " | ".join(rows[0].keys()))
            print("  " + "-" * 40)

            for row in rows:
                print("  " + " | ".join(str(row[key]) for key in row.keys()))
        except Exception as e:
            print(f"  ⚠ Ошибка при выводе таблицы {table}: {e}")

    conn.close()

if __name__ == "__main__":
    print_all_tables()