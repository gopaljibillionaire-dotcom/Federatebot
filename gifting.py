import asyncio
import datetime
import logging
import random
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
BOT_TOKEN = "8739157428:AAE63N1UIMGJO3B-uD12g3Gx52b6-ejUty4[span_3](start_span)"[span_3](end_span)
MONGO_URI = "mongodb+srv://mahakalnaturalresourcespvtltd_db_user:OdzMVa8BxBGXf2eT@cluster0.hvxg8tb.mongodb.net/?appName=Cluster0[span_4](start_span)"[span_4](end_span)
OXAPAY_API_KEY = "CNSQNK-D58COJ-UTTMFV-GOTYR5"

# --- IMGBB IMAGES ---
IMG_MAIN = "https://picsum.photos/800/400?text=Welcome+to+Fedarate[span_5](start_span)"[span_5](end_span)
IMG_PREMIUM = "https://i.ibb.co/6JHkSgfj/IMG-20260920-131952-198.jpg[span_6](start_span)"[span_6](end_span)
IMG_THANK_YOU = "https://i.ibb.co/mrSbwWjX/IMG-20260920-132011-139.jpg[span_7](start_span)"[span_7](end_span)
IMG_SUPPORT_US = "https://i.ibb.co/tpnPCqqS/IMG-20260920-132013-670.jpg[span_8](start_span)"[span_8](end_span)
IMG_STARS = "https://i.ibb.co/rfN5N5c9/IMG-20260920-132016-808.jpg[span_9](start_span)"[span_9](end_span)
IMG_CRYPTO = "https://i.ibb.co/Q7szPntS/IMG-20260920-132018-685.jpg[span_10](start_span)"[span_10](end_span)
IMG_WEEKLY_CASE = "https://i.ibb.co/example/weekly_case_photo.jpg[span_11](start_span)"[span_11](end_span)

# MongoDB Setup
mongo_client = AsyncIOMotorClient(MONGO_URI)[span_12](start_span)[span_12](end_span)
db = mongo_client["fedarate_bot"][span_13](start_span)[span_13](end_span)
users_collection = db["users"][span_14](start_span)[span_14](end_span)

# Bot Setup
bot = Bot(token=BOT_TOKEN)[span_15](start_span)[span_15](end_span)
dp = Dispatcher(storage=MemoryStorage())[span_16](start_span)[span_16](end_span)

# FSM States
class FormStates(StatesGroup):
    waiting_for_stars = State()[span_17](start_span)[span_17](end_span)
    waiting_for_crypto_dollars = State()[span_18](start_span)[span_18](end_span)
    waiting_for_deposit_amount = State()

# --- MONGO DB HELPER FUNCTIONS ---
async def get_or_create_user(user):
    user_id = user.id[span_19](start_span)[span_19](end_span)
    user_data = await users_collection.find_one({"user_id": user_id})[span_20](start_span)[span_20](end_span)
    if not user_data:
        user_data = {
            "user_id": user_id,[span_21](start_span)[span_21](end_span)
            "username": user.username or "N/A",[span_22](start_span)[span_22](end_span)
            "first_name": user.first_name or "User",[span_23](start_span)[span_23](end_span)
            "balance": 0.0,  # Starting balance is 0.00 until added
            "total_spends": 0.0,[span_24](start_span)[span_24](end_span)
            "weekly_spends": 0.0,[span_25](start_span)[span_25](end_span)
        }
        await users_collection.insert_one(user_data)[span_26](start_span)[span_26](end_span)
    else:
        updates = {}
        if "balance" not in user_data:
            user_data["balance"] = 0.0
            updates["balance"] = 0.0
        if "total_spends" not in user_data:
            user_data["total_spends"] = 0.0[span_27](start_span)[span_27](end_span)
            updates["total_spends"] = 0.0[span_28](start_span)[span_28](end_span)
        if "weekly_spends" not in user_data:
            user_data["weekly_spends"] = 0.0[span_29](start_span)[span_29](end_span)
            updates["weekly_spends"] = 0.0[span_30](start_span)[span_30](end_span)
        if updates:
            await users_collection.update_one(
                {"user_id": user_id}, {"$set": updates}[span_31](start_span)[span_31](end_span)
            )
    return user_data[span_32](start_span)[span_32](end_span)

