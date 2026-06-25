import json
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "db.json")

def init_db():
    """Создает базовую структуру db.json, если файла нет."""
    if not os.path.exists(DB_FILE):
        default_data = {
            # Расписание — это структурированный список докладов
            "talks": [
                {
                    "number": 1,
                    "is_break": False,
                    "time_slot": "10:00 - 10:45",
                    "speaker_name": "Иванов Иван Иванович",
                    "topic": "Введение в AI и нейросети",
                    "speaker_id": 101  # Telegram ID спикера для связи с вопросами
                },
                {
                    "number": 2,
                    "is_break": False,
                    "time_slot": "11:00 - 11:45",
                    "speaker_name": "Петров Петр Петрович",
                    "topic": "Разработка ботов на aiogram 3",
                    "speaker_id": 202
                },
                {
                    "number": 3,
                    "is_break": True,
                    "time_slot": "12:00 - 12:45",
                    "speaker_name": None,
                    "topic": None,
                    "speaker_id": None
                }
            ],
            "current_speaker_id": None,
            "current_event_id": 1,
            "questions": []
        }
        write_db(default_data)

def read_db():
    """Внутренняя функция чтения."""
    init_db()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_db(data):
    """Внутренняя функция записи."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Функции для Разработчика 2 (Слушатель и Спикер) ---

def get_schedule() -> str:
    """Формирует текстовое расписание дня с учетом докладов и перерывов."""
    db = read_db()
    talks = db.get("talks", [])
    
    if not talks:
        return "📅 Расписание пока не заполнено."
        
    lines = ["📅 *Программа мероприятия:*", ""]
    for talk in talks:
        # Проверяем, перерыв это или доклад
        if talk.get("is_break", False):
            # Шаблон для перерыва/обеда (выводим только время и само событие)
            line = f"☕️ *[{talk['time_slot']}]* — Обед / Технический перерыв"
        else:
            # Строгий шаблон для обычного доклада
            line = (
                f"🔹 *Доклад {talk['number']}.* "
                f"Спикер: {talk['speaker_name']}. "
                f"Тема: «{talk['topic']}». "
                f"Время: {talk['time_slot']}."
            )
        lines.append(line)
        
    return "\n\n".join(lines)


def add_question(user_id: int, user_name: str, text: str):
    """Сохраняет вопрос в общую базу данных."""
    db = read_db()
    new_q = {
        "user_id": user_id,
        "user_name": user_name,
        "text": text,
        "speaker_id": db.get("current_speaker_id")
    }
    db["questions"].append(new_q)
    write_db(db)

def get_questions_for_speaker(speaker_id: int) -> list:
    """Возвращает список вопросов, адресованных конкретному спикеру."""
    db = read_db()
    return [q for q in db["questions"] if q["speaker_id"] == speaker_id]

def log_donation(user_id: int, user_name: str, amount: int):
    """Сохраняет информацию о сделанном донате в db.json."""
    db = read_db()
    
    # Инициализируем список донатов, если его еще нет в файле
    if "donations" not in db:
        db["donations"] = []
        
    db["donations"].append({
        "user_id": user_id,
        "user_name": user_name,
        "amount": amount
    })
    write_db(db)

# --- Функции для Разработчика 3 (Организатор) ---

def add_talk_to_schedule(number: int, time_slot: str, speaker_name: str = None, topic: str = None, speaker_id: int = None, is_break: bool = False):
    """
    Добавляет новый элемент в расписание. 
    Если is_break=True, то это технический перерыв (обед, кофе-брейк).
    """
    db = read_db()
    new_item = {
        "number": number,
        "time_slot": time_slot,
        "is_break": is_break,
        "speaker_name": speaker_name if not is_break else None,
        "topic": topic if not is_break else None,
        "speaker_id": speaker_id if not is_break else None
    }
    db["talks"].append(new_item)
    db["talks"].sort(key=lambda x: x["number"])
    write_db(db)


def clear_schedule():
    """Полностью очищает список докладов."""
    db = read_db()
    db["talks"] = []
    write_db(db)

def set_speaker_by_talk_number(talk_number: int):
    """Автоматически включает спикера на сцене по номеру доклада."""
    db = read_db()
    talks = db.get("talks", [])
    
    for talk in talks:
        if talk["number"] == talk_number:
            db["current_speaker_id"] = talk["speaker_id"]
            db["current_event_id"] = talk_number
            write_db(db)
            return True
    return False

def set_speaker(user_id: int, event_id: int):
    """Назначает активного спикера вручную и привязывает его к ID события."""
    db = read_db()
    db["current_speaker_id"] = user_id
    db["current_event_id"] = event_id
    write_db(db)

def get_current_speaker_id():
    """Возвращает ID текущего спикера на сцене (для проверки прав)."""
    db = read_db()
    return db.get("current_speaker_id")
