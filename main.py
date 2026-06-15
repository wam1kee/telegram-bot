import asyncio
import random
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8642030263:AAHp1M74lNjXMDfvd_oAqg1gvuvLyaO2r2k"
ADMIN_ID = 8492086832

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_data = {}
if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users_data = json.load(f)

def save_users():
    with open("users.json", "w") as f:
        json.dump(users_data, f, indent=4)

def get_balance(user_id):
    user_id = str(user_id)
    if user_id not in users_data:
        users_data[user_id] = {"balance": 100}
        save_users()
    return users_data[user_id]["balance"]

def add_balance(user_id, amount):
    user_id = str(user_id)
    if user_id not in users_data:
        users_data[user_id] = {"balance": 100}
    users_data[user_id]["balance"] += amount
    save_users()

@dp.message(Command("start"))
async def start(msg: types.Message):
    balance = get_balance(msg.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="play")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")]
    ])
    await msg.answer(f"👋 Привет!\n💰 Баланс: {balance} 💎", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "play")
async def play(callback: types.CallbackQuery):
    balance = get_balance(callback.from_user.id)
    if balance < 10:
        await callback.message.answer("❌ Недостаточно средств!")
        await callback.answer()
        return
    
    remove_balance = get_balance(callback.from_user.id) - 10
    users_data[str(callback.from_user.id)]["balance"] = remove_balance
    save_users()
    
    win = random.choice([True, False])
    if win:
        win_amount = 20
        add_balance(callback.from_user.id, win_amount)
        await callback.message.answer(f"✅ ПОБЕДА! +{win_amount}💎")
    else:
        await callback.message.answer(f"❌ ПРОИГРЫШ! -10💎")
    
    await callback.message.answer(f"💰 Новый баланс: {get_balance(callback.from_user.id)}💎")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "balance")
async def balance(callback: types.CallbackQuery):
    balance = get_balance(callback.from_user.id)
    await callback.message.answer(f"💰 Баланс: {balance} 💎")
    await callback.answer()

@dp.message(Command("confirm"))
async def confirm(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("❌ Нет доступа!")
        return
    parts = msg.text.split()
    if len(parts) == 3:
        try:
            user_id = int(parts[1])
            amount = int(parts[2])
            add_balance(user_id, amount)
            await msg.answer(f"✅ Начислено {amount} 💎 пользователю {user_id}")
            try:
                await bot.send_message(user_id, f"✅ Ваш баланс пополнен на {amount} 💎!")
            except:
                pass
        except:
            await msg.answer("❌ Ошибка! Пример: /confirm 123456789 100")
    else:
        await msg.answer("❌ Пример: /confirm 123456789 100")

async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
