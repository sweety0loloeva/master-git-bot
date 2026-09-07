import sqlite3
import json
import os


def init_database():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "quiz.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаем таблицы, если их нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            question_text TEXT NOT NULL,
            option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT, option_e TEXT,
            correct_option TEXT NOT NULL,
            explanation TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY, 
            username TEXT, 
            first_name TEXT, 
            score INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question_id INTEGER,
            is_correct INTEGER,
            UNIQUE(user_id, question_id)
        )
    ''')

    files_to_import = ["english_tests.json"]

    for file_name in files_to_import:
        json_path = os.path.join(BASE_DIR, file_name)
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # ИСПРАВЛЕНИЕ: если данные завернуты в лишний список [[...]]
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    data = data[0]  # достаем внутренний список элементов

                for item in data:
                    # На всякий случай проверяем, что item — это словарь
                    if not isinstance(item, dict):
                        continue

                    topic_title = item.get("topic", "English")
                    cursor.execute("INSERT OR IGNORE INTO topics (title) VALUES (?)", (topic_title,))
                    cursor.execute("SELECT id FROM topics WHERE title = ?", (topic_title,))
                    topic_id = cursor.fetchone()[0]

                    q_text = item.get("question")
                    if not q_text:
                        continue

                    cursor.execute("SELECT id FROM questions WHERE question_text = ?", (q_text,))
                    if not cursor.fetchone():
                        opts = item.get("options", {})
                        cursor.execute('''
                            INSERT INTO questions 
                            (topic_id, question_text, option_a, option_b, option_c, option_d, option_e, correct_option, explanation) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (topic_id, q_text, opts.get("A"), opts.get("B"), opts.get("C"), opts.get("D"),
                              opts.get("E"),
                              item.get("correct"), item.get("explanation")))
    conn.commit()
    conn.close()
    print("✅ База обновлена! Структура users синхронизирована.")


if __name__ == "__main__":
    init_database()