from flask import Flask, request
import requests
import json
import datetime
from options import Collection, startweek
from transliterate import translit
import pymongo.errors
from modules import check_group, get_table, get_tomorrow_table

app = Flask(__name__)

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
    elif "сегодня" in text.lower() or "седня" in text.lower() or "сёдня" in text.lower():
        group = Collection.find_one({"_id": user_id})
        if group:
            group = group['group_num'].replace(' ', '')
            table = get_table.get_table(group)
            response["response"]["text"] = f"Расписание на сегодня для группы {group}:\n{table}"
        else:
            response["response"]["text"] = 'Вы мне не называли свою группу. Просто скажите мне "Алиса, добавь мою группу".'
    elif "завтра" in text.lower():
        group = Collection.find_one({"_id": user_id})
        if group:
            group = group['group_num'].replace(' ', '')
            table = get_tomorrow_table.get_tomorrow_table(group)
            response["response"]["text"] = f"Расписание на завтра для группы {group}:\n{table}"
        else:
            response["response"]["text"] = 'Вы мне не называли свою группу. Просто скажите мне "Алиса, добавь мою группу".'
    elif "групп" in text.lower():
        response["response"]["text"] = "Хорошо. Назовите название вашей группы. Пример: ИКБО-09-22."
    elif check_group.check_group(text.upper().replace(" ", "")):
        first_part = text.upper().replace(" ", "")[:4] # Получаем первую часть
        second_part = text.upper().replace(" ", "")[4:6] # Получаем вторую часть
        third_part = text.upper().replace(" ", "")[6:] # Получаем третью часть
        name = f"{first_part}-{second_part}-{third_part}"
        name = translit(name, 'ru')
        add_group(user_id, name)
        response["response"]["text"] = "Готово. Ваша группа сохранена, можете спросить расписание."

    # Формируем ответ пользователю
    return response

def add_group(user_id, group):
    try:
        Collection.insert_one({"_id": user_id, "group_num": group})
    except pymongo.errors.DuplicateKeyError:
        Collection.update_one({"_id": user_id}, {"$set": {"group_num": group}})        

def delete_group(user_id):
    Collection.delete_one({"_id": user_id})

if __name__ == "__main__":
    app.run()