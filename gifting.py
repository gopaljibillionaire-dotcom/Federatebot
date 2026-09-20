import asyncio
import logging
import dns.resolver

# --- FIX FOR PYDROID 3 / ANDROID DNS RESOLVER ISSUE ---
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)
from motor.motor_asyncio import AsyncIOMotorClient

# --- CONFIGURATION ---
BOT_TOKEN = "8739157428:AAGOkc7biRMGeyqSP5YxbiZf5_GBY5MZGvg"
MONGO_URI = "mongodb+srv://mahakalnaturalresourcespvtltd_db_user:OdzMVa8BxBGXf2eT@cluster0.hvxg8tb.mongodb.net/?appName=Cluster0"

# Image URLs (Replace these with your actual image URLs or Telegram File IDs)
WELCOME_IMAGE = "https://picsum.photos/800/400?text=Welcome+to+Fedarate"
BUY_PREMIUM_IMAGE = "https://picsum.photos/800/400?text=Buy+Premium"

# MongoDB Setup
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["fedarate_bot"]
users_collection = db["users"]

# Aiogram Initialization
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# --- KEYBOARDS ---


# Main Menu UI Keyboard
def get_main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Buy Premium", callback_data="ui_buy_premium"
                ),
                InlineKeyboardButton(
                    text="Buy boosts", callback_data="btn_buy_boosts"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Buy Stars", callback_data="btn_buy_stars"
                ),
                InlineKeyboardButton(
                    text="Sell Stars", callback_data="btn_sell_stars"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Profile/Stats", callback_data="btn_profile"
                ),
                InlineKeyboardButton(
                    text="Wallet",
                    callback_data="btn_wallet",
                    style="success",  # Green button
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Host a Giveaway", callback_data="btn_giveaway"
                )
            ],
            [InlineKeyboardButton(text="More", callback_data="btn_more")],
            [
                InlineKeyboardButton(
                    text="Settings", callback_data="btn_settings"
                ),
                InlineKeyboardButton(
                    text="Support", callback_data="btn_support"
                ),
            ],
        ]
    )


# Buy Premium UI Keyboard
def get_premium_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Deposit Funds",
                    callback_data="btn_deposit",
                    style="success",  # Green button
                )
            ],
            [
                InlineKeyboardButton(
                    text="Buy for myself", callback_data="btn_buy_self"
                ),
                InlineKeyboardButton(
                    text="Buy someone else", callback_data="btn_buy_other"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Contact Support", callback_data="btn_contact_support"
                )
            ],
            [
                # Full row red button for returning to the main menu
                InlineKeyboardButton(
                    text="Back to Main menu",
                    callback_data="ui_main_menu",
                    style="danger",  # Red button
                )
            ],
        ]
    )


# --- CAPTION TEXTS ---

MAIN_MENU_TEXT = (
    "<b>Welcome to Fedarate </b>\n\n"
    "<code> Total spends : $0\n"
    " Current balance : $10</code>\n\n"
    "<b>Please choose an option below :</b>"
)

PREMIUM_MENU_TEXT = (
    "<b>Wallet Balance : $10</b>\n"
    "<b>Product : Telegram Premium</b>\n\n"
    "<i>\"Upcoming #1 bot for telegram services.\"</i>\n\n"
    "<b>Select the options below to proceed further :</b>"
)


# --- HANDLERS ---


# Command /start handler -> Shows First UI
@dp.message(CommandStart())
async def cmd_start(message: Message):
    # Save user to MongoDB database safely
    try:
        user_data = {
            "user_id": message.from_user.id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
        }
        await users_collection.update_one(
            {"user_id": message.from_user.id}, {"$set": user_data}, upsert=True
        )
    except Exception as e:
        logging.error(f"MongoDB Update Failed: {e}")

    # Send Initial Main UI Message
    await message.answer_photo(
        photo=WELCOME_IMAGE,
        caption=MAIN_MENU_TEXT,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )


# Callback for 'Buy Premium' -> Edits existing message to show Second UI
@dp.callback_query(F.data == "ui_buy_premium")
async def show_buy_premium(callback: CallbackQuery):
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BUY_PREMIUM_IMAGE, caption=PREMIUM_MENU_TEXT, parse_mode="HTML"
        ),
        reply_markup=get_premium_keyboard(),
    )
    await callback.answer()


# Callback for 'Back to Main menu' -> Edits existing message back to First UI
@dp.callback_query(F.data == "ui_main_menu")
async def show_main_menu(callback: CallbackQuery):
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=WELCOME_IMAGE, caption=MAIN_MENU_TEXT, parse_mode="HTML"
        ),
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


# --- BOT RUNNER ---
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot is starting successfully...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
