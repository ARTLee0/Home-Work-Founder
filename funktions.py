from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F

from database import create_table, get_quiz_index, get_user_result, update_quiz_index, save_result, create_results_table
from quiz_question import quiz_data

# Запишем токен нашего бота, который мы получили от BotFather
API_TOKEN = '7422574631:AAG3jM3PGhoVy4Ru7WHXOr9XoQrJrn8qu_U'

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()

user_answers = []  # Глобальный список для хранения ответов

def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()

@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    global user_answers
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_answer = quiz_data[current_question_index]['options'][quiz_data[current_question_index]['correct_option']]
    
    user_answers.append(correct_answer)  # Сохраняем правильный ответ
    await callback.message.answer(f"Верно! Ответ: {correct_answer}")
    
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        await callback.message.answer("Ваши ответы: " + ", ".join(user_answers))
        
        score = user_answers.count("Ошибочный ответ")  # Количество правильных ответов
        await save_result(callback.from_user.id, callback.from_user.username, score)

@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    global user_answers
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_answer = quiz_data[current_question_index]['options'][quiz_data[current_question_index]['correct_option']]
    
    user_answers.append("Ошибочный ответ")  # Сохраняем "Ошибочный ответ" для неверного ответа
    await callback.message.answer(f"Неправильно! Правильный ответ: {correct_answer}")

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        await callback.message.answer("Ваши ответы: " + ", ".join(user_answers))
        
        score = user_answers.count("Ошибочный ответ")  # Количество правильных ответов
        await save_result(callback.from_user.id, callback.from_user.username, score)

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика"))  # Кнопка для статистики
    builder.add(types.KeyboardButton(text="Список команд"))  # Кнопка для статистики
    await message.answer("Добро пожаловать в квиз! Готовы начать? (/help для получения списка команд).", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команду /quiz
@dp.message(Command("quiz"))
@dp.message(F.text == "Начать игру")
async def start_quiz(message: types.Message):
    print("Команда 'Начать игру' получена")  # Отладочное сообщение
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)
    print(f"Текущий индекс вопроса: {current_question_index}")  # Отладочное сообщение

    if current_question_index < len(quiz_data):
        correct_index = quiz_data[current_question_index]['correct_option']
        opts = quiz_data[current_question_index]['options']
        kb = generate_options_keyboard(opts, opts[correct_index])
        await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)
    else:
        await message.answer("Квиз завершен! Спасибо за участие.")

async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)  # Получение текущего индекса вопроса
    print(f"Текущий индекс вопроса: {current_question_index}")  # Отладочное сообщение

    if current_question_index < len(quiz_data):  # Проверка, что индекс не выходит за пределы
        correct_index = quiz_data[current_question_index]['correct_option']
        opts = quiz_data[current_question_index]['options']
        kb = generate_options_keyboard(opts, opts[correct_index])
        await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)
    else:
        await message.answer("Квиз завершен! Спасибо за участие.")

async def new_quiz(message):
    global user_answers
    user_answers = []  # Сброс ответов при новом квизе
    user_id = message.from_user.id
    current_question_index = 0
    await update_quiz_index(user_id, current_question_index)  # Убедитесь, что эта функция работает
    await get_question(message, user_id)

# Хэндлер на команду /stats
@dp.message(F.text=="Статистика")
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    result = await get_user_result(user_id)  # Получите результат пользователя из базы данных

    if result:
        await message.answer(f"Ваши результаты:\nНеправильных ответов: {result['score']}")
    else:
        await message.answer("У вас еще нет результатов.")


# Функция для обработки команды /help
@dp.message(Command("help"))
@dp.message(F.text == "Список команд")
async def help_command(message: types.Message):
    help_text = (
        "Доступные команды:\n"
        "/start - Запустить бота\n"
        "/help - Получить список команд\n"
        "/quiz - Начать квиз (Игра - Викторина, Вопрос/ответ)\n"
        "/stats - Показать статистику прохождений\n"
    )
    await message.answer(help_text)

# Запуск процесса поллинга новых апдейтов
async def main():
    await create_table()  # Создание таблицы для вопросов
    await create_results_table()  # Создание таблицы для результатов

    # Запускаем поллинг
    await dp.start_polling(bot)

    