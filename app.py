from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import get_all_polls, get_poll_by_id, create_poll, update_poll, delete_poll, get_poll_results, \
    get_db_connection, create_vote, get_vote_by_id, delete_vote, get_vote_results
import requests
from keyboards import create_keyboard
from config import TOKEN
import json


app = Flask(__name__)
BOT_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"  # Telegram API


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    conn = get_db_connection()
    cur = conn.cursor()
    if query:
        cur.execute("SELECT id, question FROM polls WHERE question LIKE ? ORDER BY id DESC", (f"%{query}%",))
    else:
        cur.execute("SELECT id, question FROM polls ORDER BY id DESC")
    polls = cur.fetchall()
    conn.close()

    return render_template("index.html", polls=polls)


import json

@app.route("/send_poll", methods=["POST"])
def send_poll():
    from keyboards import create_keyboard

    conn = get_db_connection()
    cur = conn.cursor()

    # Берем последний созданный опрос
    cur.execute("SELECT id, question FROM polls ORDER BY id DESC LIMIT 1")
    poll = cur.fetchone()

    if not poll:
        print("❌ Ошибка: Нет активных опросов в БД")
        return jsonify({"error": "Нет активных опросов"}), 400

    poll_id = poll["id"]
    question = poll["question"]
    print(f"✅ Опрос найден в БД: ID={poll_id}, Вопрос='{question}'")


    # 📌 Получаем варианты ответа
    cur.execute("SELECT option_text FROM poll_options WHERE poll_id = ?", (poll_id,))
    options = [row["option_text"].strip() for row in cur.fetchall() if row["option_text"].strip()]
    conn.close()

    if not options:
        print("⚠️ Внимание: Нет вариантов ответа для опроса")
        options = []

    print(f"✅ Варианты ответа для опроса {poll_id}: {options}")

    # 📌 Генерируем inline-клавиатуру
    keyboard = create_keyboard(options, poll_id) if options else None

    if keyboard:
        try:
            keyboard_dict = keyboard.model_dump()

            # Удаляем `url`, если он есть
            for row in keyboard_dict["inline_keyboard"]:
                for button in row:
                    if "url" in button:
                        del button["url"]

            keyboard_json = json.dumps(keyboard_dict)

            print(f"✅ JSON-клавиатура перед отправкой: {keyboard_json}")

        except Exception as e:
            print(f"❌ Ошибка сериализации клавиатуры: {e}")
            keyboard_json = None
    else:
        keyboard_json = None

    # 📌 Проверяем подписчиков
    from database import get_subscribers
    subscribers = get_subscribers()

    if not subscribers:
        print("❌ Ошибка: Нет подписчиков для рассылки")
        return jsonify({"error": "Нет подписчиков для рассылки"}), 400

    print(f"📩 Рассылка опроса подписчикам: {subscribers}")

    # 📩 Отправляем опрос подписчикам
    for chat_id in subscribers:
        payload = {
            "chat_id": chat_id,
            "text": f"📊 *Новый опрос:*\n\n{question}",
            "parse_mode": "Markdown"
        }

        if keyboard_json:
            payload["reply_markup"] = json.loads(keyboard_json)

        print(f"📤 Отправляем запрос Telegram API: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        response = requests.post(BOT_URL, json=payload)

        if response.status_code != 200:
            print(f"❌ Ошибка отправки опроса пользователю {chat_id}: {response.text}")

    return jsonify({"success": "Опрос отправлен подписчикам"})


# Страница создания опроса
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        question = request.form["question"]
        options = request.form.getlist("options")  # Получаем список вариантов

        # Очистка пустых вариантов ответа
        options = [opt.strip() for opt in options if opt.strip()]

        if len(options) < 2:
            return "Ошибка: Необходимо минимум 2 заполненных варианта ответа", 400

        create_poll(question, options)  # Передаем оба аргумента
        requests.post("http://127.0.0.1:5000/send_poll")

        return redirect(url_for("index"))
    return render_template("create.html")

@app.route("/view/<int:poll_id>")
def view_poll(poll_id):
    poll = get_poll_by_id(poll_id)  # Получаем данные опроса

    if not poll:
        return "Опрос не найден", 404

    return render_template("view_poll.html", poll=poll)  # Отображаем новый шаблон

# Удаление опроса
@app.route("/delete/<int:poll_id>")
def delete(poll_id):
    delete_poll(poll_id)
    return redirect(url_for("index"))

# Просмотр статистики
@app.route("/stats/<int:poll_id>")
def stats(poll_id):
    poll = get_poll_by_id(poll_id)
    results = get_poll_results(poll_id)
    return render_template("stats.html", poll=poll, results=results)


@app.route("/create_vote", methods=["GET", "POST"])
def create_vote_page():
    if request.method == "POST":
        question = request.form["question"]
        options = request.form.getlist("options")
        create_vote(question, options)
        requests.post("http://127.0.0.1:5000/send_vote")
        return redirect(url_for("votes_index"))
    return render_template("create_vote.html")

@app.route("/votes")
def votes_index():
    query = request.args.get("q", "").strip()
    conn = get_db_connection()
    cur = conn.cursor()

    if query:
        cur.execute("SELECT id, question FROM votes WHERE question LIKE ? ORDER BY id DESC", (f"%{query}%",))
    else:
        cur.execute("SELECT id, question FROM votes ORDER BY id DESC")

    votes = cur.fetchall()
    conn.close()
    return render_template("votes.html", votes=votes)

@app.route("/view_vote/<int:vote_id>")
def view_vote(vote_id):
    vote = get_vote_by_id(vote_id)
    if not vote:
        return "Голосование не найдено", 404
    return render_template("view_vote.html", vote=vote)

@app.route("/delete_vote/<int:vote_id>")
def delete_vote_page(vote_id):
    delete_vote(vote_id)
    return redirect(url_for("votes_index"))

@app.route("/vote_stats/<int:vote_id>")
def vote_stats(vote_id):
    vote = get_vote_by_id(vote_id)
    results = get_vote_results(vote_id)
    return render_template("vote_stats.html", vote=vote, results=results)

@app.route("/send_vote", methods=["POST"])
def send_vote():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, question FROM votes ORDER BY id DESC LIMIT 1")
    vote = cur.fetchone()

    if not vote:
        print("❌ Нет голосований в БД")
        return jsonify({"error": "Нет голосований"}), 400

    vote_id = vote["id"]
    question = vote["question"]

    print(f"✅ Голосование найдено в БД: ID={vote_id}, Вопрос='{question}'")

    cur.execute("SELECT option_text FROM vote_options WHERE vote_id = ?", (vote_id,))
    options = [row["option_text"].strip() for row in cur.fetchall()]
    conn.close()

    print(f"✅ Варианты ответов голосования {vote_id}: {options}")

    if not options:
        print("⚠️ Нет вариантов ответа для голосования")
        return jsonify({"error": "Нет вариантов ответа для голосования"}), 400

    from keyboards import create_keyboard
    from database import get_subscribers
    keyboard = create_keyboard(options, vote_id, prefix="vote")
    keyboard_dict = keyboard.model_dump()

    if not keyboard:
        print("❌ Ошибка создания клавиатуры")
        return jsonify({"error": "Ошибка создания клавиатуры"}), 500

    for row in keyboard_dict["inline_keyboard"]:
        for btn in row:
            btn.pop("url", None)

    payload = {
        "text": f"🗳 *Новое голосование:*\n\n{question}",
        "parse_mode": "Markdown",
        "reply_markup": keyboard_dict,
    }

    subscribers = get_subscribers()
    if not subscribers:
        print("❌ Нет подписчиков для рассылки")
        return jsonify({"error": "Нет подписчиков для рассылки"}), 400

    print(f"📩 Рассылка голосования подписчикам: {subscribers}")

    for user_id in get_subscribers():
        payload["chat_id"] = user_id
        print(f"📤 Отправляю голосование пользователю {user_id}: {json.dumps(payload, ensure_ascii=False)}")
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=payload)

        response: requests.Response = requests.post(BOT_URL, json=payload)

        if response.status_code != 200:
            print(f"❌ Ошибка отправки голосования пользователю {user_id}: {response.text}")
        else:
            print(f"✅ Голосование успешно отправлено пользователю {user_id}")

    return jsonify({"success": "Голосование отправлено"})

@app.route("/subscribers")
def show_subscribers():
    from database import get_subscribers
    subscribers = get_subscribers()
    return render_template("subscribers.html", subscribers=subscribers)

@app.route("/subscriber/<int:user_id>")
def subscriber_detail(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Опросы (по убыванию poll_id)
    cur.execute("""
        SELECT p.question, v.choice
        FROM poll_votes v
        JOIN polls p ON v.poll_id = p.id
        WHERE v.user_id = ?
        ORDER BY v.poll_id DESC
    """, (user_id,))
    poll_votes = cur.fetchall()

    # Голосования (по убыванию vote_id)
    cur.execute("""
        SELECT v.question, r.choice
        FROM vote_results r
        JOIN votes v ON r.vote_id = v.id
        WHERE r.user_id = ?
        ORDER BY r.vote_id DESC
    """, (user_id,))
    vote_results = cur.fetchall()

    conn.close()
    return render_template("subscriber_detail.html", user_id=user_id, poll_votes=poll_votes, vote_results=vote_results)

@app.route("/user/<int:user_id>")
def user_info(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscribers WHERE user_id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()

    if not user:
        return "Пользователь не найден", 404

    return render_template("user_info.html", user=user)


if __name__ == "__main__":
    app.run(debug=True)