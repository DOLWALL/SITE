import asyncio
import logging
import os
import io
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile

# --- 1. НАСТРОЙКИ СИСТЕМЫ И БЕЗОПАСНОСТИ ---
# ВПИШИ СЮДА ТОКЕН БОТА-ГЕНЕРАТОРА
GENERATOR_TOKEN = "8577015225:AAFbVE3hZ23HZI50gWk7vdgqi5rKHcJ4A"
AUTHORIZED_ADMIN_ID = 7316276135

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=GENERATOR_TOKEN)
dp = Dispatcher()

# --- 2. МАШИНА СОСТОЯНИЙ (FSM) ---
class BotConfigurator(StatesGroup):
    waiting_for_token = State()
    waiting_for_admin_id = State()
    waiting_for_company_name = State()
    waiting_for_context = State()
    waiting_for_product_type = State()

# --- 3. ШАБЛОН ЯДРА (АБСОЛЮТНО ПОЛНЫЙ КОД БЕЗ УРЕЗАНИЙ) ---
def get_bot_template(token, admin_id, company_name, context_msg, product_type):
    # Используем f-строки и экранирование скобок для внедрения переменных
    template = f'''import sys
import subprocess
import os

# --- 1. АВТОМАТИЧЕСКАЯ УСТАНОВКА ЗАВИСИМОСТЕЙ ---
def install_requirements():
    reqs = ["pyTelegramBotAPI", "schedule", "Pillow"]
    for req in reqs:
        try:
            __import__(req.lower() if req != 'Pillow' else 'PIL')
        except ImportError:
            print(f"Устанавливаю {{req}}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])

install_requirements()

import telebot
from telebot import types
import sqlite3
import schedule
import threading
import time
import logging
import shutil
from PIL import Image, ImageDraw

# --- 2. НАСТРОЙКИ И КОНСТАНТЫ ---
TOKEN = "{token}"
DEV_ID = {admin_id}
ADMIN_ID = {admin_id}

bot = telebot.TeleBot(TOKEN)

# Настройка логирования
logging.basicConfig(
    filename='bot.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

# Папки
if not os.path.exists('photos'):
    os.makedirs('photos')

# Создание dummy-картинок, если их нет
def create_dummy_image(filename, text):
    if not os.path.exists(filename):
        img = Image.new('RGB', (400, 200), color=(255, 182, 193))
        d = ImageDraw.Draw(img)
        d.text((150, 90), text, fill=(0, 0, 0))
        img.save(filename)

create_dummy_image('hello.png', '{company_name} Welcome!')
create_dummy_image('Ahello.png', 'Admin Panel {company_name}')

# --- 3. БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(\'\'\'CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price TEXT, photo TEXT)\'\'\')
    c.execute(\'\'\'CREATE TABLE IF NOT EXISTS cart
                 (user_id INTEGER, product_id INTEGER, quantity INTEGER)\'\'\')
    c.execute(\'\'\'CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, phone TEXT, details TEXT, status TEXT)\'\'\')
    conn.commit()
    conn.close()

init_db()

def db_query(query, params=(), fetch=False):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        res = c.fetchall()
    else:
        conn.commit()
        res = None
    conn.close()
    return res

# --- 4. ЕЖЕДНЕВНЫЙ БЭКАП РАЗРАБОТЧИКУ ---
def send_backup():
    try:
        backup_dir = 'backup_temp'
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        os.makedirs(backup_dir)
        
        # Копируем файлы
        if os.path.exists('bot.db'): shutil.copy('bot.db', backup_dir)
        if os.path.exists('bot.log'): shutil.copy('bot.log', backup_dir)
        if os.path.exists('photos'): shutil.copytree('photos', os.path.join(backup_dir, 'photos'))
        
        # Архивируем
        shutil.make_archive('{company_name}_Backup', 'zip', backup_dir)
        
        # Отправляем
        with open('{company_name}_Backup.zip', 'rb') as f:
            bot.send_document(DEV_ID, f, caption="📦 Ежедневный бэкап (БД, Логи, Фото)")
        
        # Убираем за собой
        shutil.rmtree(backup_dir)
        os.remove('{company_name}_Backup.zip')
        
        # Очищаем лог, чтобы не рос бесконечно
        open('bot.log', 'w').close()
    except Exception as e:
        bot.send_message(DEV_ID, f"Ошибка при создании бэкапа: {{e}}")

def schedule_checker():
    schedule.every().day.at("00:00").do(send_backup)
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=schedule_checker, daemon=True).start()

# --- 5. СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ И ЧАТА ---
user_states = {{}} # {{user_id: state}}
chat_sessions = {{}} # {{client_id: admin_id}} - кто с кем общается

# --- 6. КЛАВИАТУРЫ ---
def get_user_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🛒 Корзина"), types.KeyboardButton("✉️ Сообщение менеджеру"))
    return markup

def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📋 СПИСОК ЗАКАЗОВ"))
    markup.add(types.KeyboardButton("➕ Добавить {product_type}"), types.KeyboardButton("🔙 Назад"))
    return markup

def get_chat_exit_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Назад"))
    return markup

def get_carousel_keyboard(products, index):
    markup = types.InlineKeyboardMarkup()
    if not products:
        return markup
    
    prod_id = products[index][0]
    
    # Кнопки навигации
    nav_buttons = []
    if index > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅️ Пред", callback_data=f"page_{{index-1}}"))
    if index < len(products) - 1:
        nav_buttons.append(types.InlineKeyboardButton("След ➡️", callback_data=f"page_{{index+1}}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
        
    markup.row(types.InlineKeyboardButton("💳 Заказать сразу", callback_data=f"buy_{{prod_id}}"))
    markup.row(types.InlineKeyboardButton("📥 В корзину", callback_data=f"cart_{{prod_id}}"))
    return markup

# --- 7. ОБРАБОТЧИКИ СООБЩЕНИЙ ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.chat.id
    
    # Состояние общения сбрасываем при старте
    if uid in user_states: del user_states[uid]
    
    if uid == DEV_ID:
        bot.send_message(uid, "Привет, Владелец/Разработчик! Бэкапы будут приходить сюда каждый день в 00:00. Можешь также пользоваться ботом как клиент.", reply_markup=get_user_keyboard())
    
    if uid == ADMIN_ID:
        with open('Ahello.png', 'rb') as photo:
            bot.send_photo(uid, photo, caption="Приветствую! Панель управления {company_name} активирована.", reply_markup=get_admin_keyboard())
    else:
        # Обычный пользователь
        with open('hello.png', 'rb') as photo:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 Начать сборку заказа", callback_data="start_order"))
            bot.send_photo(uid, photo, caption="{context_msg}", reply_markup=markup)
            bot.send_message(uid, "Используйте меню ниже для навигации:", reply_markup=get_user_keyboard())

# === КААРУСЕЛЬ И КНОПКИ INLINE ===
@bot.callback_query_handler(func=lambda call: call.data.startswith('start_order') or call.data.startswith('page_'))
def handle_carousel(call):
    products = db_query("SELECT id, name, price, photo FROM products", fetch=True)
    
    if not products:
        bot.answer_callback_query(call.id, "Товаров пока нет :(", show_alert=True)
        return

    index = 0
    if call.data.startswith('page_'):
        index = int(call.data.split('_')[1])
        
    product = products[index]
    caption = f"<b>{{product[1]}}</b>\\nЦена: {{product[2]}}"
    markup = get_carousel_keyboard(products, index)

    if call.data == 'start_order':
        with open(product[3], 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo, caption=caption, parse_mode='HTML', reply_markup=markup)
    else:
        with open(product[3], 'rb') as photo:
            media = types.InputMediaPhoto(photo, caption=caption, parse_mode='HTML')
            bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id, media=media, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cart_'))
def add_to_cart(call):
    prod_id = int(call.data.split('_')[1])
    uid = call.message.chat.id
    
    # Проверяем, есть ли уже товар
    exists = db_query("SELECT quantity FROM cart WHERE user_id=? AND product_id=?", (uid, prod_id), fetch=True)
    if exists:
        db_query("UPDATE cart SET quantity=quantity+1 WHERE user_id=? AND product_id=?", (uid, prod_id))
    else:
        db_query("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)", (uid, prod_id))
        
    bot.answer_callback_query(call.id, "✅ Добавлено в корзину!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_now(call):
    prod_id = int(call.data.split('_')[1])
    uid = call.message.chat.id
    
    db_query("DELETE FROM cart WHERE user_id=?", (uid,))
    db_query("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)", (uid, prod_id))
    
    checkout_process(uid, call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
def del_from_cart(call):
    prod_id = int(call.data.split('_')[1])
    uid = call.message.chat.id
    db_query("DELETE FROM cart WHERE user_id=? AND product_id=?", (uid, prod_id))
    bot.answer_callback_query(call.id, "Удалено из корзины")
    show_cart(call.message)

@bot.callback_query_handler(func=lambda call: call.data == 'checkout_all')
def checkout_all(call):
    checkout_process(call.message.chat.id, call.message)

def checkout_process(uid, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📱 Отправить номер", request_contact=True)
    markup.add(btn, types.KeyboardButton("🔙 Назад"))
    bot.send_message(uid, "Пожалуйста, поделитесь своим номером телефона для оформления заказа (кнопка ниже):", reply_markup=markup)
    user_states[uid] = 'WAITING_PHONE'

# === КОРЗИНА ===
@bot.message_handler(func=lambda m: m.text == "🛒 Корзина")
def show_cart(message):
    uid = message.chat.id
    items = db_query(\'\'\'SELECT p.id, p.name, p.price, c.quantity 
                        FROM cart c JOIN products p ON c.product_id = p.id 
                        WHERE c.user_id=?\'\'\', (uid,), fetch=True)
    
    if not items:
        bot.send_message(uid, "Ваша корзина пуста 😔")
        return
        
    text = "<b>Ваша корзина:</b>\\n\\n"
    markup = types.InlineKeyboardMarkup()
    
    for item in items:
        text += f"▪️ {{item[1]}} x {{item[3]}} шт. - {{item[2]}}\\n"
        markup.add(types.InlineKeyboardButton(f"❌ Удалить {{item[1]}}", callback_data=f"del_{{item[0]}}"))
        
    markup.add(types.InlineKeyboardButton("✅ Оформить всё", callback_data="checkout_all"))
    bot.send_message(uid, text, parse_mode='HTML', reply_markup=markup)

# === ТЕКСТОВЫЕ КНОПКИ И ОБРАБОТКА КОНТАКТОВ ===
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    uid = message.chat.id
    if user_states.get(uid) == 'WAITING_PHONE':
        phone = message.contact.phone_number
        username = message.from_user.username or "Без юзернейма"
        
        items = db_query(\'\'\'SELECT p.name, p.price, c.quantity 
                            FROM cart c JOIN products p ON c.product_id = p.id 
                            WHERE c.user_id=?\'\'\', (uid,), fetch=True)
        
        details = "\\n".join([f"{{i[0]}} x {{i[2]}} шт. ({{i[1]}})" for i in items])
        
        db_query("INSERT INTO orders (user_id, username, phone, details, status) VALUES (?, ?, ?, ?, ?)",
                 (uid, username, phone, details, "Новый"))
        
        db_query("DELETE FROM cart WHERE user_id=?", (uid,))
        user_states.pop(uid, None)
        
        bot.send_message(uid, "🎉 Спасибо! Ваш заказ успешно оформлен. Менеджер скоро с вами свяжется.", reply_markup=get_user_keyboard())
        bot.send_message(ADMIN_ID, f"🔔 <b>НОВЫЙ ЗАКАЗ!</b>\\n\\nКлиент: @{{username}}\\nТелефон: {{phone}}\\n\\n<b>Заказ:</b>\\n{{details}}", parse_mode='HTML')
        logging.info(f"New Order: User={{username}}, Phone={{phone}}, Items={{details}}")

@bot.message_handler(func=lambda m: m.text == "📋 СПИСОК ЗАКАЗОВ")
def admin_orders(message):
    if message.chat.id != ADMIN_ID: return
    
    orders = db_query("SELECT id, username, phone, details FROM orders WHERE status='Новый'", fetch=True)
    if not orders:
        bot.send_message(ADMIN_ID, "Новых заказов пока нет.")
        return
        
    for o in orders:
        text = f"📦 <b>Заказ #{{o[0]}}</b>\\nКлиент: @{{o[1]}}\\nТелефон: {{o[2]}}\\n\\n<b>Состав:</b>\\n{{o[3]}}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Ответить клиенту", callback_data=f"reply_{{o[2]}}_{{o[1]}}"))
        bot.send_message(ADMIN_ID, text, parse_mode='HTML')

# === ЧАТ С МЕНЕДЖЕРОМ ===
@bot.message_handler(func=lambda m: m.text == "✉️ Сообщение менеджеру")
def chat_with_baker(message):
    uid = message.chat.id
    user_states[uid] = 'CHATTING_WITH_ADMIN'
    bot.send_message(uid, "Вы вошли в режим диалога с менеджером. Напишите свой вопрос или пожелание! 👇\\n\\n(Чтобы выйти, нажмите 'Назад')", reply_markup=get_chat_exit_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def admin_reply_callback(call):
    pass

@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def go_back(message):
    uid = message.chat.id
    if uid in user_states:
        state = user_states[uid]
        if state == 'CHATTING_WITH_ADMIN':
            bot.send_message(ADMIN_ID, f"🔴 Клиент @{{message.from_user.username or message.from_user.first_name}} покинул чат.")
        elif state.startswith('CHATTING_WITH_USER_'):
            user_to_notify = state.split('_')[3]
            bot.send_message(user_to_notify, "🔴 Менеджер завершил диалог.")
            
        del user_states[uid]
        
    keyboard = get_admin_keyboard() if uid == ADMIN_ID else get_user_keyboard()
    bot.send_message(uid, "Вы вышли в главное меню.", reply_markup=keyboard)

# === ДОБАВЛЕНИЕ ТОВАРОВ (АДМИН) ===
@bot.message_handler(func=lambda m: m.text == "➕ Добавить {product_type}")
def add_product_start(message):
    if message.chat.id != ADMIN_ID: return
    msg = bot.send_message(ADMIN_ID, "Введите название позиции (или 'Назад' для отмены):", reply_markup=get_chat_exit_keyboard())
    bot.register_next_step_handler(msg, add_product_name)

def add_product_name(message):
    if message.text == "🔙 Назад": return go_back(message)
    bot.send_message(ADMIN_ID, "Введите цену (например: 1500 руб):")
    bot.register_next_step_handler(message, add_product_price, message.text)

def add_product_price(message, name):
    if message.text == "🔙 Назад": return go_back(message)
    bot.send_message(ADMIN_ID, "Пришлите фотографию:")
    bot.register_next_step_handler(message, add_product_photo, name, message.text)

def add_product_photo(message, name, price):
    if message.text == "🔙 Назад": return go_back(message)
    if not message.photo:
        msg = bot.send_message(ADMIN_ID, "Нужно прислать именно фото! Попробуйте еще раз:")
        bot.register_next_step_handler(msg, add_product_photo, name, price)
        return
        
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    photo_path = f"photos/{{message.photo[-1].file_id}}.jpg"
    with open(photo_path, 'wb') as new_file:
        new_file.write(downloaded_file)
        
    db_query("INSERT INTO products (name, price, photo) VALUES (?, ?, ?)", (name, price, photo_path))
    bot.send_message(ADMIN_ID, f"✅ Позиция '{{name}}' успешно добавлена!", reply_markup=get_admin_keyboard())

# === ПЕРЕСЫЛКА СООБЩЕНИЙ В ЧАТЕ (АДМИН <-> КЛИЕНТ) ===
@bot.message_handler(content_types=['text', 'photo', 'document', 'voice'])
def handle_chat_messages(message):
    uid = message.chat.id
    
    if user_states.get(uid) == 'CHATTING_WITH_ADMIN':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Ответить", callback_data=f"chat_reply_{{uid}}"))
        
        text_prefix = f"💬 <b>Сообщение от клиента @{{message.from_user.username or message.from_user.first_name}}:</b>\\n\\n"
        
        if message.text:
            bot.send_message(ADMIN_ID, text_prefix + message.text, parse_mode='HTML', reply_markup=markup)
        elif message.photo:
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=text_prefix + (message.caption or ""), parse_mode='HTML', reply_markup=markup)
            
    elif uid == ADMIN_ID and uid in user_states and user_states[uid].startswith('CHATTING_WITH_USER_'):
        client_id = int(user_states[uid].split('_')[3])
        text_prefix = "👩‍💼 <b>Сообщение от менеджера:</b>\\n\\n"
        try:
            if message.text:
                bot.send_message(client_id, text_prefix + message.text, parse_mode='HTML')
            elif message.photo:
                bot.send_photo(client_id, message.photo[-1].file_id, caption=text_prefix + (message.caption or ""), parse_mode='HTML')
        except Exception as e:
            bot.send_message(ADMIN_ID, "Не удалось отправить сообщение. Возможно клиент заблокировал бота.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('chat_reply_'))
def admin_start_chat(call):
    client_id = call.data.split('_')[2]
    user_states[ADMIN_ID] = f'CHATTING_WITH_USER_{{client_id}}'
    bot.send_message(ADMIN_ID, f"Вы вошли в режим диалога с клиентом. Все ваши следующие сообщения будут отправлены ему.\\nДля выхода нажмите 'Назад'.", reply_markup=get_chat_exit_keyboard())
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    print("Бот {company_name} запущен!")
    bot.infinity_polling()
'''
    return template