async def update_balance_and_spends(user_id: int, deduct_amount: float):
    await users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": -deduct_amount, "total_spends": deduct_amount, "weekly_spends": deduct_amount}},[span_33](start_span)[span_33](end_span)
    )

async def create_oxapay_invoice(amount: float, order_id: str, description: str, lifetime_mins: int = 15):
    url = "https://api.oxapay.com/merchants/request[span_34](start_span)"[span_34](end_span)
    payload = {
        "merchant": OXAPAY_API_KEY,
        "amount": amount,[span_35](start_span)[span_35](end_span)
        "currency": "USD",[span_36](start_span)[span_36](end_span)
        "lifeTime": lifetime_mins,  # Set receipt/payment window (15 minutes default)
        "feePaidByUser": 0,[span_37](start_span)[span_37](end_span)
        "orderId": order_id,[span_38](start_span)[span_38](end_span)
        "description": description,[span_39](start_span)[span_39](end_span)
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("result") == 100:[span_40](start_span)[span_40](end_span)
                    return data.get("payLink")[span_41](start_span)[span_41](end_span)
    except Exception as e:
        logging.error(f"OxaPay API error: {e}")[span_42](start_span)[span_42](end_span)
    return f"https://oxapay.com/pay/{OXAPAY_API_KEY}"

# --- KEYBOARDS ---
def get_main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Buy Premium", callback_data="ui_buy_premium[span_43](start_span)"[span_43](end_span)
                ),
                InlineKeyboardButton(
                    text="Buy boosts", callback_data="btn_buy_boosts[span_44](start_span)"[span_44](end_span)
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Buy Stars", callback_data="btn_buy_stars[span_45](start_span)"[span_45](end_span)
                ),
                InlineKeyboardButton(
                    text="Sell Stars", callback_data="btn_sell_stars[span_46](start_span)"[span_46](end_span)
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Profile/Stats", callback_data="btn_profile[span_47](start_span)"[span_47](end_span)
                ),
                InlineKeyboardButton(
                    text="Wallet", callback_data="btn_wallet", style="success[span_48](start_span)"[span_48](end_span)
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Host a Giveaway", callback_data="btn_giveaway[span_49](start_span)"[span_49](end_span)
                )
            ],
            [InlineKeyboardButton(text="More", callback_data="btn_more")],[span_50](start_span)[span_50](end_span)
            [
                InlineKeyboardButton(
                    text="Settings", callback_data="btn_settings[span_51](start_span)"[span_51](end_span)
                ),
                InlineKeyboardButton(
                    text="Support", callback_data="btn_support[span_52](start_span)"[span_52](end_span)
                ),
            ],
        ]
    )

def get_more_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Weekly Cases", callback_data="btn_weekly_cases[span_53](start_span)"[span_53](end_span)
                )
            ],
            [
                InlineKeyboardButton(
                    text="Back to Main menu",[span_54](start_span)[span_54](end_span)
                    callback_data="ui_main_menu",[span_55](start_span)[span_55](end_span)
                    style="danger",[span_56](start_span)[span_56](end_span)
                )
            ],
        ]
    )

