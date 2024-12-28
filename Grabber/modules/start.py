from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
import random
from . import user_collection, app, capsify
from Grabber import *
from .block import block_dec, temp_block

sudb = db.sudo
devb = db.dev
uploaderdb = db.uploader

BOT_NAME = "Okarun"  
start_text = f"👋 Hi, this is {BOT_NAME}, an anime-based games bot! Add me to your group to start your journey."
credits_text = (
    "Bot Credits\n\n"
    "Users below are the developers, uploaders, etc... of this bot, you can personally contact them for issues, do not DM unnecessarily.\n\n"
    "Thank You!"
)

support_buttons = [
    [IKB(capsify("Support"), url=f"https://t.me/{SUPPORT_CHAT}"),
     IKB(capsify("Updates"), url=f"https://t.me/{UPDATE_CHAT}")],
    [IKB(capsify("Add Me Baby 🐥"), url=f"https://t.me/{BOT_NAME}?startgroup=true")],
    [IKB(capsify("Help"), url=f"https://t.me/{SUPPORT_CHAT}"),
     IKB(capsify("Credits"), callback_data="credits")]
]

@app.on_message(filters.command("start") & filters.private)
@block_dec
async def startp(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    user = await _.get_users(user_id)
    username = user.username
    first_name = user.first_name

    user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "first_name": first_name}},
        upsert=True
    )

    random_video = random.choice(PHOTO_URL)
    await _.send_video(
        chat_id=user_id,
        video=random_video,
        caption=capsify(start_text),
        reply_markup=IKM(support_buttons)
    )

@app.on_message(filters.command("start") & filters.group)
@block_dec
async def startg(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    await message.reply_text(
        capsify("🚀 To start using me, please click the button below to initiate in DM."),
        reply_markup=IKM([
            [IKB(capsify("Start in DM"), url=f"https://t.me/{BOT_NAME}")]
        ])
    )

@app.on_message(filters.command("credits"))
@block_dec
async def cred(_, message):
    user_id = message.from_user.id
    if temp_block(user_id):
        return
    await message.reply_text(
        text=capsify(credits_text),
        reply_markup=IKM([
            [IKB(capsify("Developers"), callback_data="sdev"),
             IKB(capsify("Sudos"), callback_data="ssudo")],
            [IKB(capsify("Uploads"), callback_data="suploader"),
             IKB(capsify("Back"), callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("credits"))
async def credcb(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify(credits_text),
        reply_markup=IKM([
            [IKB(capsify("Developers"), callback_data="sdev"),
             IKB(capsify("Sudos"), callback_data="ssudo")],
            [IKB(capsify("Uploads"), callback_data="suploader"),
             IKB(capsify("Back"), callback_data="main")]
        ])
    )

@app.on_callback_query(filters.regex("sdev"))
async def sdev(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading developer names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    dev_buttons = []
    async for user in devb.find():
        dev_id = user.get("user_id")
        first_name = user.get("first_name", "Unknown")
        if dev_id:
            dev_buttons.append(IKB(capsify(first_name), user_id=dev_id))

    rows = [dev_buttons[i:i+3] for i in range(0, min(len(dev_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Developers:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("ssudo"))
async def ssudo(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading sudo names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    sudo_buttons = []
    async for user in sudb.find():
        sudo_id = user.get("user_id")
        first_name = user.get("first_name", "Unknown")
        if sudo_id:
            sudo_buttons.append(IKB(capsify(first_name), user_id=sudo_id))

    rows = [sudo_buttons[i:i+3] for i in range(0, min(len(sudo_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Sudos:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("suploader"))
async def suploader(_, callback_query):
    await callback_query.edit_message_text(
        text=capsify("Loading uploader names..."),
        reply_markup=IKM([
            [IKB(capsify("Back"), callback_data="credits")]
        ])
    )

    uploader_buttons = []
    async for user in uploaderdb.find():
        uploader_id = user.get("user_id")
        first_name = user.get("first_name", "Unknown")
        if uploader_id:
            uploader_buttons.append(IKB(capsify(first_name), user_id=uploader_id))

    rows = [uploader_buttons[i:i+3] for i in range(0, min(len(uploader_buttons), 12), 3)]
    await callback_query.edit_message_text(
        text=capsify("**Uploaders:**"),
        reply_markup=IKM(rows + [[IKB(capsify("Back"), callback_data="credits")]])
    )

@app.on_callback_query(filters.regex("main"))
async def main(_, callback_query):
    random_video = random.choice(PHOTO_URL)
    await callback_query.edit_message_text(
        text=capsify(start_text),
        reply_markup=IKM(support_buttons)
    )