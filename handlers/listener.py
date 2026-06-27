import os
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db_manager

PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
router = Router()

class ListenerStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_application = State()

def get_listener_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📜 Расписание"), KeyboardButton(text="❓ Задать вопрос")],
            [KeyboardButton(text="❤️ Поддержать проект"), KeyboardButton(text="🎤 Меню Спикера")],
            [KeyboardButton(text="📢 Хочу стать спикером!")]
        ],
        resize_keyboard=True
    )

@router.message(CommandStart())
async def cmd_start(message: Message):
    db_manager.add_user(
        user_id=message.from_user.id,
        user_name=message.from_user.full_name,
        username=message.from_user.username
    )

    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋 Добро пожаловать на наше мероприятие.\n\n"
        f"С помощью этого бота вы можете:\n"
        f"📜 **Узнать расписание** — посмотреть программу мероприятия\n"
        f"❓ **Задать вопрос** — отправить вопрос спикеру на сцене\n"
        f"📢 **Стать спикером** — оставить заявку на выступление\n"
        f"🎤 **Меню Спикера** — открыть панель управления для докладчиков\n"
        f"❤ **Поддержать проект** — поддержать проект донатом\n\n"
        f"Используйте клавиатуру ниже для навигации по функциям!",
        parse_mode="Markdown",
        reply_markup=get_listener_keyboard()
    )

@router.message(F.text == "📜 Расписание")
async def show_schedule(message: Message):
    schedule_text = db_manager.get_schedule()
    await message.answer(schedule_text, parse_mode="Markdown")

@router.message(F.text == "❓ Задать вопрос")
async def ask_question_start(message: Message, state: FSMContext):
    current_speaker = db_manager.get_current_speaker_id()
    if not current_speaker:
        await message.answer("Сейчас на сцене никто не выступает. Вопрос задать некому.")
        return
        
    await message.answer("Напишите ваш вопрос для текущего спикера одним сообщением:")
    await state.set_state(ListenerStates.waiting_for_question)

@router.message(ListenerStates.waiting_for_question)
async def process_listener_question(message: Message, state: FSMContext):
    db_manager.add_question(
        user_id=message.from_user.id,
        user_name=message.from_user.full_name,
        text=message.text
    )
    await message.answer("✅ Ваш вопрос успешно отправлен спикеру!")
    await state.clear()

# 2. Хендлер нажатия на кнопку доната — отправляем инвойс
@router.message(F.text == "❤️ Поддержать проект")
async def send_donation_invoice(message: Message):
    await message.answer_invoice(
        title="Добровольное пожертвование",
        description="Поддержка организаторов и развития будущих мероприятий",
        payload="donation_payload",  # Внутренний идентификатор для вашей логики
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(label="Донат", amount=25000) # Цена в минимальных единицах валюты (25000 копеек = 250 рублей)
        ],
        start_parameter="donate",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        is_flexible=False # Фиксированная цена без выбора доставки
    )

# 3. ОБЯЗАТЕЛЬНЫЙ ХЕНДЛЕР: Ответ на предварительный запрос (PreCheckoutQuery)
# Telegram дает 10 секунд на проверку доступности товара перед списанием денег
@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Так как это донат, товар всегда "в наличии", сразу одобряем (ok=True)
    await pre_checkout_query.answer(ok=True)

# 4. Хендлер успешной оплаты
@router.message(F.successful_payment)
async def success_payment_handler(message: Message):
    payment_info = message.successful_payment
    # Переводим копейки обратно в рубли для записи
    rub_amount = payment_info.total_amount / 100 
    
    db_manager.log_donation(
        user_id=message.from_user.id,
        user_name=message.from_user.full_name,
        amount=rub_amount
    )
    
    await message.answer(
        f"🎉 Спасибо огромное, {message.from_user.first_name}!\n"
        f"Ваш донат в размере {rub_amount} руб. успешно получен. "
        f"Вы помогаете делать наши мероприятия лучше!"
    )

@router.message(F.text == "📢 Хочу стать спикером!")
async def submit_application(message: Message, state: FSMContext):   
    await message.answer("Напишите тему, с которой хотели бы выступить одним сообщением:")
    await state.set_state(ListenerStates.waiting_for_application)

@router.message(ListenerStates.waiting_for_application)
async def process_listener_application(message: Message, state: FSMContext):
    db_manager.add_application(
        user_id=message.from_user.id,
        user_name=message.from_user.full_name,
        text=message.text
    )
    await message.answer("✅ Ваша заявка успешно сохранена! С вами свяжется администратор")
    await state.clear()