def get_cases_grid_keyboard(opened_index=None, revealed=False):
    rewards = ["6 Stars", "15 Stars", "25 Stars", "1 Month TG Premium", "Better Luck Next Time"][span_57](start_span)[span_57](end_span)
    keyboard = [][span_58](start_span)[span_58](end_span)
    row = [][span_59](start_span)[span_59](end_span)
    for i in range(1, 7):[span_60](start_span)[span_60](end_span)
        if not revealed:[span_61](start_span)[span_61](end_span)
            btn_text = "🎁[span_62](start_span)"[span_62](end_span)
            style = "success[span_63](start_span)"[span_63](end_span)
        else:
            if i == opened_index:[span_64](start_span)[span_64](end_span)
                btn_text = "Better Luck Next Time[span_65](start_span)"[span_65](end_span)
            else:
                btn_text = random.choice(["6 Stars", "15 Stars", "25 Stars", "1 Month TG Premium"])[span_66](start_span)[span_66](end_span)
            style = "danger[span_67](start_span)"[span_67](end_span)
                    
        row.append([span_68](start_span)[span_68](end_span)
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"open_case_{i}" if not revealed else "case_opened_already",[span_69](start_span)[span_69](end_span)
                style=style[span_70](start_span)[span_70](end_span)
            )
        )
        if len(row) == 3:[span_71](start_span)[span_71](end_span)
            keyboard.append(row)[span_72](start_span)[span_72](end_span)
            row = [][span_73](start_span)[span_73](end_span)
                
    keyboard.append([span_74](start_span)[span_74](end_span)
        [
            InlineKeyboardButton(
                text="Back to Main menu",[span_75](start_span)[span_75](end_span)
                callback_data="ui_main_menu",[span_76](start_span)[span_76](end_span)
                style="danger",[span_77](start_span)[span_77](end_span)
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)[span_78](start_span)[span_78](end_span)

def get_premium_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Deposit Funds",[span_79](start_span)[span_79](end_span)
                    callback_data="btn_wallet",[span_80](start_span)[span_80](end_span)
                    style="success",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Buy for myself", callback_data="btn_buy_self[span_81](start_span)"[span_81](end_span)
                ),
                InlineKeyboardButton(
                    text="Buy someone else", callback_data="btn_buy_other[span_82](start_span)"[span_82](end_span)
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Contact Support", callback_data="btn_contact_support[span_83](start_span)"[span_83](end_span)
                )
            ],
            [
                InlineKeyboardButton(
                    text="Back to Main menu",[span_84](start_span)[span_84](end_span)
                    callback_data="ui_main_menu",[span_85](start_span)[span_85](end_span)
                    style="danger",[span_86](start_span)[span_86](end_span)
                )
            ],
        ]
    )

def get_duration_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="3 months - $11.99", callback_data="dur_3_11.99[span_87](start_span)"[span_87](end_span)
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 months - $15.99", callback_data="dur_6_15.99[span_88](start_span)"[span_88](end_span)
                )
            ],
            [
                InlineKeyboardButton(
                    text="12 months - $28.99", callback_data="dur_12_28.99[span_89](start_span)"[span_89](end_span)
                )
            ],
            [
                InlineKeyboardButton(
                    text="Change Recipient", callback_data="btn_buy_other[span_90](start_span)"[span_90](end_span)
                ),
                InlineKeyboardButton(
                    text="Contact Support", callback_data="btn_contact_support[span_91](start_span)"[span_91](end_span)
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Return to Main Menu", callback_data="ui_main_menu[span_92](start_span)"[span_92](end_span)
                )
            ],
        ]
    )

def get_wallet_keyboard(pay_url: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Use another crypto currency", url=pay_url, style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Back to Main Menu", callback_data="ui_main_menu", style="danger"
                )
            ],
        ]
    )

def get_payment_keyboard(pay_url: str, plan_type: str, amount: float):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Pay Now", url=pay_url, style="success[span_93](start_span)"[span_93](end_span)
                )
            ],
            [
                InlineKeyboardButton(
                    text="Deduct from wallet balance",[span_94](start_span)[span_94](end_span)
                    callback_data=f"deduct_{plan_type}_{amount}",[span_95](start_span)[span_95](end_span)
                )
            ],
            [
                InlineKeyboardButton(
                    text="Change Recipient", callback_data="btn_buy_other[span_96](start_span)"[span_96](end_span)
                ),
                InlineKeyboardButton(
                    text="Contact Support", callback_data="btn_contact_support[span_97](start_span)"[span_97](end_span)
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Back to Main Menu", callback_data="ui_main_menu[span_98](start_span)"[span_98](end_span)
                )
            ],
        ]
    )

def get_thankyou_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Support us", callback_data="btn_support_us[span_99](start_span)"[span_99](end_span)
                ),
                InlineKeyboardButton(
                    text="Contact Support",[span_100](start_span)[span_100](end_span)
                    callback_data="btn_contact_support",[span_101](start_span)[span_101](end_span)
                    style="success",[span_102](start_span)[span_102](end_span)
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Return to Main Menu", callback_data="ui_main_menu[span_103](start_span)"[span_103](end_span)
                )
            ],
        ]
    )

