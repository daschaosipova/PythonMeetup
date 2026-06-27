import json
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "db.json")

def init_db():
    """Создает базовую структуру db.json, если файла нет."""
    if not os.path.exists(DB_FILE):
        default_data = {
            "talks": [],
            "current_speaker_id": None,
            "questions": [],
            "applications": [],
            "users": []
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

def add_application(user_id: int, user_name: str, text: str):
    """Сохраняет запрос на выступление в общую базу данных."""
    db = read_db()
    new_application = {
        "user_id": user_id,
        "user_name": user_name,
        "text": text
    }
    db["applications"].append(new_application)
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

def add_talk_to_schedule(
    number: int, 
    time_slot: str,
    speaker_name: str = None,
    topic: str = None,
    speaker_id: int = None,
    is_break: bool = False
):
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


def set_speaker(user_id: int):
    """Назначает активного спикера по его ID."""
    db = read_db()
    db["current_speaker_id"] = user_id
    write_db(db)

def get_current_speaker_id():
    """Возвращает ID текущего спикера на сцене (для проверки прав)."""
    db = read_db()
    return db.get("current_speaker_id")

def get_applications():
    db = read_db()
    applications = db.get("applications", [])
    return applications

def delete_talk_by_number(number: int) -> bool:
    """Удаляет событие по его номеру и обновляет нумерацию остальных элементов."""
    db = read_db()
    talks = db.get("talks", [])
    
    # Ищем, есть ли вообще событие с таким номером
    initial_length = len(talks)
    
    # Фильтруем список, оставляя только те элементы, чей номер НЕ совпадает с удаляемым
    talks = [talk for talk in talks if talk.get("number") != number]
    
    # Если размер списка не изменился, значит события с таким номером не было
    if len(talks) == initial_length:
        return False
        
    # Пересчитываем номера по порядку (1, 2, 3...), чтобы после удаления не было пропусков
    for index, talk in enumerate(talks, 1):
        talk["number"] = index
        
    # Записываем обновленный список обратно в базу
    db["talks"] = talks
    write_db(db)
    return True

def add_user(user_id: int, user_name: str, username: str | None):
    db = read_db()

    if "users" not in db:
        db["users"] = []

    for user in db["users"]:
        if user["user_id"] == user_id:
            return

    db["users"].append({
        "user_id": user_id,
        "user_name": user_name,
        "username": username
    })

    write_db(db)

def get_all_users() -> list:
    db = read_db()
    return db.get("users", [])
