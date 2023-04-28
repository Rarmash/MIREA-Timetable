from flask import Flask, request
import requests
import json
import datetime
from options import Collection
from transliterate import translit
import pymongo.errors

app = Flask(__name__)

global startweek
startweek = datetime.date(2023, 2, 9).isocalendar()[1]

@app.route("/post", methods=["POST"])
def main():
    response = {
        "version": request.json['version'],
        "session": request.json["session"],
        "response": {
            "end_session": False
        }
    }    
    user_id = response["session"]["user"]["user_id"]
    # Получаем запрос пользователя
    text = request.json["request"]["command"]
    print(text)
    if "забудь" in text.lower() or "удали" in text.lower():
        delete_group(user_id)
        response["response"]["text"] = "Готово, я удалила вашу группу из своей памяти."
        return response
    if "на сегодня" in text.lower():
        group = Collection.find_one({"_id": user_id})
        if group:
            group = group['group_num'].replace(' ', '')
            table = get_table(group)
            response["response"]["text"] = f"Расписание на сегодня для группы {group}:\n{table}"
        else:
            response["response"]["text"] = 'Вы мне не называли свою группу. Просто скажите мне "Алиса, добавь мою группу".'
    elif "на завтра" in text.lower():
        group = Collection.find_one({"_id": user_id})
        if group:
            group = group['group_num'].replace(' ', '')
            table = get_tomorrow_table(group)
            response["response"]["text"] = f"Расписание на завтра для группы {group}:\n{table}"
        else:
            response["response"]["text"] = 'Вы мне не называли свою группу. Просто скажите мне "Алиса, добавь мою группу".'
    elif "групп" in text.lower():
        response["response"]["text"] = "Хорошо. Назовите название вашей группы. Пример: ИКБО-09-22."
    elif check_group(text.upper().replace(" ", "")):
        first_part = text.upper().replace(" ", "")[:4] # Получаем первую часть
        second_part = text.upper().replace(" ", "")[4:6] # Получаем вторую часть
        third_part = text.upper().replace(" ", "")[6:] # Получаем третью часть
        name = f"{first_part}-{second_part}-{third_part}"
        name = translit(name, 'ru')
        add_group(user_id, name)
        response["response"]["text"] = "Готово. Ваша группа сохранена, можете спросить расписание."

    # Формируем ответ пользователю
    return response

def get_table(name):    
    response = requests.get(f'https://timetable.mirea.ru/api/group/name/{name}').content
    response = json.loads(response)
    lessons_list = []
    lessons = response['lessons']
    week = datetime.datetime.today().isocalendar()[1] - startweek + 1
    stroka = ""
    for lesson in lessons:
        if lesson["weekday"] == datetime.datetime.today().isoweekday():
            for weeknum in lesson['weeks']:
                if week == weeknum:
                    if lesson["lesson_type"]["name"] == 'пр':
                        lesson_name = 'практика'
                    elif lesson["lesson_type"]["name"] == 'лек':
                        lesson_name = 'лекция'
                    elif lesson["lesson_type"]["name"] == 'с/р':
                        lesson_name = 'самостоятельная работа'
                    elif lesson["lesson_type"]["name"] == 'лаб':
                        lesson_name = 'лабораторная работа'
                    stroka += f'{lesson["discipline"]["name"]} ({lesson_name}): {str(lesson["calls"]["time_start"])[:-3]} - {str(lesson["calls"]["time_end"])[:-3]}\n'
    stroka = stroka[:-1]
    return stroka

def get_tomorrow_table(name):
    response = requests.get(f'https://timetable.mirea.ru/api/group/name/{name}').content
    response = json.loads(response)

    lessons = response['lessons']
    stroka = ""
    day = datetime.datetime.today().isoweekday() + 1
    week = datetime.datetime.today().isocalendar()[1] - startweek + 1
    if day == 8:
        day = 1
        week += 1
    for lesson in lessons:
        if lesson["weekday"] == day:
            for weeknum in lesson['weeks']:
                if week == weeknum:
                    if lesson["lesson_type"]["name"] == 'пр':
                        lesson_name = 'практика'
                    elif lesson["lesson_type"]["name"] == 'лек':
                        lesson_name = 'лекция'
                    elif lesson["lesson_type"]["name"] == 'с/р':
                        lesson_name = 'самостоятельная работа'
                    elif lesson["lesson_type"]["name"] == 'лаб':
                        lesson_name = 'лабораторная работа'
                    stroka += f'{lesson["discipline"]["name"]} ({lesson_name}): {str(lesson["calls"]["time_start"])[:-3]} - {str(lesson["calls"]["time_end"])[:-3]}\n'
    stroka = stroka[:-1]
    return stroka

def check_group(name):
    first_part = name[:4] # Получаем первую часть
    second_part = name[4:6] # Получаем вторую часть
    third_part = name[6:] # Получаем третью часть
    
    name = f"{first_part}-{second_part}-{third_part}"
    #part 2
    parts = name.split('-')
    if len(parts) != 3:
        return False
    # Проверяем, что первая часть состоит из 4 букв или цифр
    if not parts[0].isalnum() or len(parts[0]) != 4:
        return False
    # Проверяем, что вторая и третья части состоят из двух цифр
    if not parts[1].isdigit() or len(parts[1]) != 2:
        return False
    if not parts[2].isdigit() or len(parts[2]) != 2:
        return False
    # Если все проверки прошли успешно, строка соответствует формату
    return True
    

def add_group(user_id, group):
    try:
        Collection.insert_one({"_id": user_id, "group_num": group})
    except pymongo.errors.DuplicateKeyError:
        Collection.update_one({"_id": user_id}, {"$set": {"group_num": group}})        

def delete_group(user_id):
    Collection.delete_one({"_id": user_id})

if __name__ == "__main__":
    app.run()