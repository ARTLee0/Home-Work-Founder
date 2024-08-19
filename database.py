import asyncio
import aiosqlite
import sqlite3

# Зададим имя базы данных
DB_NAME = 'quiz_bot.db'

''' async def create_table():
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем таблицу
        await db.execute(''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER)'')
        # Сохраняем изменения
        await db.commit()
'''

async def get_quiz_index(user_id):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


async def update_quiz_index(user_id, index):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)', (user_id, index))
        # Сохраняем изменения
        await db.commit()

# Функция для создания таблицы вопросов
async def create_table():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _create_table)

def _create_table():
    connection = sqlite3.connect('quiz_questions.db')
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY,
        question TEXT,
        options TEXT,
        correct_option INTEGER
    )
    """)

    connection.commit()
    cursor.close()
    connection.close()

# Функция для создания таблицы результатов
async def create_results_table():
    async with aiosqlite.connect('quiz_results.db') as connection:
        cursor = await connection.cursor()
        await cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            score INTEGER
        )
        """)
        await connection.commit()
        await cursor.close()
        pass



# Функция для сохранения результата
async def save_result(user_id, username, score):
    connection = sqlite3.connect('quiz_results.db')
    cursor = connection.cursor()

    # Вставка или замена результата
    cursor.execute("""
    INSERT OR REPLACE INTO results (user_id, username, score)
    VALUES (?, ?, ?)
    """, (user_id, username, score))

    connection.commit()
    cursor.close()
    connection.close()

# Функция для получения результата пользователя
async def get_user_result(user_id):
    connection = sqlite3.connect('quiz_results.db')
    cursor = connection.cursor()

    cursor.execute("SELECT username, score FROM results WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    if result:
        return {
            'username': result[0],
            'score': result[1]
        }
    return None