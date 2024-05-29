from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_admin = ReplyKeyboardMarkup(resize_keyboard=True)
main_admin.add(KeyboardButton("Каталог"))
main_admin.add(KeyboardButton("Корзина"))
main_admin.add(KeyboardButton("Контакты"))
main_admin.add(KeyboardButton("Сотрудники"))
main_admin.add(KeyboardButton("Админ-панель"))
main_admin.add(KeyboardButton("Назад"))

main = ReplyKeyboardMarkup(resize_keyboard=True)
main.add(KeyboardButton("Каталог"))
main.add(KeyboardButton("Корзина"))
main.add(KeyboardButton("Контакты"))
main.add(KeyboardButton("Сотрудники"))
main.add(KeyboardButton("Назад"))

admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)
admin_panel.add(KeyboardButton("Добавить товар"))
admin_panel.add(KeyboardButton("Удалить товар"))
admin_panel.add(KeyboardButton("Назад"))

catalog_list = InlineKeyboardMarkup(row_width=2)
catalog_list.add(InlineKeyboardButton("Видеокарты", callback_data="videocards"))
catalog_list.add(InlineKeyboardButton("Процессоры", callback_data="processors"))
catalog_list.add(InlineKeyboardButton("Материнские платы", callback_data="motherboards"))

clear_cart = InlineKeyboardMarkup(row_width=2)
clear_cart.add(InlineKeyboardButton("Очистить корзину", callback_data="clear_all_cart"))
clear_cart.add(InlineKeyboardButton("Удалить товар", callback_data="select_items_to_delete"))
