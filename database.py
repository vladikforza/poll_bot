import sqlite3


# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect("polls.db")
    conn.row_factory = sqlite3.Row
    return conn


# Инициализация базы данных
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
       CREATE TABLE IF NOT EXISTS subscribers (
           user_id INTEGER PRIMARY KEY
       )
       """)

    # Таблица ОПРОСОВ (polls)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL
    )
    """)

    # Таблица ВАРИАНТОВ ОТВЕТОВ ДЛЯ ОПРОСОВ
    cur.execute("""
    CREATE TABLE IF NOT EXISTS poll_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER,
        option_text TEXT NOT NULL,
        FOREIGN KEY (poll_id) REFERENCES polls(id)
    )
    """)

    # Таблица ГОЛОСОВ ДЛЯ ОПРОСОВ
    cur.execute("""
    CREATE TABLE IF NOT EXISTS poll_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER,
        user_id INTEGER,
        choice TEXT,
        FOREIGN KEY (poll_id) REFERENCES polls(id)
    )
    """)

    # Таблица ГОЛОСОВАНИЙ (votes)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL
    )
    """)

    # Таблица ВАРИАНТОВ ОТВЕТОВ ДЛЯ ГОЛОСОВАНИЙ
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vote_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vote_id INTEGER,
        option_text TEXT NOT NULL,
        FOREIGN KEY (vote_id) REFERENCES votes(id)
    )
    """)

    # Таблица ГОЛОСОВ ДЛЯ ГОЛОСОВАНИЙ
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vote_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vote_id INTEGER,
        user_id INTEGER,
        choice TEXT,
        FOREIGN KEY (vote_id) REFERENCES votes(id)
    )
    """)

    conn.commit()
    conn.close()

def add_subscriber(user):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO subscribers (user_id, username, first_name, last_name, language_code)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            language_code = excluded.language_code
    """, (
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        user.language_code
    ))
    conn.commit()
    conn.close()


# Получить список подписчиков
def get_subscribers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscribers ORDER BY user_id DESC")
    users = cur.fetchall()
    conn.close()
    return users




# Функция для добавления опроса и вариантов ответа
def create_poll(question, options):
    print(f"Создание опроса: {question}")  # Логирование

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Добавляем сам опрос
        cur.execute("INSERT INTO polls (question) VALUES (?)", (question,))
        poll_id = cur.lastrowid
        print(f"✅ Опрос записан в БД с ID: {poll_id}")

        # Проверяем, записался ли опрос
        if poll_id:
            print(f"✅ Опрос добавлен в базу (ID: {poll_id}, Вопрос: {question})")
        else:
            print("❌ Ошибка: Опрос не был добавлен!")

        # Добавляем варианты ответов
        for option in options:
            cur.execute("INSERT INTO poll_options (poll_id, option_text) VALUES (?, ?)", (poll_id, option))
            print(f"📌 Вариант ответа '{option}' записан в базу для опроса {poll_id}")

        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка при записи в базу: {e}")
    finally:
        conn.close()
    print(f"✅ Опрос создан с ID: {poll_id}")  # Логирование
    return poll_id  # Возвращаем ID созданного опроса


# Функция для добавления голосования
def create_vote(question, options):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO votes (question) VALUES (?)", (question,))
    vote_id = cur.lastrowid

    for option in options:
        cur.execute("INSERT INTO vote_options (vote_id, option_text) VALUES (?, ?)", (vote_id, option))

    conn.commit()
    conn.close()
    return vote_id  # Возвращаем ID созданного голосования

def get_all_polls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM polls")
    polls = cur.fetchall()
    conn.close()
    return polls

# Функция для получения опроса
def get_poll_by_id(poll_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM polls WHERE id = ?", (poll_id,))
    poll = cur.fetchone()

    cur.execute("SELECT option_text FROM poll_options WHERE poll_id = ?", (poll_id,))
    options = [row["option_text"] for row in cur.fetchall()]

    conn.close()
    return {"id": poll["id"], "question": poll["question"], "options": options} if poll else None

def get_poll_results(poll_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT option_text, COUNT(poll_votes.id) as votes
        FROM poll_options
        LEFT JOIN poll_votes ON poll_options.option_text = poll_votes.choice AND poll_options.poll_id = poll_votes.poll_id
        WHERE poll_options.poll_id = ?
        GROUP BY poll_options.option_text
    """, (poll_id,))

    results = cur.fetchall()
    conn.close()
    return [{"option": row["option_text"], "votes": row["votes"]} for row in results]

def update_poll(poll_id, new_question):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE polls SET question = ? WHERE id = ?", (new_question, poll_id))
    conn.commit()
    conn.close()

# Удалить опрос
def delete_poll(poll_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM polls WHERE id = ?", (poll_id,))
    conn.commit()
    conn.close()


# Функция для получения голосования
def get_vote_by_id(vote_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM votes WHERE id = ?", (vote_id,))
    vote = cur.fetchone()

    cur.execute("SELECT option_text FROM vote_options WHERE vote_id = ?", (vote_id,))
    options = [row["option_text"] for row in cur.fetchall()]

    conn.close()
    return {"id": vote["id"], "question": vote["question"], "options": options} if vote else None

def record_poll_vote(poll_id, user_id, choice):
    conn = get_db_connection()
    cur = conn.cursor()

    # Проверяем, голосовал ли уже пользователь
    cur.execute("SELECT * FROM poll_votes WHERE poll_id = ? AND user_id = ?", (poll_id, user_id))
    existing_vote = cur.fetchone()

    if existing_vote:
        conn.close()
        return False  # ❌ Пользователь уже голосовал

    # Записываем голос
    cur.execute("INSERT INTO poll_votes (poll_id, user_id, choice) VALUES (?, ?, ?)", (poll_id, user_id, choice))
    conn.commit()
    conn.close()
    return True  # ✅ Голос записан

def record_vote(vote_id, user_id, choice):
    conn = get_db_connection()
    cur = conn.cursor()

    # Проверяем, голосовал ли уже пользователь
    cur.execute("SELECT * FROM vote_results WHERE vote_id = ? AND user_id = ?", (vote_id, user_id))
    existing_vote = cur.fetchone()

    if existing_vote:
        conn.close()
        return False  # ❌ Пользователь уже голосовал

    # Записываем голос
    cur.execute("INSERT INTO vote_results (vote_id, user_id, choice) VALUES (?, ?, ?)", (vote_id, user_id, choice))
    conn.commit()
    conn.close()
    return True  # ✅ Голос записан
def get_all_votes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM votes")
    votes = cur.fetchall()
    conn.close()
    return votes

def delete_vote(vote_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM votes WHERE id = ?", (vote_id,))
    conn.commit()
    conn.close()

def get_vote_results(vote_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT option_text, COUNT(vote_results.id) as votes
        FROM vote_options
        LEFT JOIN vote_results ON vote_options.option_text = vote_results.choice AND vote_options.vote_id = vote_results.vote_id
        WHERE vote_options.vote_id = ?
        GROUP BY vote_options.option_text
    """, (vote_id,))
    results = cur.fetchall()
    conn.close()
    return [{"option": row["option_text"], "votes": row["votes"]} for row in results]

