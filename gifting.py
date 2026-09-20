import asyncio
import logging
import dns.resolver
import aiohttp

# --- FIX FOR PYDROID 3 / ANDROID DNS RESOLVER ISSUE ---
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from motor.motor_asyncio import AsyncIOMotorClient

# --- CONFIGURATION ---
BOT_TOKEN = "8739157428:AAGOkc7biRMGeyqSP5YxbiZf5_GBY5MZGvg"
MONGO_URI = "mongodb+srv://mahakalnaturalresourcespvtltd_db_user:OdzMVa8BxBGXf2eT@cluster0.hvxg8tb.mongodb.net/?appName=Cluster0"
OXAPAY_API_KEY = "YOUR_OXAPAY_API_KEY"

# --- IMGBB IMAGES ---
IMG_MAIN = "https://picsum.photos/800/400?text=Welcome+to+Fedarate"
IMG_PREMIUM = "https://i.ibb.co/6JHkSgfj/IMG-20260920-131952-198.jpg"
IMG_THANK_YOU = "https://i.ibb.co/mrSbwWjX/IMG-20260920-132011-139.jpg"
IMG_SUPPORT_US = "https://i.ibb.co/tpnPCqqS/IMG-20260920-132013-670.jpg"
IMG_STARS = "https://i.ibb.co/rfN5N5c9/IMG-20260920-132016-808.jpg"
IMG_CRYPTO = "https://i.ibb.co/Q7szPntS/IMG-20260920-132018-685.jpg"

# MongoDB Setup
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["fedarate_bot"]
users_collection = db["users"]

# Bot Setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# FSM States
class FormStates(StatesGroup):
    waiting_for_stars = State()
    waiting_for_crypto_dollars = State()


# --- MONGO DB HELPER FUNCTIONS ---
async def get_or_create_user(user):
    user_id = user.id
    user_data = await users_collection.find_one({"user_id": user_id})

    if not user_data:
        user_data = {
            "user_id": user_id,
            "username": user.username or "N/A",
            "first_name": user.first_name or "User",
            "balance": 10.0,
            "total_spends": 0.0,
        }
        await users_collection.insert_one(user_data)
    else:
        updates = {}
        if "balance" not in user_data:
            user_data["balance"] = 10.0
            updates["balance"] = 10.0
        if "total_spends" not in user_data:
            user_data["total_spends"] = 0.0
            updates["total_spends"] = 0.0

        if updates:
            await users_collection.update_one(
                {"user_id": user_id}, {"$set": updates}
            )

    return user_data


async def update_balance_and_spends(user_id: int, deduct_amount: float):
    await users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": -deduct_amount, "total_spends": deduct_amount}},
    )


async def create_oxapay_invoice(amount: float, order_id: str, description: str):
    url = "https://api.oxapay.com/merchants/request"
    payload = {
        "merchant": OXAPAY_API_KEY,
        "amount": amount,
        "currency": "USD",
        "lifeTime": 30,
        "feePaidByUser": 0,
        "orderId": order_id,
        "description": description,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("result") == 100:
                    return data.get("payLink")
    except Exception as e:
        logging.error(f"OxaPay API error: {e}")
    return "https://oxapay.com/pay/example"


# --- KEYBOARDS ---
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
                    text="Wallet", callback_data="btn_wallet", style="success"
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


def get_premium_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Deposit Funds",
                    callback_data="btn_deposit",
                    style="success",
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
                InlineKeyboardButton(
                    text="Back to Main menu",
                    callback_data="ui_main_menu",
                    style="danger",
                )
            ],
        ]
    )


def get_duration_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="3 months - $11.99", callback_data="dur_3_11.99"
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 months - $15.99", callback_data="dur_6_15.99"
                )
            ],
            [
                InlineKeyboardButton(
                    text="12 months - $28.99", callback_data="dur_12_28.99"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Change Recipient", callback_data="btn_buy_other"
                ),
                InlineKeyboardButton(
                    text="Contact Support", callback_data="btn_contact_support"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Return to Main Menu", callback_data="ui_main_menu"
                )
            ],
        ]
    )


