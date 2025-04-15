import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from database import record_poll_vote, record_vote, create_poll, get_subscribers, add_subscriber
from keyboards import create_keyboard

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 🎯 Определяем состояния FSM для создания опросов и голосований
# class PollCreation(StatesGroup):
#     waiting_for_question = State()
#     waiting_for_options = State()
#     waiting_for_confirmation = State()
#
# class VoteCreation(StatesGroup):
#     waiting_for_question = State()
#     waiting_for_options = State()
#     waiting_for_confirmation = State()

# 📌 Главное меню с кнопками
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start"), KeyboardButton(text="/restart")]
    ],
    resize_keyboard=True
)

# 📌 Кнопка "Подтвердить" (InlineKeyboard)
confirm_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_poll_or_vote")]
    ]
)

# 📌 Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Здравствуйте, я - бот для рассылки сголосований и опросов!\n\n"
        "В этот диалог с некоторой периодичностью будут приходить тематические опросы и голосования на различные темы.\n\n"
        "Спасибо, что подписались на рассылку:)))\n",
        reply_markup=main_menu  # Показываем меню с кнопками
    )

async def send_poll_to_subscribers(question, keyboard):
    subscribers = get_subscribers()
    for user_id in subscribers:
        try:
            await bot.send_message(user_id, f"📊 *Новый опрос:*\n\n{question}",
                                   reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки пользователю {user_id}: {e}")

@dp.message(Command("subscribe"))
async def subscribe_user(message: types.Message):
    add_subscriber(message.chat.id)
    await message.answer("✅ Вы подписались на рассылку новых опросов и голосований!")

# 📌 Команда /create_poll (начало создания опроса)
# @dp.message(Command("create_poll"))
# async def create_poll_start(message: types.Message, state: FSMContext):
#     await message.answer("Введите вопрос для опроса:")
#     await state.set_state(PollCreation.waiting_for_question)
#
# # 📌 Обрабатываем ввод вопроса для опроса
# @dp.message(PollCreation.waiting_for_question)
# async def poll_question_handler(message: types.Message, state: FSMContext):
#     await state.update_data(question=message.text)
#     await message.answer("Теперь введите варианты ответов (в одном сообщении, каждый с новой строки):")
#     await state.set_state(PollCreation.waiting_for_options)

# 📌 Обрабатываем ввод вариантов ответа для опроса
# @dp.message(PollCreation.waiting_for_options)
# async def poll_options_handler(message: types.Message, state: FSMContext):
#     print("➡ poll_options_handler вызван!")  # Должно появиться в консоли
#
#     options = message.text.strip().split("\n")  # Разделяем строки на список вариантов
#
#     if len(options) < 2:
#         await message.answer("❗ Минимум 2 варианта ответа! Введите их одним сообщением, каждый с новой строки.")
#         return
#
#     user_data = await state.get_data()
#     question = user_data["question"]
#
#     print(f"✅ Вопрос для опроса: {question}")
#     print(f"✅ Варианты ответа: {options}")
#
#     poll_id = create_poll(question, options)
#
#     if not poll_id:
#         print("❌ Ошибка записи опроса в БД!")
#         await message.answer("⚠️ Не удалось создать опрос.")
#         return
#
#     print(f"✅ Опрос записан в БД: ID={poll_id}")
#
#     # ✅ Генерируем клавиатуру
#     keyboard = create_keyboard(options, poll_id, prefix="poll")
#
#     if keyboard is None:  # Если клавиатура не создалась
#         await message.answer("❌ Ошибка: Не удалось создать клавиатуру для опроса")
#         return
#
#     # ✅ Отправляем сообщение с опросом в личный чат создателя бота
#     bot_owner_chat_id = message.chat.id  # ID чата, где была запущена команда
#     await bot.send_message(bot_owner_chat_id, "📊 Опрос успешно создан!")
#     await bot.send_message(bot_owner_chat_id, f"📊 *Опрос:*\n\n{question}", reply_markup=keyboard, parse_mode="Markdown")
#     # Рассылаем подписчикам
#     await send_poll_to_subscribers(question, keyboard)
#     await state.clear()  # Завершаем FSM

# 📌 Команда /create_vote (начало создания голосования)
# @dp.message(Command("create_vote"))
# async def create_vote_start(message: types.Message, state: FSMContext):
#     await message.answer("Введите вопрос для голосования:")
#     await state.set_state(VoteCreation.waiting_for_question)
#
# # 📌 Обрабатываем ввод вопроса для голосования
# @dp.message(VoteCreation.waiting_for_question)
# async def vote_question_handler(message: types.Message, state: FSMContext):
#     await state.update_data(question=message.text)
#     await message.answer("Теперь введите варианты ответов (в одном сообщении, каждый с новой строки):")
#     await state.set_state(VoteCreation.waiting_for_options)
#
# # 📌 Обрабатываем ввод вариантов ответа для голосования
# @dp.message(VoteCreation.waiting_for_options)
# async def vote_options_handler(message: types.Message, state: FSMContext):
#     options = message.text.strip().split("\n")  # Разделяем строки на список вариантов
#
#     if len(options) < 2:
#         await message.answer("❗ Минимум 2 варианта ответа! Введите их одним сообщением, каждый с новой строки.")
#         return
#
#     user_data = await state.get_data()
#     question = user_data["question"]
#
#     # ✅ Генерируем клавиатуру
#     keyboard = create_keyboard(options, question, is_vote=True)
#
#     # ✅ Отправляем сообщение с голосованием в личный чат создателя бота
#     bot_owner_chat_id = message.chat.id  # ID чата, где была запущена команда
#     await bot.send_message(bot_owner_chat_id, "✅ Голосование успешно создано!")
#     await bot.send_message(bot_owner_chat_id, f"✅ *Голосование:*\n\n{question}", reply_markup=keyboard, parse_mode="Markdown")
#
#     await state.clear()  # Завершаем FSM


@dp.callback_query(lambda c: c.data.startswith("poll_"))
async def handle_poll_vote(callback: types.CallbackQuery):
    data = callback.data.split("_")  # Разбираем callback_data: poll_{poll_id}_{choice}

    if len(data) < 3:
        await callback.answer("❌ Ошибка обработки голоса!")
        return

    poll_id = int(data[1])  # ID опроса
    choice = data[2]  # Выбранный вариант ответа
    user_id = callback.from_user.id  # ID пользователя

    # Записываем голос в базу
    success = record_poll_vote(poll_id, user_id, choice)

    if success:
        await callback.answer("✅ Ваш голос учтён!")
    else:
        await callback.answer("❗ Вы уже голосовали в этом опросе!")

@dp.callback_query(lambda c: c.data.startswith("vote_"))
async def handle_vote(callback: CallbackQuery):
    _, vote_id, choice = callback.data.split("_", 2)
    success = record_vote(int(vote_id), callback.from_user.id, choice)
    if success:
        await callback.answer("✅ Ваш голос учтён!")
    else:
        await callback.answer("❗ Вы уже голосовали.")