def get_support_us_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Telegram Stars", callback_data="btn_donate_stars[span_104](start_span)"[span_104](end_span)
                ),
                InlineKeyboardButton(
                    text="Crypto Currency", callback_data="btn_donate_crypto[span_105](start_span)"[span_105](end_span)
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Return to Main Menu", callback_data="ui_main_menu[span_106](start_span)"[span_106](end_span)
                )
            ],
        ]
    )

# --- HANDLERS ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_data = await get_or_create_user(message.from_user)[span_107](start_span)[span_107](end_span)
    caption = (
        "<b>Welcome to Fedarate  </b>\n\n[span_108](start_span)"[span_108](end_span)
        f"<code>  Total spends : ${user_data.get('total_spends', 0.0):.2f}\n[span_109](start_span)"[span_109](end_span)
        f"  Current balance : ${user_data.get('balance', 0.0):.2f}</code>\n\n[span_110](start_span)"[span_110](end_span)
        "<b>Please choose an option below :</b>[span_111](start_span)"[span_111](end_span)
    )
    await message.answer_photo(
        photo=IMG_MAIN,[span_112](start_span)[span_112](end_span)
        caption=caption,[span_113](start_span)[span_113](end_span)
        parse_mode="HTML",[span_114](start_span)[span_114](end_span)
        reply_markup=get_main_menu_keyboard(),[span_115](start_span)[span_115](end_span)
    )

@dp.callback_query(F.data == "btn_wallet")
async def show_wallet(callback: CallbackQuery):
    user_data = await get_or_create_user(callback.from_user)
    
    # Generate custom payment link via OxaPay for balance deposit
    pay_url = await create_oxapay_invoice(
        amount=10.0, 
        order_id=f"deposit_{callback.from_user.id}_{int(datetime.datetime.now().timestamp())}", 
        description="Wallet Balance Deposit",
        lifetime_mins=15
    )
    
    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n\n"
        "Add your balance via <b>USDT (BEP20), BNB, BTC, and LTC</b>.\n\n"
        "Click the button below to complete payment using your preferred cryptocurrency:"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_CRYPTO, caption=caption, parse_mode="HTML"
        ),
        reply_markup=get_wallet_keyboard(pay_url),
    )
    await callback.answer()

@dp.callback_query(F.data == "btn_more")
async def show_more_menu(callback: CallbackQuery):
    caption = "<b>More Options</b>\n\nSelect an option below:[span_116](start_span)"[span_116](end_span)
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_MAIN, caption=caption, parse_mode="HTML[span_117](start_span)"[span_117](end_span)
        ),
        reply_markup=get_more_menu_keyboard(),[span_118](start_span)[span_118](end_span)
    )
    await callback.answer()[span_119](start_span)[span_119](end_span)

@dp.callback_query(F.data == "btn_weekly_cases")
async def show_weekly_cases(callback: CallbackQuery):
    user_data = await get_or_create_user(callback.from_user)[span_120](start_span)[span_120](end_span)
    today = datetime.datetime.now().weekday()  # Sunday is 6[span_121](start_span)[span_121](end_span)
    is_sunday = (today == 6)[span_122](start_span)[span_122](end_span)
    weekly_spends = user_data.get("weekly_spends", 0.0)[span_123](start_span)[span_123](end_span)
    caption = (
        "<b>Weekly Cases for our bot users</b>\n\n[span_124](start_span)"[span_124](end_span)
        "We’re adding a small way to return some to the users who make purchases in @FedarateBot,\n\n[span_125](start_span)"[span_125](end_span)
        "Each week, customers who purchased Telegram Premium, Stars, Boosts, or Hosted a Pre-paid giveaways through @FedarateBot [span_126](start_span)"[span_126](end_span)
        "will be able to open 1 case every Sunday, The cases will contain gifts such as telegram premium, Stars - 25 to 5k, [span_127](start_span)"[span_127](end_span)
        "Boosts - 1 to 15, Telegram nfts and nothing (Better luck next time) Every purchase made during the week counts as an entry.\n\n[span_128](start_span)"[span_128](end_span)
        "Winner will be picked every Sunday\n\n[span_129](start_span)"[span_129](end_span)
        "We’re grateful for everyone who continues to use and trust our service, this is just a small way of giving back.[span_130](start_span)"[span_130](end_span)
    )
    if not is_sunday:[span_131](start_span)[span_131](end_span)
        await callback.answer("Please wait for Sunday to open cases!", show_alert=True)[span_132](start_span)[span_132](end_span)
        return
    if weekly_spends <= 0.0:[span_133](start_span)[span_133](end_span)
        await callback.answer("You haven't spent anything this week! Purchase services during the week to unlock Sunday cases.", show_alert=True)[span_134](start_span)[span_134](end_span)
        return
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_WEEKLY_CASE, caption=caption, parse_mode="HTML[span_135](start_span)"[span_135](end_span)
        ),
        reply_markup=get_cases_grid_keyboard(),[span_136](start_span)[span_136](end_span)
    )
    await callback.answer()[span_137](start_span)[span_137](end_span)

