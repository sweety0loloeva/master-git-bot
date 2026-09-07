import asyncio
import sqlite3
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Ошибка: Токен бота не найден в переменных окружения (.env)")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    db_path = os.path.join(BASE_DIR, "quiz.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, params)
    res = None
    if fetchone:
        res = cursor.fetchone()
    elif fetchall:
        res = cursor.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return res


def check_and_register_user(user_id, username, first_name):
    db_query(
        "INSERT OR IGNORE INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name),
        commit=True
    )


def get_theory_eng(filename):
    filepath = os.path.join(BASE_DIR, "theory", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "❌ Теория по английскому не найдена."


def get_theory_alg(filename):
    filepath_with_ext = os.path.join(BASE_DIR, "algorithms", filename)
    name_without_ext = os.path.splitext(filename)[0]
    filepath_without_ext = os.path.join(BASE_DIR, "algorithms", name_without_ext)

    try:
        with open(filepath_with_ext, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        try:
            with open(filepath_without_ext, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"❌ Файл с алгоритмами не найден в папке 'algorithms'."


THEORY_ENG_MODULES = {
    "1": ("🐾 Модуль 1: Noun (Имя существительное) 🐈", "module1.txt"),
    "2": ("🐾 Модуль 2: Article (Артикль) 🐱", "module2.txt"),
    "3": ("🐾 Модуль 3: Adjective (Имя прилагательное) 🎀", "module3.txt"),
    "4": ("🐾 Модуль 4: Pronoun (Местоимения) 🎁", "module4.txt"),
    "5": ("🐾 Модуль 5: Numeral (Имя числительное) 🔢", "module5.txt"),
    "6": ("🐾 Модуль 6: Verb (Глагол) 🐈‍⬛", "module6.txt"),
    "7": ("🐾 Модуль 7: Non-finite verb forms (Неличные формы глагола) 🧶", "module7.txt"),
    "8": ("🐾 Модуль 8: Adverb (Наречие) 🧭", "module8.txt"),
    "9": ("🐾 Модуль 9: Preposition (Предлог) 📍", "module9.txt"),
    "10": ("🐾 Модуль 10: Mood (Наклонение глагола) 🎭", "module10.txt"),
    "11": ("🐱📚 Все 12 времен английского языка", "tenses.txt"),
}

THEORY_ALG_MODULES = {
    "1": ("🐾 Модуль 1: Основы C — Память, Указатели и Биты 🧠", "alg1.txt"),
    "2": ("🐾 Модуль 2: Эффективность алгоритмов — Время, Память и Стратегии ⚖️", "alg2.txt"),
    "3": ("🐾 Модуль 3: Обход графов — DFS и BFS 🌲", "alg3.txt"),
    "4": ("🐾 Модуль 4: Деревья в структурах — Binary Tree, BST, Heap 🌳", "alg4.txt"),
    "5": ("🐾 Модуль 5: Быстрая сортировка (Quick Sort) — Pivot 🎯", "alg5.txt"),
    "6": ("🐾 Модуль 6: Пирамидальная сортировка (Heap Sort) 🏰", "alg6.txt"),
    "7": ("🐾 Модуль 7: Оценка сложности алгоритмов — Big-O 📈", "alg7.txt"),
    "8": ("🐾 Модуль 8: Хэширование — Hash Table и коллизии 🗄️", "alg8.txt"),
    "9": ("🐾 Модуль 9: Сортировка подсчётом (Counting Sort) 🧮", "alg9.txt"),
    "10": ("🐾 Модуль 10: Фундаментальные свойства алгоритмов 🛠️", "alg10.txt"),
}


def get_main_menu_builder():
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Начать тест", callback_data="choose_topic")
    builder.button(text="🇬🇧 Теория: Английский", callback_data="menu_eng")
    builder.button(text="💻 Теория: Алгоритмы", callback_data="menu_alg")
    builder.button(text="🏆 ТОП лидеров", callback_data="show_top")
    builder.button(text="Мур-р-р 🐾", callback_data="love_cat")
    builder.adjust(1)
    return builder


def build_answers_keyboard(q_id, a, b, c, d, e, selected=""):
    builder = InlineKeyboardBuilder()
    options = [('A', a), ('B', b), ('C', c), ('D', d)]
    if e:
        options.append(('E', e))

    for char, opt_text in options:
        status = "✅ " if char in selected else ""
        passed_selected = selected if selected else "empty"
        builder.button(text=f"{status}{char}) {opt_text}", callback_data=f"multians_{q_id}_{char}_{passed_selected}")

    builder.adjust(1)
    if selected:
        builder.button(text="📥 Отправить ответ", callback_data=f"confirm_{q_id}_{selected}")
        builder.adjust(1)
    return builder.as_markup()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    check_and_register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        f"✨ Привет, котик {message.from_user.first_name}! 💖🐱\n\n"
        f"Добро пожаловать в бот подготовки к магистратуре **М094**!\n"
        f"Здесь ты можешь тренироваться на реальных тестах, сохранять прогресс и соревноваться с другими.",
        reply_markup=get_main_menu_builder().as_markup()
    )


@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_menu_builder().as_markup())
    await callback.answer()


@dp.callback_query(F.data == "love_cat")
async def love_cat_callback(callback: types.CallbackQuery):
    await callback.answer(
        "Мур-р-р! 🐱 Котик тебя очень любит, целует в носик и верит в твои силы! 💖✨",
        show_alert=True
    )


@dp.callback_query(F.data == "menu_eng")
async def theory_menu_eng(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for module_id, (title, _) in THEORY_ENG_MODULES.items():
        builder.button(text=title, callback_data=f"th_eng_{module_id}")
    builder.button(text="⬅️ Назад в меню", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text("🇬🇧 Выберите тему по Английскому языку:", reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "menu_alg")
async def theory_menu_alg(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for module_id, (title, _) in THEORY_ALG_MODULES.items():
        builder.button(text=title, callback_data=f"th_alg_{module_id}")
    builder.button(text="⬅️ Назад в меню", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text("💻 Выберите тему по Алгоритмам:", reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("th_eng_"))
async def show_theory_eng(callback: types.CallbackQuery):
    module_id = callback.data.replace("th_eng_", "")
    if module_id not in THEORY_ENG_MODULES:
        await callback.answer("❌ Модуль не найден")
        return

    title, filename = THEORY_ENG_MODULES[module_id]
    text = get_theory_eng(filename)

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ К темам английского", callback_data="menu_eng")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)

    try:
        await callback.message.edit_text(text[:4000], reply_markup=builder.as_markup())
    except Exception:
        await callback.message.answer(text[:4000], reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("th_alg_"))
async def show_theory_alg(callback: types.CallbackQuery):
    module_id = callback.data.replace("th_alg_", "")
    if module_id not in THEORY_ALG_MODULES:
        await callback.answer("❌ Модуль не найден")
        return

    title, filename = THEORY_ALG_MODULES[module_id]
    text = get_theory_alg(filename)

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ К темам алгоритмов", callback_data="menu_alg")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)

    try:
        await callback.message.edit_text(text[:4000], reply_markup=builder.as_markup())
    except Exception:
        await callback.message.answer(text[:4000], reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "choose_topic")
async def choose_topic(callback: types.CallbackQuery):
    check_and_register_user(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)

    topics = db_query("SELECT id, title FROM topics", fetchall=True)
    if not topics:
        await callback.answer("Пока нет тем. Сначала запусти init_db.py ✨", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for topic_id, title in topics:
        builder.button(text=title, callback_data=f"topic_{topic_id}")
    builder.button(text="⬅️ Назад", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text("Выбери предмет для подготовки:", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("topic_"))
async def start_quiz(callback: types.CallbackQuery):
    check_and_register_user(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)

    topic_id = int(callback.data.split("_")[1])

    question = db_query('''
        SELECT q.id, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e 
        FROM questions q LEFT JOIN user_progress up ON q.id = up.question_id AND up.user_id = ?
        WHERE q.topic_id = ? AND up.id IS NULL LIMIT 1
''', (callback.from_user.id, topic_id), fetchone=True)

    if not question:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ К темам", callback_data="choose_topic")
        builder.button(text="🏠 В главное меню", callback_data="main_menu")
        builder.adjust(1)
        await callback.message.edit_text("🎉 Ты ответила на все вопросы в этой теме! Скоро добавим новые.",
                                         reply_markup=builder.as_markup())
        return

    q_id, text, a, b, c, d, e = question
    keyboard = build_answers_keyboard(q_id, a, b, c, d, e, selected="")
    await callback.message.edit_text(f"❓ **Вопрос:**\n{text}", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("multians_"))
async def handle_multi_selection(callback: types.CallbackQuery):
    await callback.answer()
    _, q_id, char, selected = callback.data.split("_")

    if selected == "empty":
        selected = ""

    if char in selected:
        new_selected = selected.replace(char, "")
    else:
        new_selected = "".join(sorted(selected + char))

    question = db_query('''
        SELECT option_a, option_b, option_c, option_d, option_e 
        FROM questions WHERE id = ?
    ''', (q_id,), fetchone=True)

    if not question:
        return

    a, b, c, d, e = question
    keyboard = build_answers_keyboard(q_id, a, b, c, d, e, selected=new_selected)

    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise e


@dp.callback_query(F.data.startswith("confirm_"))
async def handle_confirm_answer(callback: types.CallbackQuery):
    _, q_id, user_answer = callback.data.split("_")

    q_info = db_query("SELECT correct_option, explanation, topic_id, question_text FROM questions WHERE id = ?",
                      (q_id,), fetchone=True)
    correct_option, explanation, topic_id, question_text = q_info

    user_answer_sorted = "".join(sorted(user_answer.upper().strip()))
    correct_option_sorted = "".join(sorted(correct_option.upper().strip()))

    is_correct = 1 if user_answer_sorted == correct_option_sorted else 0
    db_query("INSERT OR IGNORE INTO user_progress (user_id, question_id, is_correct) VALUES (?, ?, ?)",
             (callback.from_user.id, q_id, is_correct), commit=True)

    builder = InlineKeyboardBuilder()
    user_fmt = ", ".join(list(user_answer_sorted))
    correct_fmt = ", ".join(list(correct_option_sorted))

    if is_correct:
        db_query("UPDATE users SET score = score + 1 WHERE telegram_id = ?", (callback.from_user.id,), commit=True)
        result_text = f"✅ **Верно! Полное совпадение!** 💖\n\n❓ **Вопрос:**\n{question_text}\n\nТвой ответ: *{user_fmt}*"
        builder.button(text="➡️ Следующий", callback_data=f"topic_{topic_id}")
        builder.button(text="⬅️ Выйти к темам", callback_data="choose_topic")
    else:
        result_text = (
            f"❌ **Неверно.**\n\n"
            f"❓ **Вопрос:**\n{question_text}\n\n"
            f"Ты выбрала варианты: *{user_fmt}*\n"
            f"Правильные варианты: *{correct_fmt}*\n\n"
        )
        if explanation:
            result_text += f"💡 {explanation}\n\n"

        builder.button(text="🔄 Попробовать еще раз", callback_data=f"retry_{q_id}")
        builder.button(text="➡️ Пропустить вопрос", callback_data=f"topic_{topic_id}")
        builder.button(text="⬅️ Выйти к темам", callback_data="choose_topic")

    builder.adjust(1)
    await callback.message.edit_text(result_text, reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("retry_"))
async def retry_question(callback: types.CallbackQuery):
    q_id = int(callback.data.split("_")[1])

    db_query("DELETE FROM user_progress WHERE user_id = ? AND question_id = ?",
             (callback.from_user.id, q_id), commit=True)

    question = db_query('''
        SELECT id, question_text, option_a, option_b, option_c, option_d, option_e 
        FROM questions WHERE id = ?
    ''', (q_id,), fetchone=True)

    if not question:
        await callback.answer("Ошибка: вопрос не найден.", show_alert=True)
        return

    q_id, text, a, b, c, d, e = question
    keyboard = build_answers_keyboard(q_id, a, b, c, d, e, selected="")
    await callback.message.edit_text(f"❓ **Вопрос:**\n{text}", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "show_top")
async def show_top(callback: types.CallbackQuery):
    leaders = db_query("SELECT first_name, score FROM users ORDER BY score DESC LIMIT 10", fetchall=True)
    text = "🏆 **ТОП Лидеров:**\n\n"
    for i, (name, score) in enumerate(leaders):
        display_name = name if name else "Котик"
        text += f"{i + 1}. 👤 {display_name} — *{score}* очков\n"
    builder = InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="main_menu")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@dp.message(Command("admin_logs"))
async def show_all_users_logs(message: types.Message):
    YOUR_TELEGRAM_ID = 7720852426

    if message.from_user.id != YOUR_TELEGRAM_ID:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    all_users = db_query("SELECT telegram_id, first_name, username, score FROM users ORDER BY score DESC",
                         fetchall=True)

    if not all_users:
        await message.answer("📂 В базе данных пока нет ни одного пользователя.")
        return

    text = f"📋 **Полный список пользователей бота (Всего: {len(all_users)}):**\n\n"

    for i, (tg_id, name, username, score) in enumerate(all_users):
        user_link = f"@{username}" if username else "нет юзернейма"
        text += f"{i + 1}. 👤 {name} ({user_link}) \n   ID: `{tg_id}` | 🏆 Очки: *{score}*\n\n"

        if len(text) > 3500:
            await message.answer(text)
            text = ""

    if text:
        await message.answer(text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())