# --- 4. МАРШРУТИЗАЦИЯ И ЛОГИКА ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != AUTHORIZED_ADMIN_ID:
        await message.answer("В доступе отказано. Идентификация не пройдена.")
        return
    
    await message.answer(
        "⬛️ Системный архитектор инициализирован.\n"
        "Давай соберем нового бота на базе шаблона.\n\n"
        "Отправь мне **ТОКЕН** нового бота (из BotFather):"
    )
    await state.set_state(BotConfigurator.waiting_for_token)

@dp.message(BotConfigurator.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    await state.update_data(token=message.text.strip())
    await message.answer("Принято. Теперь отправь **ID Админа** (кому будут приходить заказы, бэкапы и админ-панель):")
    await state.set_state(BotConfigurator.waiting_for_admin_id)

@dp.message(BotConfigurator.waiting_for_admin_id)
async def process_admin_id(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID должен состоять только из цифр. Попробуй еще раз:")
        return
    await state.update_data(admin_id=message.text.strip())
    await message.answer("Отлично. Как называется бизнес? (Например: <i>Cyber-Barbershop</i> или <i>Кондитерская у Аси</i>):", parse_mode="HTML")
    await state.set_state(BotConfigurator.waiting_for_company_name)

@dp.message(BotConfigurator.waiting_for_company_name)
async def process_company_name(message: types.Message, state: FSMContext):
    await state.update_data(company_name=message.text.strip())
    await message.answer("Введи приветственный текст для клиентов при команде /start (Например: <i>Добро пожаловать в наш премиум-салон! Выбирай услуги ниже</i>):", parse_mode="HTML")
    await state.set_state(BotConfigurator.waiting_for_context)

@dp.message(BotConfigurator.waiting_for_context)
async def process_context(message: types.Message, state: FSMContext):
    await state.update_data(context_msg=message.text.strip())
    await message.answer("Как называется то, что продает бизнес? (Например: <i>товар</i>, <i>услугу</i>, <i>десерт</i>, <i>стрижку</i>). Это пойдет в кнопку '➕ Добавить ...':")
    await state.set_state(BotConfigurator.waiting_for_product_type)

@dp.message(BotConfigurator.waiting_for_product_type)
async def process_compile(message: types.Message, state: FSMContext):
    await state.update_data(product_type=message.text.strip())
    data = await state.get_data()
    
    await message.answer("⏳ Анализирую зависимости... Компилирую архитектуру... Создаю 3 варианта сохранения...")
    
    # Генерация кода
    compiled_code = get_bot_template(
        token=data['token'],
        admin_id=data['admin_id'],
        company_name=data['company_name'],
        context_msg=data['context_msg'],
        product_type=data['product_type']
    )
    
    # ЗАПАСНОЙ ВАРИАНТ 1: Отправка файлом напрямую из памяти
    try:
        file_bytes = compiled_code.encode('utf-8')
        input_file = BufferedInputFile(file_bytes, filename=f"bot_{data['company_name'].replace(' ', '_')}.py")
        await message.answer_document(input_file, caption="✅ Компиляция завершена! (Вариант 1: Прямая отправка в RAM)")
    except Exception as e:
        logger.error(f"Memory send failed: {e}")
        
        # ЗАПАСНОЙ ВАРИАНТ 2: Сохранение на диск и отправка
        try:
            temp_filename = f"temp_bot.py"
            with open(temp_filename, 'w', encoding='utf-8') as f:
                f.write(compiled_code)
            from aiogram.types import FSInputFile
            await message.answer_document(FSInputFile(temp_filename), caption="✅ Компиляция завершена! (Вариант 2: Дисковый бэкап)")
            os.remove(temp_filename)
        except Exception as e2:
            logger.error(f"Disk send failed: {e2}")
            
            # ЗАПАСНОЙ ВАРИАНТ 3: Отправка частями прямо в чат (если API телеграма блокирует файлы)
            await message.answer("⚠️ Отправка файла заблокирована. Активирован Вариант 3: Выдача сырого кода.")
            chunks = [compiled_code[i:i+4000] for i in range(0, len(compiled_code), 4000)]
            for chunk in chunks:
                await message.answer(f"```python\n{chunk}\n```", parse_mode="MarkdownV2")

    await message.answer("Разработка — это святое. Жду новых архитектурных задач. Для повторной генерации введи /start.")
    await state.clear()

async def main():
    logger.info("Starting Generator Bot...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