@dp.callback_query(F.data.startswith("open_case_"))
async def open_case(callback: CallbackQuery):
    case_idx = int(callback.data.split("_")[-1])[span_138](start_span)[span_138](end_span)
    new_keyboard = get_cases_grid_keyboard(opened_index=case_idx, revealed=True)[span_139](start_span)[span_139](end_span)
    caption = (
        "<b>Weekly Case Opened!</b>\n\n[span_140](start_span)"[span_140](end_span)
        "Better luck next time! Spend again during the week to try your luck next Sunday[span_141](start_span)!"[span_141](end_span)
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_WEEKLY_CASE, caption=caption, parse_mode="HTML[span_142](start_span)"[span_142](end_span)
        ),
        reply_markup=new_keyboard,[span_143](start_span)[span_143](end_span)
    )
    await callback.answer("Revealed! Better luck next time!", show_alert=True)[span_144](start_span)[span_144](end_span)

@dp.callback_query(F.data == "case_opened_already")
async def case_opened_already(callback: CallbackQuery):
    await callback.answer("You have already opened your case for this week!", show_alert=True)[span_145](start_span)[span_145](end_span)

@dp.callback_query(F.data == "ui_main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()[span_146](start_span)[span_146](end_span)
    user_data = await get_or_create_user(callback.from_user)[span_147](start_span)[span_147](end_span)
    caption = (
        "<b>Welcome to Fedarate  </b>\n\n[span_148](start_span)"[span_148](end_span)
        f"<code>  Total spends : ${user_data.get('total_spends', 0.0):.2f}\n[span_149](start_span)"[span_149](end_span)
        f"  Current balance : ${user_data.get('balance', 0.0):.2f}</code>\n\n[span_150](start_span)"[span_150](end_span)
        "<b>Please choose an option below :</b>[span_151](start_span)"[span_151](end_span)
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_MAIN, caption=caption, parse_mode="HTML[span_152](start_span)"[span_152](end_span)
        ),
        reply_markup=get_main_menu_keyboard(),[span_153](start_span)[span_153](end_span)
    )
    await callback.answer()[span_154](start_span)[span_154](end_span)

@dp.callback_query(F.data == "ui_buy_premium")
async def show_buy_premium(callback: CallbackQuery):
    user_data = await get_or_create_user(callback.from_user)[span_155](start_span)[span_155](end_span)
    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n[span_156](start_span)"[span_156](end_span)
        "<b>Product : Telegram Premium</b>\n\n[span_157](start_span)"[span_157](end_span)
        '<i>"Upcoming #1 bot for telegram services."</i>\n\n[span_158](start_span)'[span_158](end_span)
        "<b>Select the options below to proceed further :</b>[span_159](start_span)"[span_159](end_span)
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_PREMIUM, caption=caption, parse_mode="HTML[span_160](start_span)"[span_160](end_span)
        ),
        reply_markup=get_premium_keyboard(),[span_161](start_span)[span_161](end_span)
    )
    await callback.answer()[span_162](start_span)[span_162](end_span)

