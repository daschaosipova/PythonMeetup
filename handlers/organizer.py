import os
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db_manager

ORGANIZER_ID = os.getenv("ORGANIZER_ID")
router = Router()


class OrganizerStates(StatesGroup):
    choosing_type = State()  # Выбор: доклад или перерыв
    waiting_time = State()  # Ожидание времени (например, 12:00-13:00)
    waiting_speaker = State()  # Ожидание ФИО (только для докладов)
    waiting_topic = State()  # Ожидание темы (только для докладов)
    waiting_for_speaker_id = State()


def get_organizer_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📜 Расписание"), KeyboardButton(text="📝 Список заявок")],
            [KeyboardButton(text="➕ Добавить событие"), KeyboardButton(text="👤 Назначить спикера")]
        ],
        resize_keyboard=True
    )


# Клавиатура выбора типа события
def get_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Доклад"), KeyboardButton(text="Перерыв/Обед")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    # Проверка прав доступа организатора
    if message.from_user.id != ORGANIZER_ID:
        await message.answer("❌ У вас нет прав доступа к этой команде.")
        return

    await message.answer("🛠 Добро пожаловать в панель Организатора!", reply_markup=get_organizer_keyboard())


# --- 1. Старт сценария (Доступно только админу по команде /add)
@router.message(Command("add"))
async def start_add_talk(message: Message, state: FSMContext):
    if message.from_user.id != ORGANIZER_ID:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer(
        "Что вы хотите добавить в расписание?",
        reply_markup=get_type_keyboard()
    )
    await state.set_state(OrganizerStates.choosing_type)


# --- Обработка кнопки "Отмена" на любом шаге
@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())


# --- 1. Старт сценария добавления события ---
@router.message(F.text == "➕ Добавить событие")
async def start_add_talk(message: Message, state: FSMContext):
    if message.from_user.id != ORGANIZER_ID:
        return

    await message.answer(
        "Что вы хотите добавить в расписание?",
        reply_markup=get_type_keyboard()
    )
    await state.set_state(OrganizerStates.choosing_type)


# --- 2. Выбор типа события
@router.message(OrganizerStates.choosing_type, F.text.in_(["Доклад", "Перерыв/Обед"]))
async def process_type(message: Message, state: FSMContext):
    is_break = message.text == "Перерыв/Обед"
    await state.update_data(is_break=is_break)

    await message.answer(
        "Введите временной слот (например, *14:00 - 14:45*):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True)
    )
    await state.set_state(OrganizerStates.waiting_time)


# --- 3. Получение времени
@router.message(OrganizerStates.waiting_time)
async def process_time(message: Message, state: FSMContext):
    await state.update_data(time_slot=message.text)
    user_data = await state.get_data()

    # Если это перерыв — нам не нужны спикер и тема, сразу сохраняем в БД
    if user_data['is_break']:
        db = db_manager.read_db()
        # Автоматически вычисляем следующий порядковый номер
        next_number = len(db.get("talks", [])) + 1

        # Вызываем вашу функцию из модуля БД
        db_manager.add_talk_to_schedule(
            number=next_number,
            time_slot=user_data['time_slot'],
            is_break=True
        )

        await message.answer(f"✅ Перерыв [{user_data['time_slot']}] успешно добавлен!",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:
        # Если это доклад, идем дальше запрашивать спикера
        await message.answer("Введите ФИО спикера:")
        await state.set_state(OrganizerStates.waiting_speaker)


# --- 4. Получение ФИО спикера (только для доклада)
@router.message(OrganizerStates.waiting_speaker)
async def process_speaker(message: Message, state: FSMContext):
    await state.update_data(speaker_name=message.text)
    await message.answer("Введите тему доклада:")
    await state.set_state(OrganizerStates.waiting_topic)


# --- 5. Получение темы и финальное сохранение доклада
@router.message(OrganizerStates.waiting_topic)
async def process_topic(message: Message, state: FSMContext):
    user_data = await state.get_data()
    db = db_manager.read_db()
    next_number = len(db.get("talks", [])) + 1

    # Сохраняем доклад в JSON через вашу функцию
    db_manager.add_talk_to_schedule(
        number=next_number,
        time_slot=user_data['time_slot'],
        speaker_name=user_data['speaker_name'],
        topic=message.text,
        is_break=False
    )

    text = (
        f"✅ Доклад успешно добавлен!\n\n"
        f"№ {next_number}. {user_data['speaker_name']} — {message.text} ({user_data['time_slot']})"
    )
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await state.clear()


# --- Сценарий назначения спикера ---
@router.message(F.text == "👤 Назначить спикера")
async def set_speaker_start(message: Message, state: FSMContext):
    if message.from_user.id != ORGANIZER_ID: return

    await message.answer("Перешлите сообщение спикера или введите его цифровой Telegram ID:")
    await state.set_state(OrganizerStates.waiting_for_speaker_id)


@router.message(OrganizerStates.waiting_for_speaker_id)
async def set_speaker_finish(message: Message, state: FSMContext):
    # Проверяем, переслал ли админ сообщение или ввел ID текстом
    if message.forward_from:
        speaker_id = message.forward_from.id
    else:
        try:
            speaker_id = int(message.text)
        except ValueError:
            await message.answer("❌ Пожалуйста, введите корректный числовой ID.")
            return

    # Вызываем функцию Разработчика 1
    db_manager.set_speaker(user_id=speaker_id, event_id=1)
    await message.answer(f"✅ Спикер с ID {speaker_id} успешно назначен на сцену!")
    await state.clear()

