from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database import db_manager

router = Router()

def get_speaker_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Посмотреть вопросы к моему докладу")],
            [KeyboardButton(text="⬅️ Вернуться в меню слушателя")]
        ],
        resize_keyboard=True
    )

@router.message(F.text == "🎤 Меню Спикера")
async def speaker_menu(message: Message):
    current_speaker_id = db_manager.get_current_speaker_id()
    
    # Проверка: является ли пользователь текущим спикером
    if message.from_user.id != current_speaker_id:
        await message.answer("❌ Вы не являетесь текущим активным спикером на сцене.")
        return
        
    await message.answer("Добро пожаловать в панель докладчика!", reply_markup=get_speaker_keyboard())

@router.message(F.text == "📋 Посмотреть вопросы к моему докладу")
async def show_speaker_questions(message: Message):
    current_speaker_id = db_manager.get_current_speaker_id()
    if message.from_user.id != current_speaker_id:
        return

    questions = db_manager.get_questions_for_speaker(current_speaker_id)
    if not questions:
        await message.answer("Пока никто не задал вопросов к вашему докладу.")
        return

    text = "📥 Вопросы от аудитории:\n\n"
    for i, q in enumerate(questions, 1):
        text += f"{i}. От {q['user_name']}:\n— {q['text']}\n\n"
    await message.answer(text)

@router.message(F.text == "⬅️ Вернуться в меню слушателя")
async def back_to_listener(message: Message):
    from handlers.listener import get_listener_keyboard
    await message.answer("Вы вернулись в общее меню.", reply_markup=get_listener_keyboard())