@dp.callback_query(F.data == "btn_buy_self")
async def buy_for_self(callback: CallbackQuery):
    user_data = await get_or_create_user(callback.from_user)[span_163](start_span)[span_163](end_span)
    recipient = (
        f"@{callback.from_user.username}[span_164](start_span)"[span_164](end_span)
        if callback.from_user.username[span_165](start_span)[span_165](end_span)
        else callback.from_user.first_name[span_166](start_span)[span_166](end_span)
    )
    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n[span_167](start_span)"[span_167](end_span)
        f"<b>Product : Telegram Premium Recipient : {recipient}</b>\n\n[span_168](start_span)"[span_168](end_span)
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>\n\n[span_169](start_span)"[span_169](end_span)
        "<b>Please select the number of months you'd like to purchase.</b>[span_170](start_span)"[span_170](end_span)
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_PREMIUM, caption=caption, parse_mode="HTML[span_171](start_span)"[span_171](end_span)
        ),
        reply_markup=get_duration_keyboard(),[span_172](start_span)[span_172](end_span)
    )
    await callback.answer()[span_173](start_span)[span_173](end_span)

@dp.callback_query(F.data.startswith("dur_"))
async def process_duration_selection(callback: CallbackQuery):
    _, months, price_str = callback.data.split("_")[span_174](start_span)[span_174](end_span)
    amount = float(price_str)[span_175](start_span)[span_175](end_span)
    recipient = (
        f"@{callback.from_user.username}[span_176](start_span)"[span_176](end_span)
        if callback.from_user.username[span_177](start_span)[span_177](end_span)
        else callback.from_user.first_name[span_178](start_span)[span_178](end_span)
    )
    # Automatic 15-minute invoice creation
    pay_url = await create_oxapay_invoice(
        amount, f"prem_{callback.from_user.id}", f"Telegram Premium Purchase ({months}M)", lifetime_mins=15
    )
    caption = (
        "<b>Product : Telegram Premium</b>\n[span_179](start_span)"[span_179](end_span)
        f"<b>Recipient : {recipient}</b>\n[span_180](start_span)"[span_180](end_span)
        f"<b>Plan Duration : {months} Months</b>\n[span_181](start_span)"[span_181](end_span)
        f"<b>Total bill amount : ${amount}</b>\n\n[span_182](start_span)"[span_182](end_span)
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>\n\n[span_183](start_span)"[span_183](end_span)
        "Click <b>Pay Now</b> below to access your custom receipt and pay using your desired cryptocurrency. "
        "The invoice is valid for 15 minutes."
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_PREMIUM, caption=caption, parse_mode="HTML[span_184](start_span)"[span_184](end_span)
        ),
        reply_markup=get_payment_keyboard(pay_url, "premium", amount),[span_185](start_span)[span_185](end_span)
    )
    await callback.answer()[span_186](start_span)[span_186](end_span)

@dp.callback_query(F.data.startswith("deduct_"))
async def process_wallet_deduction(callback: CallbackQuery):
    _, item_type, amount_str = callback.data.split("_")[span_187](start_span)[span_187](end_span)
    amount = float(amount_str)[span_188](start_span)[span_188](end_span)
    user_data = await get_or_create_user(callback.from_user)[span_189](start_span)[span_189](end_span)
    current_balance = user_data.get("balance", 0.0)[span_190](start_span)[span_190](end_span)
    if current_balance >= amount:[span_191](start_span)[span_191](end_span)
        await update_balance_and_spends(callback.from_user.id, amount)[span_192](start_span)[span_192](end_span)
        await callback.message.answer(
            "Undergoing a security check, Once it is confirmed, Your product will be delivered[span_193](start_span)"[span_193](end_span)
        )
        await asyncio.sleep(2)[span_194](start_span)[span_194](end_span)
        thankyou_caption = (
            "<b>Your order has been successfully delivered, Thank you for trusting @Fedaratebot and contributing in making it,</b>\n\n[span_195](start_span)"[span_195](end_span)
            "<blockquote>Upcoming #1 bot for telegram services.</blockquote>[span_196](start_span)"[span_196](end_span)
        )
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=IMG_THANK_YOU,[span_197](start_span)[span_197](end_span)
                caption=thankyou_caption,[span_198](start_span)[span_198](end_span)
                parse_mode="HTML",[span_199](start_span)[span_199](end_span)
            ),
            reply_markup=get_thankyou_keyboard(),[span_200](start_span)[span_200](end_span)
        )
    else:
        await callback.answer(
            f"Insufficient balance! You need ${amount:.2f}, but have ${current_balance:.2f}.",[span_201](start_span)[span_201](end_span)
            show_alert=True,[span_202](start_span)[span_202](end_span)
        )

