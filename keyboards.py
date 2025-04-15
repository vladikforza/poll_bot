from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_keyboard(options, poll_id, prefix="poll"):
    buttons = []

    for option in options:
        option_text = option.strip()
        if option_text:
            callback_data = f"{prefix}_{poll_id}_{option_text[:50]}"
            button = InlineKeyboardButton(text=option_text, callback_data=callback_data)
            buttons.append([button])

    if not buttons:
        print("❌ Ошибка: Пустой список кнопок!")
        return None

    return InlineKeyboardMarkup(inline_keyboard=buttons)




# def create_keyboard(options, item_id, prefix):
#     if not options:  # Проверяем, есть ли варианты
#         print("❌ Ошибка: Пустой список вариантов для клавиатуры")
#         return None  # Возвращаем `None`, если нет вариантов
#
#     buttons = [
#         [InlineKeyboardButton(text=option, callback_data=f"{prefix}_{item_id}_{option}")]
#         for option in options
#     ]
#
#     return InlineKeyboardMarkup(inline_keyboard=buttons)
