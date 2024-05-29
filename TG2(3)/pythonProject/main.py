import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from app import keyboard as kb
from app.database import db_start, create_item, get_items_by_category, get_item_by_id, delete_item, add_item_to_cart, get_cart_items, delete_item_from_cart, clear_cart
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
load_dotenv()
bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot=bot, storage=storage)

GROUP_ID = int(os.getenv('GROUP_ID'))

# Словарь для хранения последнего сообщения бота для каждого пользователя
last_bot_message = {}

async def on_startup(_):
    await db_start()
    print("Бот запущен")

class NewOrder(StatesGroup):
    type = State()
    name = State()
    desc = State()
    price = State()
    photo = State()
    delete = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await db_start()
    bot_message = await message.answer_sticker('CAACAgIAAxkBAAM9Ziuu23M1fh9_bjwPhDM65R298JwAAtMRAAJU4YBK542cbGDIzuA0BA')
    last_bot_message[message.from_user.id] = bot_message.message_id
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        bot_message = await message.answer(f'{message.from_user.full_name}, добро пожаловать в магазин компьютерных комплектующих!',
                                           reply_markup=kb.main_admin)
    else:
        bot_message = await message.answer(f'{message.from_user.full_name}, добро пожаловать в магазин компьютерных комплектующих!',
                                           reply_markup=kb.main)
    last_bot_message[message.from_user.id] = bot_message.message_id