@dp.callback_query(F.data == "btn_profile")
async def show_profile_stats(callback: CallbackQuery):
    user_data = await get_or_create_user(callback.from_user)[span_203](start_span)[span_203](end_span)
    profile_text = (
        "<b>User Profile & Stats</b>\n\n[span_204](start_span)"[span_204](end_span)
        f"<b>User ID:</b> <code>{user_data.get('user_id')}</code>\n[span_205](start_span)"[span_205](end_span)
        f"<b>Username:</b> @{user_data.get('username', 'N/A')}\n[span_206](start_span)"[span_206](end_span)
        f"<b>Current Balance:</b> ${user_data.get('balance', 0.0):.2f}\n[span_207](start_span)"[span_207](end_span)
        f"<b>Total Spending:</b> ${user_data.get('total_spends', 0.0):.2f}\n[span_208](start_span)"[span_208](end_span)
        f"<b>Weekly Spending:</b> ${user_data.get('weekly_spends', 0.0):.2f}[span_209](start_span)"[span_209](end_span)
    )
    await callback.answer(profile_text, show_alert=True)[span_210](start_span)[span_210](end_span)

@dp.callback_query(F.data == "btn_support_us")
async def show_support_us(callback: CallbackQuery):
    caption = (
        "<b>Enjoying our services ? Your support helps us improve the bot, introduce new features, and deliver a better experience.</b>\n\n[span_211](start_span)"[span_211](end_span)
        "<b>Every contribution is greatly appreciated. Thank you for being part of our journey, You can support us by donating some telegram stars or crypto.</b>\n\n[span_212](start_span)"[span_212](end_span)
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>[span_213](start_span)"[span_213](end_span)
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_SUPPORT_US, caption=caption, parse_mode="HTML[span_214](start_span)"[span_214](end_span)
        ),
        reply_markup=get_support_us_keyboard(),[span_215](start_span)[span_215](end_span)
    )
    await callback.answer()[span_216](start_span)[span_216](end_span)

@dp.callback_query(F.data == "btn_donate_stars")
async def ask_stars_amount(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FormStates.waiting_for_stars)[span_217](start_span)[span_217](end_span)
    caption = (
        "Please send the number of stars you are willing to donate\n[span_218](start_span)"[span_218](end_span)
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>[span_219](start_span)"[span_219](end_span)
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_STARS, caption=caption, parse_mode="HTML[span_220](start_span)"[span_220](end_span)
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Back to Main menu", callback_data="ui_main_menu", style="danger[span_221](start_span)"[span_221](end_span)
                    )
                ]
            ]
        ),
    )
    await callback.answer()[span_222](start_span)[span_222](end_span)

@dp.message(FormStates.waiting_for_stars)
async def process_stars_input(message: Message, state: FSMContext):
    if not message.text.isdigit():[span_223](start_span)[span_223](end_span)
        await message.answer(
            "Please enter a valid numeric value for XTR stars.[span_224](start_span)"[span_224](end_span)
        )
        return
    num_stars = int(message.text)[span_225](start_span)[span_225](end_span)
    await state.clear()[span_226](start_span)[span_226](end_span)
    prices = [LabeledPrice(label="Donation Stars", amount=num_stars)][span_227](start_span)[span_227](end_span)
    await message.answer_invoice(
        title="Donate Stars to Support Us",[span_228](start_span)[span_228](end_span)
        description=f"Donating {num_stars} Telegram Stars to Fedarate",[span_229](start_span)[span_229](end_span)
        prices=prices,[span_230](start_span)[span_230](end_span)
        provider_token="",[span_231](start_span)[span_231](end_span)
        currency="XTR",[span_232](start_span)[span_232](end_span)
        payload=f"stars_donation_{num_stars}",[span_233](start_span)[span_233](end_span)
    )

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)[span_234](start_span)[span_234](end_span)

