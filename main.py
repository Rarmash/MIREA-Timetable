from datetime import date, datetime, timedelta
import re
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request

from database import delete_group, get_group, init_db, save_group
from schedule_client import ScheduleAPIError, ScheduleClient

app = Flask(__name__)
schedule_client = ScheduleClient()

GROUP_PATTERN = re.compile(r"^[А-ЯЁA-Z0-9]{4}-\d{2}-\d{2}$", re.IGNORECASE)
WEEKDAYS = {
    "понедельник": 0,
    "вторник": 1,
    "среда": 2,
    "среду": 2,
    "четверг": 3,
    "пятница": 4,
    "пятницу": 4,
    "суббота": 5,
    "субботу": 5,
    "воскресенье": 6,
}
MOSCOW = ZoneInfo("Europe/Moscow")


def today_moscow():
    return datetime.now(MOSCOW).date()


def alice_response(payload, text, *, end_session=False):
    return jsonify({
        "response": {"text": text[:1024], "end_session": end_session},
        "version": payload.get("version", "1.0"),
    })


def user_key(payload):
    session = payload.get("session", {})
    user = session.get("user") or {}
    application = session.get("application") or {}
    return user.get("user_id") or application.get("application_id")


def clean_group(value):
    value = re.sub(r"\s+", "", value.upper())
    if len(value) == 10 and value.count("-") == 0:
        value = f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value if GROUP_PATTERN.fullmatch(value) else None


def date_range_for(command):
    today = today_moscow()
    normalized = command.lower()
    if "завтра" in normalized:
        target = today + timedelta(days=1)
        return target, target, "завтра"
    for weekday, number in WEEKDAYS.items():
        if weekday in normalized:
            delta = (number - today.weekday()) % 7
            target = today + timedelta(days=delta)
            return target, target, weekday
    if "недел" in normalized:
        monday = today - timedelta(days=today.weekday())
        return monday, monday + timedelta(days=6), "эту неделю"
    return today, today, "сегодня"


def format_lesson(lesson, include_details=True):
    start = lesson.get("time_start", "")
    end = lesson.get("time_end", "")
    discipline = lesson.get("discipline") or "занятие"
    kind = lesson.get("lesson_type_full") or lesson.get("lesson_type")
    result = f"{start}–{end} — {discipline}"
    if kind:
        result += f", {kind.lower()}"
    if include_details:
        room = lesson.get("room") or {}
        room_number = room.get("number")
        campus = room.get("campus")
        teachers = lesson.get("teachers") or []
        if room_number:
            result += f", аудитория {room_number}"
            if campus:
                result += f", корпус {campus}"
        if teachers:
            result += f", преподаватель {teachers[0].get('name', '')}"
    return result


def render_schedule(lessons, label):
    if not lessons:
        return f"На {label} занятий нет."
    if label == "эту неделю":
        by_date = {}
        for lesson in lessons:
            by_date.setdefault(lesson.get("date", ""), []).append(lesson)
        weekday_names = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        chunks = [f"На этой неделе {len(lessons)} занятий."]
        for day, day_lessons in sorted(by_date.items()):
            try:
                weekday = weekday_names[date.fromisoformat(day).weekday()]
            except (ValueError, IndexError):
                weekday = day
            times = ", ".join(item.get("time_start", "") for item in day_lessons)
            chunks.append(f"{weekday}: {times}.")
        return " ".join(chunks)
    return f"Расписание на {label}. " + "; ".join(format_lesson(item, False) for item in lessons)


def next_lesson(lessons):
    now = datetime.now(MOSCOW).strftime("%Y-%m-%d %H:%M")
    future = [x for x in lessons if f"{x.get('date', '')} {x.get('time_end', '')}" >= now]
    return future[0] if future else None

@app.route("/post", methods=["POST"])
def main():
    payload = request.get_json(silent=True) or {}
    user_id = user_key(payload)
    command = ((payload.get("request") or {}).get("command") or "").strip()
    if not user_id:
        return alice_response(payload, "Не удалось определить пользователя. Попробуйте начать навык ещё раз.")
    if not command:
        return alice_response(payload, "Спросите, какое расписание на сегодня или завтра.")

    group = get_group(user_id)
    normalized = command.lower()
    if "забудь" in normalized or "удали" in normalized:
        delete_group(user_id)
        return alice_response(payload, "Готово, я забыла вашу группу.")

    entered_group = clean_group(command)
    if entered_group:
        save_group(user_id, entered_group)
        return alice_response(payload, f"Готово, запомнила группу {entered_group}.")
    if "групп" in normalized and not group:
        return alice_response(payload, "Назовите номер группы, например ЭПМО-01-26.")
    if not group:
        return alice_response(payload, "Сначала назовите вашу группу, например ЭПМО-01-26.")

    if "следующ" in normalized:
        start, end = today_moscow(), today_moscow() + timedelta(days=7)
        lessons = schedule_client.get_schedule(group, start, end)
        lesson = next_lesson(lessons)
        text = "Ближайших занятий в расписании нет." if not lesson else f"Следующая пара: {format_lesson(lesson)}."
        return alice_response(payload, text)

    start, end, label = date_range_for(command)
    try:
        lessons = schedule_client.get_schedule(group, start, end)
    except ScheduleAPIError:
        return alice_response(payload, "Не удалось получить расписание. Попробуйте ещё раз чуть позже.")
    if "заканч" in normalized:
        text = f"Последняя пара {label} заканчивается в {lessons[-1]['time_end']}." if lessons else f"На {label} занятий нет."
    elif "где" in normalized:
        lesson = next_lesson(lessons) or (lessons[0] if lessons else None)
        room = (lesson or {}).get("room") or {}
        text = "Аудитория для ближайшей пары не указана." if not lesson or not room.get("number") else f"Ближайшая пара в аудитории {room['number']}, корпус {room.get('campus', '')}."
    elif "кто преподаватель" in normalized or "кто вед" in normalized or "преподавател" in normalized:
        names = [t.get("name") for lesson in lessons for t in lesson.get("teachers", []) if t.get("name")]
        text = f"Преподаватель: {', '.join(dict.fromkeys(names))}." if names else f"На {label} преподаватель не указан."
    else:
        text = render_schedule(lessons, label)
    return alice_response(payload, text)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
