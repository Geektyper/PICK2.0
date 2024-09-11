from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import ReturnDocument
import random
from . import sudo_filter, app
from Grabber import collection, db, CHARA_CHANNEL_ID

app = Client("my_bot", timeout=120)

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']

rarity_map = {
    1: "🟢 Common",
    2: "🔵 Medium",
    3: "🟠 Rare",
    4: "🟡 Legendary",
    5: "🪽 Celestial",
    6: "🥵 Divine",
    7: "🥴 Special",
    8: "💎 Premium",
    9: "🔮 Limited",
    10: "🍭 Cosplay"
}

@app.on_message(filters.command('upload') & sudo_filter)
async def upload(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("Please reply to an image with the caption in the format: 'Name - Name Here\nAnime - Anime Here\nRarity - Number'")
        return

    caption = message.reply_to_message.caption.strip().split("\n")
    if len(caption) != 3:
        await message.reply_text("Incorrect format. Please use the format: 'Name - Name Here\nAnime - Anime Here\nRarity - Number'")
        return

    try:
        character_name = caption[0].split(" - ")[1].strip().title()
        anime = caption[1].split(" - ")[1].strip().title()
        rarity_str = caption[2].split(" - ")[1].strip()
        rarity = rarity_map[int(rarity_str)]
    except (KeyError, ValueError, IndexError):
        await message.reply_text("Invalid format or rarity. Please use the format: 'Name - Name Here\nAnime - Anime Here\nRarity - Number' and ensure rarity is a number between 1 and 10.")
        return

    try:
        photo = await client.download_media(message.reply_to_message.photo)

        id = str(await get_next_sequence_number('character_id')).zfill(2)
        price = random.randint(60000, 80000)

        sent_message = await client.send_photo(
            chat_id=CHARA_CHANNEL_ID,
            photo=photo,
            caption=(
                f'Waifu Name: {character_name}\n'
                f'Anime Name: {anime}\n'
                f'Quality: {rarity}\n'
                f'Price: {price}\n'
                f'ID: {id}\n'
                f'Added by {message.from_user.first_name}'
            )
        )

        character = {
            'img_url': sent_message.photo.file_id,
            'name': character_name,
            'anime': anime,
            'rarity': rarity,
            'price': price,
            'id': id,
            'message_id': sent_message.id
        }

        await collection.insert_one(character)
        await message.reply_text('WAIFU ADDED....')

    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")