@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    await message.answer(
        "Project - #3 - Fedarate:\n[span_235](start_span)"[span_235](end_span)
        "Your transaction has been detected, Your product will be delivered after the transaction is fully confirmed on-chain undergoing security checks.[span_236](start_span)"[span_236](end_span)
    )
    await asyncio.sleep(2)[span_237](start_span)[span_237](end_span)
    thankyou_caption = (
        "<b>Your donation has been confirmed! Thank you for trusting @Fedaratebot and contributing in making it,</b>\n\n[span_238](start_span)"[span_238](end_span)
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>[span_239](start_span)"[span_239](end_span)
    )
    await message.answer_photo(
        photo=IMG_THANK_YOU,[span_240](start_span)[span_240](end_span)
        caption=thankyou_caption,[span_241](start_span)[span_241](end_span)
        parse_mode="HTML",[span_242](start_span)[span_242](end_span)
        reply_markup=get_thankyou_keyboard(),[span_243](start_span)[span_243](end_span)
    )

@dp.callback_query(F.data == "btn_donate_crypto")
async def ask_crypto_dollars(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FormStates.waiting_for_crypto_dollars)[span_244](start_span)[span_244](end_span)
    user_data = await get_or_create_user(callback.from_user)[span_245](start_span)[span_245](end_span)
    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n[span_246](start_span)"[span_246](end_span)
        "<b>Amount of $ to donate :</b>\n\n[span_247](start_span)"[span_247](end_span)
        "<i>Please enter the dollar amount you would like to donate in chat:</i>\n\n[span_248](start_span)"[span_248](end_span)
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>[span_249](start_span)"[span_249](end_span)
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=IMG_CRYPTO, caption=caption, parse_mode="HTML[span_250](start_span)"[span_250](end_span)
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Return to Main Menu", callback_data="ui_main_menu", style="danger[span_251](start_span)"[span_251](end_span)
                    )
                ]
            ]
        ),
    )
    await callback.answer()[span_252](start_span)[span_252](end_span)

@dp.message(FormStates.waiting_for_crypto_dollars)
async def process_crypto_dollar_input(message: Message, state: FSMContext):
    try:
        amount = float(message.text)[span_253](start_span)[span_253](end_span)
    except ValueError:
        await message.answer("Please enter a valid dollar amount (e.g. 20).")[span_254](start_span)[span_254](end_span)
        return
    await state.clear()[span_255](start_span)[span_255](end_span)
    user_data = await get_or_create_user(message.from_user)[span_256](start_span)[span_256](end_span)
    pay_url = await create_oxapay_invoice(
        amount, f"donate_{message.from_user.id}", "Crypto Donation", lifetime_mins=15
    )
    caption = (
        f"<b>Wallet Balance : ${user_data.get('balance', 0.0):.2f}</b>\n[span_257](start_span)"[span_257](end_span)
        f"<b>Amount of $ to donate : {amount}</b>\n\n[span_258](start_span)"[span_258](end_span)
        "<blockquote>Upcoming #1 bot for telegram services.</blockquote>[span_259](start_span)"[span_259](end_span)
    )
    await message.answer_photo(
        photo=IMG_CRYPTO,[span_260](start_span)[span_260](end_span)
        caption=caption,[span_261](start_span)[span_261](end_span)
        parse_mode="HTML",[span_262](start_span)[span_262](end_span)
        reply_markup=get_payment_keyboard(pay_url, "donate", amount),[span_263](start_span)[span_263](end_span)
    )

# --- BOT RUNNER ---
async def main():
    logging.basicConfig(level=logging.INFO)[span_264](start_span)[span_264](end_span)
    print("Bot started successfully!")[span_265](start_span)[span_265](end_span)
    await dp.start_polling(bot)[span_266](start_span)[span_266](end_span)

if __name__ == "__main__":
    asyncio.run(main())[span_267](start_span)[span_267](end_span)
