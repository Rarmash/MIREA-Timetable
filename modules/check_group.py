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