import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Bot tokeni
TOKEN = "8872988314:AAGkQS8PDLkR9qfLlz3EYPBbOt2IBjUwKAY"

# Render avtomatik beradigan URL yoki o'zingizning veb-server manzilingiz
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://sizning-domen.onrender.com")
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.environ.get("PORT", 8080))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class RegState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_full_name = State()
    ready_for_test = State()

QUESTIONS = [
    {
        "text": "1. O‘zbekiston Respublikasi Konstitutsiyasi qanday yuridik kuchga ega?",
        "options": ["A) Oddiy qonun bilan teng kuchga ega", "B) Oliy yuridik kuchga ega", "C) Faqat davlat organlari uchun majburiy"],
        "correct": "B"
    },
    {
        "text": "2. O‘zbekistonda qonun chiqaruvchi oliy vakillik organi qaysi?",
        "options": ["A) Vazirlar Mahkamasi", "B) Oliy sud", "C) Oliy Majlis"],
        "correct": "C"
    },
    {
        "text": "3. Aybsizlik prezumpsiyasi nimani anglatadi?",
        "options": ["A) Aybi qonuniy tartibda isbotlanmaguncha shaxs aybsiz hisoblanadi", "B) Gumon qilingan shaxs darhol aybdor hisoblanadi", "C) Har qanday gumon qilingan shaxs jazolanadi"],
        "correct": "A"
    },
    {
        "text": "4. O‘zbekistonda davlat hokimiyati nechta asosiy tarmoqqa bo‘linadi?",
        "options": ["A) Ikki", "B) Uch", "C) To‘rt"],
        "correct": "B"
    },
    {
        "text": "5. Inson huquqlari kimlarga tegishli?",
        "options": ["A) Faqat davlat fuqarolariga", "B) Faqat voyaga yetgan shaxslarga", "C) Har bir insonga"],
        "correct": "C"
    },
    {
        "text": "6. O‘zbekiston Respublikasi Oliy Majlisi nechta palatadan iborat?",
        "options": ["A) Ikki palatadan", "B) Bir palatadan", "C) Uch palatadan"],
        "correct": "A"
    },
    {
        "text": "7. Sud hokimiyatining asosiy vazifasi nima?",
        "options": ["A) Qonunlarni qabul qilish", "B) Odil sudlovni amalga oshirish", "C) Davlat budjetini tasdiqlash"],
        "correct": "B"
    },
    {
        "text": "8. Qonunni bilmaslik javobgarlikdan ozod qiladimi?",
        "options": ["A) Ha, har doim", "B) Faqat voyaga yetganlarni ozod qiladi", "C) Yo‘q, o‘z-o‘zidan javobgarlikdan ozod qilmaydi"],
        "correct": "C"
    },
    {
        "text": "9. Zaruriy mudofaa qachon qo‘llanadi?",
        "options": ["A) Ijtimoiy xavfli tajovuzdan himoyalanishda", "B) Qasos olish maqsadida", "C) Har qanday kelishmovchilikda"],
        "correct": "A"
    },
    {
        "text": "10. Konstitutsiya va oddiy qonun o‘rtasida ziddiyat bo‘lsa, qaysi biri ustun?",
        "options": ["A) Oddiy qonun", "B) Konstitutsiya", "C) Mahalliy hokim qarori"],
        "correct": "B"
    },
    {
        "text": "11. Voyaga yetmagan shaxs deganda kim tushuniladi?",
        "options": ["A) 21 yoshga to‘lmagan har qanday shaxs", "B) 16 yoshga to‘lmagan shaxs", "C) 18 yoshga to‘lmagan shaxs"],
        "correct": "C"
    },
    {
        "text": "12. Fuqaro buzilgan huquqlarini himoya qilish uchun qayerga murojaat qilishi mumkin?",
        "options": ["A) Sudga yoki vakolatli organlarga", "B) Faqat tanishlariga", "C) Hech qayerga murojaat qila olmaydi"],
        "correct": "A"
    },
    {
        "text": "13. O‘zbekistonning xalqaro shartnomasida qonundagidan boshqacha qoida belgilangan bo‘lsa, qaysi qoida qo‘llanadi?",
        "options": ["A) Faqat mahalliy qaror qoidasi", "B) Xalqaro shartnoma qoidasi", "C) Har doim eski qonun qoidasi"],
        "correct": "B"
    },
    {
        "text": "14. So‘z erkinligi mutlaq huquqmi?",
        "options": ["A) Ha, hech qachon cheklanmaydi", "B) Faqat davlat xizmatchilariga tegishli", "C) Yo‘q, qonuniy asoslarda cheklanishi mumkin"],
        "correct": "C"
    },
    {
        "text": "15. Ma’muriy huquq asosan qaysi munosabatlarni tartibga soladi?",
        "options": ["A) Davlat boshqaruvi bilan bog‘liq munosabatlarni", "B) Faqat meros taqsimotini", "C) Faqat oilaviy munosabatlarni"],
        "correct": "A"
    }
]

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    phone_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "Assalomu alaykum! Huquqiy bilimlar test botiga xush kelibsiz.\n\n"
        "Davom etish uchun pastdagi tugma orqali telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard
    )
    await state.set_state(RegState.waiting_for_phone)

