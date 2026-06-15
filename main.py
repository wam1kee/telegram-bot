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

GAMES = {
    "кубик": {"emoji": "🎲", "min_bet": 10, "multiplier": 2},
    "дартс": {"emoji": "🎯", "min_bet": 10, "multiplier": 2},
    "баскетбол": {"emoji": "🏀", "min_bet": 10, "multiplier": 2},
    "футбол": {"emoji": "⚽", "min_bet": 10, "multiplier": 2}
}

user_states = {}

def main_menu(user_id):
    balance = get_balance(user_id)
    if balance == float('inf'):
        balance_display = "∞ (админ)"
    else:
        balance_display = f"{balance} 💎"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="play")],
        [InlineKeyboardButton(text="🎁 Промокод", callback_data="promo")],
        [InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit")],
        [InlineKeyboardButton(text="📊 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="ℹ️ Как играть", callback_data="info")]
    ])
    
    if is_admin(user_id):
        kb.inline_keyboard.append([InlineKeyboardButton(text="👑 Админ панель", callback_data="admin")])
    
    return kb

@dp.message(Command("start"))
async def start(msg: types.Message):
    balance = get_balance(msg.from_user.id)
    await msg.answer(f"👋 Добро пожаловать!\n💰 Баланс: {balance if balance != float('inf') else '∞'} 💎\n💎 1 кристалл = 0.01$", reply_markup=main_menu(msg.from_user.id))

# ============ ПОПОЛНЕНИЕ ============
@dp.callback_query(lambda c: c.data == "deposit")
async def deposit_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="100 💎 - 1$", callback_data="deposit_100")],
        [InlineKeyboardButton(text="500 💎 - 5$", callback_data="deposit_500")],
        [InlineKeyboardButton(text="1000 💎 - 10$", callback_data="deposit_1000")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await callback.message.edit_text("💰 **Выбери сумму пополнения:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("deposit_"))
async def process_deposit(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[1])
    await callback.message.edit_text(f"💎 **Пополнение на {amount} 💎**\n\n💰 Сумма: {amount // 100}$\n\n📌 Оплати и напиши админу @TgFidel с скриншотом\n🆔 Твой ID: `{callback.from_user.id}`", parse_mode="Markdown")
    await callback.answer()

# ============ ИГРЫ ============
@dp.callback_query(lambda c: c.data == "play")
async def play_menu(callback: types.CallbackQuery):
    balance = get_balance(callback.from_user.id)
    if balance == 0 or (balance != float('inf') and balance < 10):
        await callback.message.answer("❌ Недостаточно средств! Пополни баланс", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit")]
        ]))
        await callback.answer()
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Кубик", callback_data="game_кубик"),
         InlineKeyboardButton(text="🎯 Дартс", callback_data="game_дартс")],
        [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_баскетбол"),
         InlineKeyboardButton(text="⚽ Футбол", callback_data="game_футбол")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await callback.message.edit_text("🎮 **Выбери игру:**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("game_"))
async def select_game(callback: types.CallbackQuery):
    game_name = callback.data.split("_")[1]
    user_states[callback.from_user.id] = f"bet_{game_name}"
    await callback.message.answer(f"🎲 Игра: {GAMES[game_name]['emoji']} {game_name.upper()}\n💰 Минимальная ставка: 10 💎\n\nВведи сумму ставки (10, 20, 50, 100):")
    await callback.answer()

@dp.message()
async def process_bet(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in user_states or not user_states[user_id].startswith("bet_"):
        return
    
    try:
        bet = int(msg.text)
        game_name = user_states[user_id].split("_")[1]
        balance = get_balance(user_id)
        
        if bet < 10:
            await msg.answer("❌ Минимальная ставка 10 💎")
            return
        
        if bet > balance and balance != float('inf'):
            await msg.answer(f"❌ Недостаточно средств! Баланс: {balance} 💎")
            return
        
        if not is_admin(user_id):
            remove_balance(user_id, bet)
        
        win = random.choice([True, False])
        if win:
            win_amount = bet * GAMES[game_name]["multiplier"]
            add_balance(user_id, win_amount)
            await msg.answer(f"✅ **ПОБЕДА!**\nВыигрыш: {win_amount} 💎")
        else:
            await msg.answer(f"❌ **ПРОИГРЫШ!**\nСтавка: {bet} 💎")
        
        await msg.answer(f"💰 Новый баланс: {get_balance(user_id) if get_balance(user_id) != float('inf') else '∞'} 💎", reply_markup=main_menu(user_id))
        del user_states[user_id]
        
    except ValueError:
        await msg.answer("❌ Введи число!")

# ============ ПРОМОКОДЫ ============
@dp.callback_query(lambda c: c.data == "promo")
async def promo_menu(callback: types.CallbackQuery):
    user_states[callback.from_user.id] = "waiting_promo"
    await callback.message.answer("🎁 Введи промокод:")
    await callback.answer()

@dp.message()
async def process_promo(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in user_states or user_states[user_id] != "waiting_promo":
        return
    
    code = msg.text.strip().upper()
    user_id_str = str(user_id)
    
    if code not in promocodes:
        await msg.answer("❌ Неверный промокод!")
        del user_states[user_id]
        return
    
    promo = promocodes[code]
    if promo["used"] >= promo["max_uses"]:
        await msg.answer("❌ Промокод уже использован максимальное количество раз!")
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
    
    await msg.answer(f"✅ Промокод активирован! +{promo['reward']} 💎\n💰 Новый баланс: {get_balance(user_id)} 💎", reply_markup=main_menu(user_id))
    del user_states[user_id]

# ============ ПРОФИЛЬ ============
@dp.callback_query(lambda c: c.data == "profile")
async def profile(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    balance = get_balance(callback.from_user.id)
    used_promos = len(users_data.get(user_id, {}).get("promo_used", []))
    
    await callback.message.edit_text(f"📊 **Твой профиль**\n\n🆔 ID: {callback.from_user.id}\n💰 Баланс: {balance if balance != float('inf') else '∞'} 💎\n🎁 Использовано промокодов: {used_promos}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ]), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "info")
async def info(callback: types.CallbackQuery):
    await callback.message.edit_text("🎲 **Как играть:**\n\n1. Пополни баланс\n2. Нажми 'Играть'\n3. Выбери игру\n4. Сделай ставку (мин. 10 💎)\n5. Победа = x2", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ]), parse_mode="Markdown")
    await callback.answer()

# ============ АДМИН ПАНЕЛЬ ============
@dp.callback_query(lambda c: c.data == "admin")
async def admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="admin_balance")],
        [InlineKeyboardButton(text="🎁 Добавить промокод", callback_data="admin_promo")],
        [InlineKeyboardButton(text="📊 Список промокодов", callback_data="admin_list")],
        [InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    await callback.message.edit_text("👑 **Админ панель**", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_balance")
async def admin_balance_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    user_states[callback.from_user.id] = "admin_waiting_user"
    await callback.message.answer("💳 Введи ID пользователя и сумму через пробел\nПример: `5049662929 100`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_promo")
async def admin_add_promo_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    user_states[callback.from_user.id] = "admin_waiting_promo"
    await callback.message.answer("🎁 Введи промокод, сумму и лимит через пробел\nПример: `TEST 100 5`", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_list")
async def admin_list_promos(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    if not promocodes:
        await callback.message.answer("❌ Нет промокодов")
    else:
        text = "🎁 **Список промокодов:**\n\n"
        for code, data in promocodes.items():
            text += f"📌 {code}: +{data['reward']} 💎 | {data['used']}/{data['max_uses']}\n"
        await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа!")
        return
    
    total_users = len(users_data)
    total_balance = sum(u["balance"] for u in users_data.values() if isinstance(u["balance"], (int, float)))
    await callback.message.answer(f"📊 **Статистика:**\n\n👥 Пользователей: {total_users}\n💰 Общий баланс: {total_balance} 💎", parse_mode="Markdown")
    await callback.answer()

# ============ ОБРАБОТЧИКИ АДМИН КОМАНД ============
@dp.message()
async def handle_admin_commands(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()
    
    if user_id in user_states and user_states[user_id] == "admin_waiting_user":
        parts = text.split()
        if len(parts) == 2:
            try:
                target_id = int(parts[0])
                amount = int(parts[1])
                add_balance(target_id, amount)
                await msg.answer(f"✅ Начислено {amount} 💎 пользователю {target_id}")
                try:
                    await bot.send_message(target_id, f"✅ Ваш баланс пополнен на {amount} 💎!\n💰 Новый баланс: {get_balance(target_id)} 💎")
                except:
                    pass
            except:
                await msg.answer("❌ Ошибка! Пример: `5049662929 100`", parse_mode="Markdown")
        else:
            await msg.answer("❌ Пример: `5049662929 100`", parse_mode="Markdown")
        del user_states[user_id]
    
    elif user_id in user_states and user_states[user_id] == "admin_waiting_promo":
        parts = text.split()
        if len(parts) == 3:
            code = parts[0].upper()
            reward = int(parts[1])
            max_uses = int(parts[2])
            promocodes[code] = {"reward": reward, "max_uses": max_uses, "used": 0}
            save_promos()
            await msg.answer(f"✅ Промокод {code} создан!\n💰 Награда: {reward} 💎\n🔢 Лимит: {max_uses} активаций")
        else:
            await msg.answer("❌ Пример: `TEST 100 5`", parse_mode="Markdown")
        del user_states[user_id]

@dp.callback_query(lambda c: c.data == "back")
async def back(callback: types.CallbackQuery):
    balance = get_balance(callback.from_user.id)
    await callback.message.edit_text(f"👋 Главное меню\n💰 Баланс: {balance if balance != float('inf') else '∞'} 💎", reply_markup=main_menu(callback.from_user.id))
    await callback.answer()

# ============ ЗАПУСК ============
async def main():
    print("✅ Casino бот запущен")
    print(f"👑 Админы: {ADMIN_ID} и {ADMIN_ID2}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
