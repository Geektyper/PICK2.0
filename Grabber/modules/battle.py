import math
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pymongo import MongoClient
import random
import asyncio
from . import user_collection, clan_collection, application, Grabberu

weapons_data = [
    {'name': 'Sword', 'price': 500, 'damage': 10},
    {'name': 'Bow', 'price': 800, 'damage': 15},
    {'name': 'Staff', 'price': 1000, 'damage': 20},
    {'name': 'Knife', 'price': 200, 'damage': 5},
    {'name': 'Snipper', 'price': 5000, 'damage': 30}
]

def custom_format_number(num):
    if int(num) >= 10**6:
        exponent = int(math.log10(num)) - 5
        base = num // (10 ** exponent)
        return f"{base:,.0f}({exponent:+})"
    return f"{num:,.0f}"

def format_timedelta(delta):
    minutes, seconds = divmod(delta.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days = delta.days
    if days > 0:
        return f"{days}d {hours}m {minutes}s"
    elif hours > 0:
        return f"{hours}h {minutes}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

@Grabberu.on_message(filters.command("battle") & filters.reply)
async def battle_command(client, message):
    user_a_id = message.from_user.id
    user_a_data = await user_collection.find_one({'id': user_a_id})

    if not user_a_data or ('clan_id' not in user_a_data and 'leader_id' not in user_a_data):
        await message.reply_text("You need to be part of a clan or a clan leader to use this command.")
        return

    user_b_id = message.reply_to_message.from_user.id
    user_b_data = await user_collection.find_one_and_update(
        {'id': user_b_id},
        {'$setOnInsert': {'id': user_b_id, 'first_name': message.reply_to_message.from_user.first_name, 'gold': 0, 'weapons': []}},
        upsert=True,
        return_document=True
    )

    if not user_b_data:
        await message.reply_text("Opponent information not found and could not be created.")
        return

    user_a_name = user_a_data.get('first_name', 'User A')
    user_b_name = user_b_data.get('first_name', 'User B')

    # Log attacker's weapons
    attacker_weapons = user_a_data.get('weapons', [])

    # Log defender's weapons
    defender_weapons = user_b_data.get('weapons', [])

    keyboard = [
        [InlineKeyboardButton("Fight", callback_data=f"battle_accept:{user_a_id}:{user_b_id}"),
         InlineKeyboardButton("Run", callback_data=f"battle_decline:{user_a_id}:{user_b_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(f"{user_b_name}, {user_a_name} challenged you: Do you fight or run?", reply_markup=reply_markup)

@Grabberu.on_callback_query(filters.regex(r'^battle_accept'))
async def handle_battle_accept(client, query: CallbackQuery):
    data = query.data.split(':')
    user_a_id = int(data[1])
    user_b_id = int(data[2])

    if query.from_user.id != user_b_id:
        await query.answer("Only the challenged user can respond.", show_alert=True)
        return

    user_a_data = await user_collection.find_one({'id': user_a_id})
    user_b_data = await user_collection.find_one({'id': user_b_id})

    if not user_a_data or not user_b_data:
        await query.answer("Users not found.")
        return

    user_a_name = user_a_data.get('first_name', 'User A')
    user_b_name = user_b_data.get('first_name', 'User B')

    a_health = 100
    b_health = 100

    a_weapon_buttons = [
        [InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}:{user_a_id}:{a_health}:{b_health}")]
        for weapon in weapons_data if weapon['name'] in user_a_data.get('weapons', [])
    ]
    print(a_weapon_buttons)

    battle_message = await query.message.edit_text(
        f"{user_b_name} accepted the challenge!\n"
        f"{user_a_name}'s health: {a_health}/100\n"
        f"{user_b_name}'s health: {b_health}/100\n"
        f"{user_a_name}, choose your weapon:",
        reply_markup=InlineKeyboardMarkup(a_weapon_buttons)
    )

@Grabberu.on_callback_query(filters.regex(r'^battle_decline'))
async def handle_battle_decline(client, query: CallbackQuery):
    await query.answer("Challenge declined!")
    await query.message.edit_text("The battle challenge was declined.")

@Grabberu.on_callback_query(filters.regex(r'^battle_attack'))
async def handle_battle_attack(client, query: CallbackQuery):
    data = query.data.split(':')
    weapon_name = data[1]
    user_a_id = int(data[2])
    user_b_id = int(data[3])
    current_turn_id = int(data[4])
    a_health = int(data[5])
    b_health = int(data[6])

    if query.from_user.id != current_turn_id:
        await query.answer("It's not your turn!", show_alert=True)
        return

    user_a_data = await user_collection.find_one({'id': user_a_id})
    user_b_data = await user_collection.find_one({'id': user_b_id})

    if not user_a_data or not user_b_data:
        await query.answer("Users not found.")
        return

    attacker_name = user_a_data['first_name'] if current_turn_id == user_a_id else user_b_data['first_name']
    defender_name = user_b_data['first_name'] if current_turn_id == user_a_id else user_a_data['first_name']

    attacker_weapons = user_a_data.get('weapons', []) if current_turn_id == user_a_id else user_b_data.get('weapons', [])
    defender_health = a_health if current_turn_id == user_b_id else b_health

    weapon = next((w for w in weapons_data if w['name'] == weapon_name), None)
    if not weapon or weapon_name not in attacker_weapons:
        await query.answer("Invalid weapon choice!", show_alert=True)
        return

    damage = weapon['damage']
    defender_health -= damage
    if defender_health < 0:
        defender_health = 0

    if current_turn_id == user_a_id:
        b_health = defender_health
        next_turn_id = user_b_id
    else:
        a_health = defender_health
        next_turn_id = user_a_id

    if a_health == 0 or b_health == 0:
        winner_id = user_a_id if a_health > 0 else user_b_id
        loser_id = user_b_id if winner_id == user_a_id else user_a_id
        await end_battle(winner_id, loser_id)
        await query.message.edit_text(
            f"{attacker_name} attacked with {weapon_name}!\n"
            f"{defender_name} has {defender_health}/100 health left.\n"
            f"{attacker_name} wins the battle!"
        )
        return

    next_turn_name = user_b_data['first_name'] if next_turn_id == user_b_id else user_a_data['first_name']

    defender_weapons = user_b_data.get('weapons', []) if next_turn_id == user_b_id else user_a_data.get('weapons', [])
    weapon_buttons = [
        [InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}:{next_turn_id}:{a_health}:{b_health}")]
        for weapon in weapons_data if weapon['name'] in defender_weapons
    ]

    await query.message.edit_text(
        f"{attacker_name} attacked with {weapon_name}!\n"
        f"{defender_name} has {defender_health}/100 health left.\n"
        f"{next_turn_name}, choose your weapon:",
        reply_markup=InlineKeyboardMarkup(weapon_buttons)
    )

async def end_battle(winner_id, loser_id):
    winner_data = await user_collection.find_one_and_update(
        {'id': winner_id},
        {'$inc': {'gold': 100}},
        return_document=True
    )

    loser_data = await user_collection.find_one_and_update(
        {'id': loser_id},
        {'$set': {'gold': 0}},
        return_document=True
    )

    if winner_data and loser_data:
        winner_name = winner_data.get('first_name', 'Winner')
        loser_name = loser_data.get('first_name', 'Loser')

        await user_collection.update_one(
            {'id': winner_id},
            {'$set': {'battle_cooldown': datetime.now() + timedelta(minutes=5)}}
        )

        await user_collection.update_one(
            {'id': loser_id},
            {'$set': {'battle_cooldown': datetime.now() + timedelta(minutes=5)}}
        )

        await application.send_message(
            winner_id,
            f"Congratulations! You won the battle against {loser_name}. You earned 100 gold."
        )

        await application.send_message(
            loser_id,
            f"Unfortunately, you lost the battle against {winner_name}. You lost all your gold."
        )

@Grabberu.on_callback_query(filters.regex(r'^battle_decline'))
async def handle_battle_decline(client, query: CallbackQuery):
    await query.answer("Challenge declined!")
    await query.message.edit_text("The battle challenge was declined.")

@Grabberu.on_callback_query(filters.regex(r'^battle_attack'))
async def handle_battle_attack(client, query: CallbackQuery):
    data = query.data.split(':')
    weapon_name = data[1]
    user_a_id = int(data[2])
    user_b_id = int(data[3])
    current_turn_id = int(data[4])
    a_health = int(data[5])
    b_health = int(data[6])

    if query.from_user.id != current_turn_id:
        await query.answer("It's not your turn!", show_alert=True)
        return

    user_a_data = await user_collection.find_one({'id': user_a_id})
    user_b_data = await user_collection.find_one({'id': user_b_id})

    if not user_a_data or not user_b_data:
        await query.answer("Users not found.")
        return

    attacker_name = user_a_data['first_name'] if current_turn_id == user_a_id else user_b_data['first_name']
    defender_name = user_b_data['first_name'] if current_turn_id == user_a_id else user_a_data['first_name']

    attacker_weapons = user_a_data.get('weapons', []) if current_turn_id == user_a_id else user_b_data.get('weapons', [])
    defender_health = a_health if current_turn_id == user_b_id else b_health

    weapon = next((w for w in weapons_data if w['name'] == weapon_name), None)
    if not weapon or weapon_name not in attacker_weapons:
        await query.answer("Invalid weapon choice!", show_alert=True)
        return

    damage = weapon['damage']
    defender_health -= damage
    if defender_health < 0:
        defender_health = 0

    if current_turn_id == user_a_id:
        b_health = defender_health
        next_turn_id = user_b_id
    else:
        a_health = defender_health
        next_turn_id = user_a_id

    if a_health == 0 or b_health == 0:
        winner_id = user_a_id if a_health > 0 else user_b_id
        loser_id = user_b_id if winner_id == user_a_id else user_a_id
        await end_battle(winner_id, loser_id)
        await query.message.edit_text(
            f"{attacker_name} attacked with {weapon_name}!\n"
            f"{defender_name} has {defender_health}/100 health left.\n"
            f"{attacker_name} wins the battle!"
        )
        return

    next_turn_name = user_b_data['first_name'] if next_turn_id == user_b_id else user_a_data['first_name']

    defender_weapons = user_b_data.get('weapons', []) if next_turn_id == user_b_id else user_a_data.get('weapons', [])
    weapon_buttons = [
        [InlineKeyboardButton(weapon['name'], callback_data=f"battle_attack:{weapon['name']}:{user_a_id}:{user_b_id}:{next_turn_id}:{a_health}:{b_health}")]
        for weapon in weapons_data if weapon['name'] in defender_weapons
    ]

    await query.message.edit_text(
        f"{attacker_name} attacked with {weapon_name}!\n"
        f"{defender_name} has {defender_health}/100 health left.\n"
        f"{next_turn_name}, choose your weapon:",
        reply_markup=InlineKeyboardMarkup(weapon_buttons)
    )

async def end_battle(winner_id, loser_id):
    winner_data = await user_collection.find_one_and_update(
        {'id': winner_id},
        {'$inc': {'gold': 100}},
        return_document=True
    )

    loser_data = await user_collection.find_one_and_update(
        {'id': loser_id},
        {'$set': {'gold': 0}},
        return_document=True
    )

    if winner_data and loser_data:
        winner_name = winner_data.get('first_name', 'Winner')
        loser_name = loser_data.get('first_name', 'Loser')

        await user_collection.update_one(
            {'id': winner_id},
            {'$set': {'battle_cooldown': datetime.now() + timedelta(minutes=5)}}
        )

        await user_collection.update_one(
            {'id': loser_id},
            {'$set': {'battle_cooldown': datetime.now() + timedelta(minutes=5)}}
        )

        await application.send_message(
            winner_id,
            f"Congratulations! You won the battle against {loser_name}. You earned 100 gold."
        )

        await application.send_message(
            loser_id,
            f"Unfortunately, you lost the battle against {winner_name}. You lost all your gold."
        )