# import asyncio
# from aiogram import Bot, Dispatcher
# #from handlers import dp
# from config import TOKEN
# from database import init_db
#
# async def main():
#     init_db()  # Инициализация базы данных
#     bot = Bot(token=TOKEN)
#     dp['bot'] = bot  # Устанавливаем бота в диспетчер
#     await dp.start_polling(bot)
#
# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import dp  # Оставляем только диспетчер обработчиков

async def main():
    bot = Bot(token=TOKEN)
    dp['bot'] = bot  # Устанавливаем бота в диспетчер
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