@dp.message(RegState.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    
    await message.answer(
        "Raqamingiz qabul qilindi ✅\nEndi **Ism va Familiyangizni** kiriting",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    await state.set_state(RegState.waiting_for_full_name)

@dp.message(RegState.waiting_for_phone)
async def process_phone_invalid(message: types.Message):
    await message.answer("Iltimos, pastdagi **'📱 Telefon raqamni yuborish'** tugmasini bosing.")

@dp.message(RegState.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text.strip()
    await state.update_data(full_name=full_name)
    
    test_start_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⚖️ Huquq testini boshlash")]],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Rahmat, **{full_name}**!\nRo‘yxatdan o‘tish muvaffaqiyatli yakunlandi.\n\n"
        f"Testni boshlash uchun pastdagi **'⚖️ Huquq testini boshlash'** tugmasini bosing.",
        reply_markup=test_start_keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(RegState.ready_for_test)

@dp.message(RegState.ready_for_test, F.text == "⚖️ Huquq testini boshlash")
@dp.message(F.text == "⚖️ Huquq testini boshlash")
async def start_quiz(message: types.Message, state: FSMContext):
    await state.update_data(q_index=0, score=0)
    await send_question(message, 0)

async def send_question(message_or_call, q_index: int):
    q = QUESTIONS[q_index]
    keyboard = []
    letters = ["A", "B", "C"]
    for i, opt in enumerate(q["options"]):
        keyboard.append([InlineKeyboardButton(text=opt, callback_data=f"ans_{q_index}_{letters[i]}")])
        
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    text = f"**Savol {q_index + 1}/{len(QUESTIONS)}**\n\n{q['text']}"
    
    if isinstance(message_or_call, types.Message):
        await message_or_call.answer(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await message_or_call.message.answer(text, reply_markup=markup, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("ans_"))
async def handle_answer(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_q_index = data.get("q_index", 0)
    score = data.get("score", 0)
    
    _, q_idx, user_ans = call.data.split("_")
    q_idx = int(q_idx)
    
    if q_idx != current_q_index:
        await call.answer("Siz bu savolga javob bergansiz!", show_alert=True)
        return
    
    q = QUESTIONS[q_idx]
    correct_ans = q["correct"]
    
    if user_ans == correct_ans:
        score += 1
        res_text = f"✅ **To‘g‘ri!** Javobingiz: {user_ans}"
    else:
        res_text = f"❌ **Noto‘g‘ri!** Sizning javobingiz: {user_ans}\nTo‘g‘ri javob: **{correct_ans}**"
    
    await call.message.edit_text(
        f"{q['text']}\n\n{res_text}",
        parse_mode="Markdown"
    )
    
    next_index = current_q_index + 1
    await state.update_data(q_index=next_index, score=score)
    
    if next_index < len(QUESTIONS):
        await send_question(call, next_index)
    else:
        user_data = await state.get_data()
        full_name = user_data.get("full_name", "Foydalanuvchi")
        phone = user_data.get("phone", "Ko'rsatilmadi")
        
        restart_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⚖️ Huquq testini boshlash")]],
            resize_keyboard=True
        )
        
        await call.message.answer(
            f"🎉 **Test yakunlandi!**\n\n"
            f"👤 **Ism Familiya:** {full_name}\n"
            f"📱 **Telefon:** {phone}\n"
            f"📊 **Natija:** {score} / {len(QUESTIONS)} ta to‘g‘ri javob!",
            reply_markup=restart_keyboard,
            parse_mode="Markdown"
        )

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook o'rnatildi: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("Webhook o'chirildi")

def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    main()
