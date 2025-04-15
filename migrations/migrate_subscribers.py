import sqlite3

def migrate_subscribers_table():
    conn = sqlite3.connect("polls.db")
    cur = conn.cursor()

    def column_exists(cursor, table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        return column in [info[1] for info in cursor.fetchall()]

    # Создаем таблицу, если её нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()

    # Добавляем недостающие поля
    fields = {
        "username": "TEXT",
        "first_name": "TEXT",
        "last_name": "TEXT",
        "language_code": "TEXT"
    }

    for column, col_type in fields.items():
        if not column_exists(cur, "subscribers", column):
            print(f"Добавляем колонку: {column}")
            cur.execute(f"ALTER TABLE subscribers ADD COLUMN {column} {col_type}")

    conn.commit()
    conn.close()
    print("✅ Миграция завершена успешно")

if __name__ == "__main__":
    migrate_subscribers_table()
