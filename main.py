from flask import Flask, request
import requests
import json
import datetime

app = Flask(__name__)

global name
name = 'ИКБО-09-22'

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
        
    # Получаем запрос пользователя
    text = request.json["request"]["command"]
    if "на сегодня" in text:
        table = get_table(text)
        response["response"]["text"] = f"Расписание на сегодня для группы {name}:\n{table}"
    elif "на завтра" in text:
        table = get_tomorrow_table(text)
        response["response"]["text"] = f"Расписание на завтра для группы {name}:\n{table}"

    if not table:
        response["response"]["text"] = "Я не могу найти расписание на эту группу. Попробуйте еще раз."
        return response

    # Формируем ответ пользователю
    return response

def get_table(text):    
    response = requests.get(f'https://timetable.mirea.ru/api/group/name/{name}').content
    response = json.loads(response)

    lessons = response['lessons']
    week = datetime.datetime.today().isocalendar()[1] - startweek + 1
    stroka = ""
    for lesson in lessons:
        if lesson["weekday"] == datetime.datetime.today().isoweekday():
            for weeknum in lesson['weeks']:
                if week == weeknum:
                    stroka += f'{lesson["discipline"]["name"]} ({lesson["lesson_type"]["name"]})\n'
    stroka = stroka[:-1]
    return stroka

def get_tomorrow_table(text):
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
                    stroka += f'{lesson["discipline"]["name"]} ({lesson["lesson_type"]["name"]})\n'
    stroka = stroka[:-1]
    return stroka

if __name__ == "__main__":
    app.run()