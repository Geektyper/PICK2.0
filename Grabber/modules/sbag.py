from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pymongo import MongoClient
from . import user_collection, Grabberu

@Grabberu.on_message(filters.command("sbag"))
async def sbag(client, message):
    user_id = message.from_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if user_data:
        gold_amount = user_data.get('gold', 0)
        ruby_amount = user_data.get('rubies', 0)  # Include ruby amount
        weapons = user_data.get('weapons', [])

        message_text = (
            f"💰 Your current gold amount: {gold_amount}\n"
            f"💎 Your current ruby amount: {ruby_amount}\n\n"  # Display ruby amount
        )

        if weapons:
            message_text += "🗡️ Your Weapons:\n"
            for weapon in weapons:
                message_text += f"- {weapon['name']} (Damage: {weapon['damage']})\n"
        else:
            message_text += "🗡️ You currently have no weapons."

        await message.reply_text(message_text)
    else:
        await message.reply_text("💰 You currently have no gold or rubies.")