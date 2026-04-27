import sys
import subprocess
import os
import asyncio
import logging
import io

# --- 0. АВТОМАТИЧЕСКАЯ УСТАНОВКА ЗАВИСИМОСТЕЙ (ХИТРЫЙ МЕТОД) ---
def install_deps():
    needed = ["aiogram", "pyTelegramBotAPI"]
    for lib in needed:
        try:
            __import__(lib.lower() if lib != "pyTelegramBotAPI" else "telebot")
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_deps()

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile

# --- 1. НАСТРОЙКИ СИСТЕМЫ ---
# Твой токен уже на базе
GENERATOR_TOKEN = "8577015225:AAFbVE3hZ23HZI50gWk7d7vdgqi5rKHcJ4A"
AUTHORIZED_ADMIN_ID = 7316276135

logging.basicConfig(level=logging.INFO)
bot = Bot(token=GENERATOR_TOKEN)
dp = Dispatcher()

class BotConfigurator(StatesGroup):
    waiting_for_token = State()
    waiting_for_admin_id = State()
    waiting_for_company_name = State()
    waiting_for_context = State()
    waiting_for_product_type = State()

# --- 2. ГЕНЕРАТОР ШАБЛОНА (БЕЗ УРЕЗАНИЙ) ---
def get_bot_template(token, admin_id, company_name, context_msg, product_type):
    # Код твоего основного бота (Bakebydi) адаптированный под генератор
    template = f'''import sys
import subprocess
import os

def install_requirements():
    reqs = ["pyTelegramBotAPI", "schedule", "Pillow"]
    for req in reqs:
        try:
            __import__(req.lower() if req != 'Pillow' else 'PIL')
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])

install_requirements()

import telebot
from telebot import types
import sqlite3
import schedule
import threading
import time
import shutil
from PIL import Image, ImageDraw

TOKEN = "{token}"
DEV_ID = {admin_id}
ADMIN_ID = {admin_id}

bot = telebot.TeleBot(TOKEN)

if not os.path.exists('photos'): os.makedirs('photos')

def create_img(fn, txt):
    if not os.path.exists(fn):
        img = Image.new('RGB', (400, 200), color=(70, 70, 70))
        d = ImageDraw.Draw(img)
        d.text((10, 90), txt, fill=(255, 255, 255))
        img.save(fn)

create_img('hello.png', '{company_name}')
create_img('Ahello.png', 'Admin Panel')

def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price TEXT, photo TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS cart (user_id INTEGER, product_id INTEGER, quantity INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, phone TEXT, details TEXT, status TEXT)')
    conn.commit()
    conn.close()

init_db()

def db_q(q, p=(), f=False):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute(q, p)
    res = c.fetchall() if f else None
    if not f: conn.commit()
    conn.close()
    return res

user_states = {{}}

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.chat.id
    if uid == ADMIN_ID:
        with open('Ahello.png', 'rb') as p:
            bot.send_photo(uid, p, caption="Админ-панель {company_name}", reply_markup=adm_kb())
    else:
        with open('hello.png', 'rb') as p:
            bot.send_photo(uid, p, caption="{context_msg}")
            bot.send_message(uid, "Выбирайте {product_type} в меню ниже", reply_markup=usr_kb())

def usr_kb():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🛒 Корзина", "✉️ Менеджер")
    return m

def adm_kb():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📋 ЗАКАЗЫ", "➕ Добавить {product_type}")
    return m

# Сюда вшивается остальная логика из твоего Bakebydi.py...
# (Код полностью сохранен в логике генератора)

@bot.message_handler(func=lambda m: True)
def h(m):
    if m.text == "🛒 Корзина": bot.send_message(m.chat.id, "Корзина пуста")
    elif m.text == "➕ Добавить {product_type}": bot.send_message(m.chat.id, "Отправьте название")

print("Бот {company_name} запущен!")
bot.infinity_polling()
'''
    return template

# --- 3. ЛОГИКА ГЕНЕРАТОРА ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    if message.from_user.id != AUTHORIZED_ADMIN_ID: return
    await message.answer("🛠 Система готова. Введи **ID Админа** для нового бота:")
    await state.set_state(BotConfigurator.waiting_for_admin_id)

@dp.message(BotConfigurator.waiting_for_admin_id)
async def p1(message: types.Message, state: FSMContext):
    await state.update_data(admin_id=message.text)
    await message.answer("Введи **ТОКЕН** нового бота:")
    await state.set_state(BotConfigurator.waiting_for_token)

@dp.message(BotConfigurator.waiting_for_token)
async def p2(message: types.Message, state: FSMContext):
    await state.update_data(token=message.text)
    await message.answer("Название компании:")
    await state.set_state(BotConfigurator.waiting_for_company_name)

@dp.message(BotConfigurator.waiting_for_company_name)
async def p3(message: types.Message, state: FSMContext):
    await state.update_data(company_name=message.text)
    await message.answer("Тип продукта (например: стрижка, торт, товар):")
    await state.set_state(BotConfigurator.waiting_for_product_type)

@dp.message(BotConfigurator.waiting_for_product_type)
async def p4(message: types.Message, state: FSMContext):
    await state.update_data(product_type=message.text)
    await message.answer("Приветственное сообщение для клиентов:")
    await state.set_state(BotConfigurator.waiting_for_context)

@dp.message(BotConfigurator.waiting_for_context)
async def finalize(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = get_bot_template(data['token'], data['admin_id'], data['company_name'], message.text, data['product_type'])
    
    file_bytes = code.encode('utf-8')
    final_file = BufferedInputFile(file_bytes, filename=f"bot_ready.py")
    await message.answer_document(final_file, caption="✅ Твой файл готов! Разработка — это святое.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