def get_payment_keyboard(pay_url: str, plan_type: str, amount: float):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Pay Now", url=pay_url, style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Deduct from wallet balance",
                    callback_data=f"deduct_{plan_type}_{amount}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Change Recipient", callback_data="btn_buy_other"
                ),
                InlineKeyboardButton(
                    text="Contact Support", callback_data="btn_contact_support"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Back to Main Menu", callback_data="ui_main_menu"
                )
            ],
        ]
    )


def get_thankyou_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Support us", callback_data="btn_support_us"
                ),
                InlineKeyboardButton(
                    text="Contact Support",
                    callback_data="btn_contact_support",
                    style="success",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Return to Main Menu", callback_data="ui_main_menu"
                )
            ],
        ]
    )


def get_support_us_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Telegram Stars", callback_data="btn_donate_stars"
                ),
                InlineKeyboardButton(
                    text="Crypto Currency", callback_data="btn_donate_crypto"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Return to Main Menu", callback_data="ui_main_menu"
                )
            ],
        ]
    )


# --- HANDLERS ---


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_data = await get_or_create_user(message.from_user)
    caption = (
        "<b>Welcome to Fedarate  </b>\n\n"
        f"<code>  Total spends : ${user_data.get('total_spends', 0.0):.2f}\n"
        f"  Current balance : ${user_data.get('balance', 0.0):.2f}</code>\n\n"
        "<b>Please choose an option below :</b>"
    )
    await message.answer_photo(
        photo=IMG_MAIN,
        caption=caption,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )


@dp.callback_query(F.data == "ui_main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_data = await get_or_create_user(callback.from_user)
    caption = (
        "<b>Welcome to Fedarate  </b>\n\n"
        f"<code>  Total spends : ${user_data.get('total_spends', 0.0):.2f}\n"
        f"  Current balance : ${user_data.get('balance', 0.0):.2f}</code>\n\n"
        "<b>Please choose an option below :</b>"
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_MAIN, caption=caption, parse_mode="HTML"
        ),
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "ui_buy_premium")
async def show_buy_premium(callback: CallbackQuery):
    user_data = await get_or_create_user(callback.from_user)
    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n"
        "<b>Product : Telegram Premium</b>\n\n"
        '<i>"Upcoming #1 bot for telegram services."</i>\n\n'
        "<b>Select the options below to proceed further :</b>"
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_PREMIUM, caption=caption, parse_mode="HTML"
        ),
        reply_markup=get_premium_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "btn_buy_self")
async def buy_for_self(callback: CallbackQuery):
    user_data = await get_or_create_user(callback.from_user)
    recipient = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else callback.from_user.first_name
    )

    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n"
        f"<b>Product : Telegram Premium Recipient : {recipient}</b>\n\n"
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>\n\n"
        "<b>Please select the number of months you'd like to purchase.</b>"
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_PREMIUM, caption=caption, parse_mode="HTML"
        ),
        reply_markup=get_duration_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("dur_"))
async def process_duration_selection(callback: CallbackQuery):
    _, months, price_str = callback.data.split("_")
    amount = float(price_str)
    recipient = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else callback.from_user.first_name
    )

    pay_url = await create_oxapay_invoice(
        amount, f"prem_{callback.from_user.id}", "Telegram Premium Purchase"
    )

    caption = (
        "<b>Product : Telegram Premium</b>\n"
        f"<b>Recipient : {recipient}</b>\n"
        f"<b>Plan Duration : {months} Months</b>\n"
        f"<b>Total bill amount : ${amount}</b>\n\n"
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>\n\n"
        "Click <b>Pay Now</b> below to access the secure OxaPay payment page and complete your payment using any supported cryptocurrency. Once your payment is confirmed, your product will be delivered shortly."
    )

    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_PREMIUM, caption=caption, parse_mode="HTML"
        ),
        reply_markup=get_payment_keyboard(pay_url, "premium", amount),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("deduct_"))
async def process_wallet_deduction(callback: CallbackQuery):
    _, item_type, amount_str = callback.data.split("_")
    amount = float(amount_str)
    user_data = await get_or_create_user(callback.from_user)

    current_balance = user_data.get("balance", 0.0)
    if current_balance >= amount:
        await update_balance_and_spends(callback.from_user.id, amount)

        await callback.message.answer(
            "Undergoing a security check, Once it is confirmed, Your product will be delivered"
        )

        await asyncio.sleep(2)

        thankyou_caption = (
            "<b>Your order has been successfully delivered, Thank you for trusting @Fedaratebot and contributing in making it,</b>\n\n"
            "<blockquote>Upcoming #1 bot for telegram services.</blockquote>"
        )
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=IMG_THANK_YOU,
                caption=thankyou_caption,
                parse_mode="HTML",
            ),
            reply_markup=get_thankyou_keyboard(),
        )
    else:
        await callback.answer(
            f"Insufficient balance! You need ${amount:.2f}, but have ${current_balance:.2f}.",
            show_alert=True,
        )