async def main_menu(message: types.Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        bot_message = await message.answer(
            f'{message.from_user.full_name}, добро пожаловать в магазин компьютерных комплектующих!',
            reply_markup=kb.main_admin
        )
    else:
        bot_message = await message.answer(
            f'{message.from_user.full_name}, добро пожаловать в магазин компьютерных комплектующих!',
            reply_markup=kb.main
        )
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.message_handler(lambda message: message.text == 'Назад', state='*')
async def cancel_process(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if (current_state is not None):
        await state.finish()
    await main_menu(message)

@dp.message_handler(commands=['id'])
async def cmd_id(message: types.Message):
    await message.answer(f'{message.from_user.id}')

@dp.message_handler(text="Контакты")
async def contacts(message: types.Message):
    bot_message = await message.answer(f"техподдержка @NowiyEnot")
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.message_handler(text="Корзина")
async def corzina(message: types.Message):
    await send_cart(message.from_user.id, message)

async def send_cart(user_id, original_message):
    items = await get_cart_items(user_id)
    total_price = sum(
        float(item[0].price.replace('₽', '').replace('\xa0', '').replace(' ', '').replace(',', '.')) * item[1] for item in items)
    cart_items_text = "\n".join([f"{item[0].name} - {item[0].price} x {item[1]}" for item in items])
    bot_message = await original_message.answer(f"Товары в корзине:\n{cart_items_text}\n\nОбщая стоимость: {total_price} ₽",
                         reply_markup=kb.clear_cart)
    last_bot_message[user_id] = bot_message.message_id

@dp.message_handler(text="Каталог")
async def catalog(message: types.Message):
    bot_message = await message.answer("Выберите категорию товаров:", reply_markup=kb.catalog_list)
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.message_handler(text="Сотрудники")
async def sotrudniki(message: types.Message):
    bot_message = await message.answer(f"Сотрудников нет")
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.message_handler(text="Админ-панель")
async def admin_panel(message: types.Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        bot_message = await message.answer(f"Вы вошли в админ-панель", reply_markup=kb.admin_panel)
    else:
        bot_message = await message.answer(f"Я тебя не понимаю.")
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.message_handler(text="Удалить товар")
async def delete_item_prompt(message: types.Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        bot_message = await message.answer('Введите название товара, который вы хотите удалить:')
        last_bot_message[message.from_user.id] = bot_message.message_id
        await NewOrder.delete.set()
    else:
        await message.reply('У вас нет прав для удаления товара.')
@dp.message_handler(state=NewOrder.delete)
async def delete_item_confirm(message: types.Message, state: FSMContext):
    item_name = message.text
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        bot_message = await message.answer(f'Попытка удалить товар "{item_name}"...')
        last_bot_message[message.from_user.id] = bot_message.message_id
        deleted = await delete_item(item_name)
        if deleted:
            bot_message = await message.answer(f'Товар "{item_name}" успешно удалён.')
        else:
            bot_message = await message.answer(f'Товар "{item_name}" не найден.')
    else:
        await message.reply('У вас нет прав для удаления товара.')
    await state.finish()
    await main_menu(message)
@dp.message_handler(text='Добавить товар')
async def add_item(message: types.Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await NewOrder.type.set()
        bot_message = await message.answer('Выберите тип товара', reply_markup=kb.catalog_list)
        last_bot_message[message.from_user.id] = bot_message.message_id
    else:
        await message.reply('У вас нет прав для выполнения этой команды.')

@dp.message_handler(lambda message: message.text == 'Отмена', state=NewOrder)
async def cancel_add_item(message: types.Message, state: FSMContext):
    await state.finish()
    bot_message = await message.answer('Добавление товара отменено.', reply_markup=kb.admin_panel)
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.callback_query_handler(lambda c: c.data in ["videocards", "processors", "motherboards"], state=NewOrder.type)
async def process_type(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['type'] = callback_query.data
    await NewOrder.next()
    bot_message = await bot.send_message(callback_query.from_user.id, 'Введите название товара:')
    last_bot_message[callback_query.from_user.id] = bot_message.message_id
    await bot.answer_callback_query(callback_query.id)

@dp.message_handler(state=NewOrder.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await NewOrder.next()
    bot_message = await message.answer('Введите описание товара:')
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.message_handler(state=NewOrder.desc)
async def process_desc(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['desc'] = message.text
    await NewOrder.next()
    bot_message = await message.answer('Введите цену товара:')
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.message_handler(state=NewOrder.price)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text
    await NewOrder.next()
    bot_message = await message.answer('Загрузите фотографию товара:')
    last_bot_message[message.from_user.id] = bot_message.message_id

@dp.message_handler(content_types=['photo'], state=NewOrder.photo)
async def process_photo(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['photo'] = message.photo[-1].file_id
            logging.info(f"Данные для создания товара: {data}")

            
            await create_item(data['name'], data['desc'], data['price'], data['photo'], data['type'])

        # После обработки фото завершаем состояние FSM
        await state.finish()

        # Отправляем подтверждение пользователю
        bot_message = await message.answer('Товар успешно добавлен!')

        # Возвращаемся в основное меню
        await main_menu(message)
    except Exception as e:
        logging.error(f"Ошибка при добавлении товара: {e}")
        await message.answer("Произошла ошибка при добавлении товара. Пожалуйста, попробуйте снова.")

@dp.callback_query_handler(text_contains="videocards")
async def show_videocards(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    items = await get_items_by_category("videocards")
    await show_item_list(callback_query, items)

@dp.callback_query_handler(text_contains="processors")
async def show_processors(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    items = await get_items_by_category("processors")
    await show_item_list(callback_query, items)

@dp.callback_query_handler(text_contains="motherboards")
async def show_motherboards(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    items = await get_items_by_category("motherboards")
    await show_item_list(callback_query, items)

async def show_item_list(callback_query, items):
    keyboard = types.InlineKeyboardMarkup()
    for item in items:
        keyboard.add(types.InlineKeyboardButton(text=item.name, callback_data=f"item:{item.id}"))
    bot_message = await bot.send_message(callback_query.from_user.id, "Выберите товар из списка:", reply_markup=keyboard)
    last_bot_message[callback_query.from_user.id] = bot_message.message_id

@dp.callback_query_handler(lambda c: c.data.startswith('item:'))
async def show_item_details(callback_query: types.CallbackQuery):
    item_id = callback_query.data.split(':')[1]
    item = await get_item_by_id(item_id)
    bot_message = await bot.send_photo(callback_query.from_user.id, item.photo, caption=f"{item.name}\n{item.desc}\nЦена: {item.price}",
                                        reply_markup=types.InlineKeyboardMarkup().add(
                                            types.InlineKeyboardButton("Добавить в корзину", callback_data=f"add_to_cart:{item.id}")
                                        ))
    last_bot_message[callback_query.from_user.id] = bot_message.message_id

@dp.callback_query_handler(lambda c: c.data.startswith('add_to_cart:'))
async def add_to_cart(callback_query: types.CallbackQuery):
    item_id = callback_query.data.split(':')[1]
    await add_item_to_cart(callback_query.from_user.id, item_id)
    bot_message = await bot.answer_callback_query(callback_query.id, "Товар добавлен в корзину!")
    last_bot_message[callback_query.from_user.id] = bot_message.message_id

@dp.message_handler(lambda message: message.text.lower() == "оплатил")
async def handle_paid_message(message: types.Message):
    if message.from_user.id in last_bot_message:
        # Пересылаем последнее сообщение бота в группу
        await bot.forward_message(GROUP_ID, message.from_user.id, last_bot_message[message.from_user.id])
    # Пересылаем сообщение пользователя в группу
    await bot.forward_message(GROUP_ID, message.from_user.id, message.message_id)
    # Отправляем сообщение пользователю и возвращаем его в главное меню
    await message.answer("Оплата прошла!")
    await main_menu(message)

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
