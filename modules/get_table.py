import requests
import json
import datetime
from options import startweek

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