@dp.callback_query(F.data == "btn_profile")
async def show_profile_stats(callback: CallbackQuery):
    user_data = await get_or_create_user(callback.from_user)
    profile_text = (
        "<b>User Profile & Stats</b>\n\n"
        f"<b>User ID:</b> <code>{user_data.get('user_id')}</code>\n"
        f"<b>Username:</b> @{user_data.get('username', 'N/A')}\n"
        f"<b>Current Balance:</b> ${user_data.get('balance', 0.0):.2f}\n"
        f"<b>Total Spending:</b> ${user_data.get('total_spends', 0.0):.2f}"
    )
    await callback.answer(profile_text, show_alert=True)


@dp.callback_query(F.data == "btn_support_us")
async def show_support_us(callback: CallbackQuery):
    caption = (
        "<b>Enjoying our services ? Your support helps us improve the bot, introduce new features, and deliver a better experience.</b>\n\n"
        "<b>Every contribution is greatly appreciated. Thank you for being part of our journey, You can support us by donating some telegram stars or crypto.</b>\n\n"
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>"
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_SUPPORT_US, caption=caption, parse_mode="HTML"
        ),
        reply_markup=get_support_us_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "btn_donate_stars")
async def ask_stars_amount(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FormStates.waiting_for_stars)
    caption = (
        "Please send the number of stars you are willing to donate\n"
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>"
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_STARS, caption=caption, parse_mode="HTML"
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Back to Main menu", callback_data="ui_main_menu"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@dp.message(FormStates.waiting_for_stars)
async def process_stars_input(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "Please enter a valid numeric value for XTR stars."
        )
        return

    num_stars = int(message.text)
    await state.clear()

    prices = [LabeledPrice(label="Donation Stars", amount=num_stars)]
    await message.answer_invoice(
        title="Donate Stars to Support Us",
        description=f"Donating {num_stars} Telegram Stars to Fedarate",
        prices=prices,
        provider_token="",
        currency="XTR",
        payload=f"stars_donation_{num_stars}",
    )


@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    await message.answer(
        "Project - #3 - Fedarate:\n"
        "Your transaction has been detected, Your product will be delivered after the transaction is fully confirmed on-chain undergoing security checks."
    )
    await asyncio.sleep(2)

    thankyou_caption = (
        "<b>Your donation has been confirmed! Thank you for trusting @Fedaratebot and contributing in making it,</b>\n\n"
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>"
    )
    await message.answer_photo(
        photo=IMG_THANK_YOU,
        caption=thankyou_caption,
        parse_mode="HTML",
        reply_markup=get_thankyou_keyboard(),
    )


@dp.callback_query(F.data == "btn_donate_crypto")
async def ask_crypto_dollars(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FormStates.waiting_for_crypto_dollars)
    user_data = await get_or_create_user(callback.from_user)
    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n"
        "<b>Amount of $ to donate :</b>\n\n"
        "<i>Please enter the dollar amount you would like to donate in chat:</i>\n\n"
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>"
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_CRYPTO, caption=caption, parse_mode="HTML"
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Return to Main Menu", callback_data="ui_main_menu"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@dp.message(FormStates.waiting_for_crypto_dollars)
async def process_crypto_dollar_input(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Please enter a valid dollar amount (e.g. 20).")
        return

    await state.clear()
    user_data = await get_or_create_user(message.from_user)
    pay_url = await create_oxapay_invoice(
        amount, f"donate_{message.from_user.id}", "Crypto Donation"
    )

    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n"
        f"<b>Amount of $ to donate : {amount}</b>\n\n"
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>"
    )

    await message.answer_photo(
        photo=IMG_CRYPTO,
        caption=caption,
        parse_mode="HTML",
        reply_markup=get_payment_keyboard(pay_url, "donate", amount),
    )


# --- BOT RUNNER ---
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot started successfully!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
