import asyncio
import random
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8642030263:AAHp1M74lNjXMDfvd_oAqg1gvuvLyaO2r2k"
ADMIN_ID = 8492086832
ADMIN_ID2 = 914664289

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_data = {}
promocodes = {}

if os.path.exists("users.json"):
    with open("users.json", "r") as f:
        users_data = json.load(f)
if os.path.exists("promos.json"):
    with open("promos.json", "r") as f:
        promocodes = json.load(f)

def save_users():
    with open("users.json", "w") as f:
        json.dump(users_data, f, indent=4)

def save_promos():
    with open("promos.json", "w") as f:
        json.dump(promocodes, f, indent=4)

def is_admin(user_id):
    return user_id == ADMIN_ID or user_id == ADMIN_ID2

def get_balance(user_id):
    user_id = str(user_id)
    if is_admin(int(user_id)):
        return float('inf')
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0, "promo_used": []}
        save_users()
    return users_data[user_id]["balance"]

def add_balance(user_id, amount):
    user_id = str(user_id)
    if is_admin(int(user_id)):
        return
    if user_id not in users_data:
        users_data[user_id] = {"balance": 0, "promo_used": []}
    users_data[user_id]["balance"] += amount
    save_users()

def remove_balance(user_id, amount):
    user_id = str(user_id)
    if is_admin(int(user_id)):
        return True
    if get_balance(user_id) >= amount:
        users_data[user_id]["balance"] -= amount
        save_users()
        return True
    return False

@dp.message(Command("start"))
async def start(msg: types.Message):
    balance = get_balance(msg.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="play")],
        [InlineKeyboardButton(text="🎁 Промокод", callback_data="promo")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")]
    ])
    await msg.answer(f"👋 Привет!\n💰 Баланс: {balance if balance != float('inf') else '∞'} 💎", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "play")
async def play(callback: types.CallbackQuery):
    balance = get_balance(callback.from_user.id)
    if balance < 10 and balance != float('inf'):
        await callback.message.answer("❌ Недостаточно средств!")
        await callback.answer()
        return
    
    await callback.message.answer("🎲 Введи сумму ставки (10, 20, 50, 100):")
    user_states[callback.from_user.id] = "waiting_bet"
    await callback.answer()

@dp.callback_query(lambda c: c.data == "balance")
async def balance_cmd(callback: types.CallbackQuery):
    balance = get_balance(callback.from_user.id)
    await callback.message.answer(f"💰 Баланс: {balance if balance != float('inf') else '∞'} 💎")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "promo")
async def promo_cmd(callback: types.CallbackQuery):
    user_states[callback.from_user.id] = "waiting_promo"
    await callback.message.answer("🎁 Введи промокод:")
    await callback.answer()

@dp.message()
async def handle_messages(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()
    
    if user_id in user_states and user_states[user_id] == "waiting_bet":
        try:
            bet = int(text)
            balance = get_balance(user_id)
            if bet < 10:
                await msg.answer("❌ Минимальная ставка 10 💎")
                return
            if bet > balance and balance != float('inf'):
                await msg.answer(f"❌ Недостаточно! Баланс: {balance} 💎")
                return
            
            if not is_admin(user_id):
                remove_balance(user_id, bet)
            
            win = random.choice([True, False])
            if win:
                win_amount = bet * 2
                add_balance(user_id, win_amount)
                await msg.answer(f"✅ ПОБЕДА! +{win_amount} 💎")
            else:
                await msg.answer(f"❌ ПРОИГРЫШ! -{bet} 💎")
            
            await msg.answer(f"💰 Новый баланс: {get_balance(user_id)} 💎")
            del user_states[user_id]
        except ValueError:
            await msg.answer("❌ Введи число!")
    
    elif user_id in user_states and user_states[user_id] == "waiting_promo":
        code = text.upper()
        user_id_str = str(user_id)
        
        if code not in promocodes:
            await msg.answer("❌ Неверный промокод!")
            del user_states[user_id]
            return
        
        promo = promocodes[code]
        if promo["used"] >= promo["max_uses"]:
            await msg.answer("❌ Промокод использован!")
            del user_states[user_id]
            return
        
        if code in users_data.get(user_id_str, {}).get("promo_used", []):
            await msg.answer("❌ Ты уже использовал этот промокод!")
            del user_states[user_id]
            return
        
        add_balance(user_id, promo["reward"])
        if user_id_str not in users_data:
            users_data[user_id_str] = {"balance": 0, "promo_used": []}
        users_data[user_id_str]["promo_used"].append(code)
        promocodes[code]["used"] += 1
        save_users()
        save_promos()
        
        await msg.answer(f"✅ +{promo['reward']} 💎! Баланс: {get_balance(user_id)} 💎")
        del user_states[user_id]
    
    elif text.startswith("/confirm") and is_admin(user_id):
        parts = text.split()
        if len(parts) == 3:
            try:
                target_id = int(parts[1])
                amount = int(parts[2])
                add_balance(target_id, amount)
                await msg.answer(f"✅ Начислено {amount} 💎 пользователю {target_id}")
                try:
                    await bot.send_message(target_id, f"✅ Ваш баланс пополнен на {amount} 💎!\n💰 Новый баланс: {get_balance(target_id)} 💎")
                except:
                    pass
            except:
                await msg.answer("❌ Ошибка! Пример: /confirm 123456789 100")
        else:
            await msg.answer("❌ Формат: /confirm ID СУММА")

async def main():
    print("✅ Бот запущен")
    print(f"👑 Админы: {ADMIN_ID} и {ADMIN_ID2}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
