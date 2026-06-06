# validators.py
data_keys = ["room", "doors", "windows", "floor_objects"]
room_keys = ["width", "length", "height"]
doors_and_windows_keys = ["id", "name", "width", "length", "height", "x", "y"]
furniture_item_keys = ["id", "name", "tag", "dimension", "width", "length", "height"]


def validate_constructor(data):
    room = data["room"]
    doors = data["doors"]
    windows = data["windows"]
    floor_objects = data["floor_objects"]
    errors = []
    for error in [
        *validate_data_type(data),
        *validate_required_keys(data, data_keys),
        *validate_windows(windows),
        *validate_doors(doors),
        *validate_floor_objects(floor_objects),
        *validate_room(room),
        *validate_area(room, floor_objects),
    ]:
        if error:
            errors.append(error)
    return errors


def validate_data_type(item):
    if not isinstance(item, dict):
        yield "Данные должны быть словарём"


def validate_required_keys(item, keys):
    for key in keys:
        if key not in item:
            yield f"Отсутствует ключ '{key}'"


def validate_items_value(item, key):
    for key, value in item.items():
        if key in [
            "width",
            "length",
            "height",
            "x",
            "y",
        ]:
            if not isinstance(value, (int, float)):
                yield f"Значение '{key}' должно быть числом"
            else:
                if value < 0:
                    yield f"Значение '{key}' должно быть положительным"

        if key in [
            "id",
            "name",
            "tag",
            "dimension",
        ]:
            if not isinstance(value, (str)):
                yield f"Значение '{key}' должно быть строкой"

        if value == "":
            yield f"Значение '{key}' пустое"


def validate_area(room, floor_objects):
    try:
        room_area = room["width"] * room["length"]
        furnitures_area = sum([item["width"] * item["length"] for item in floor_objects])
    except Exception as e:
        print(e)
        yield "Не валидные данные для расчета площади"
    else:
        if furnitures_area > room_area:
            yield "Площадь комнаты меньше площади объектов"


def validate_windows(windows):
    for item in windows:
        for error in [
            *validate_data_type(item),
            *validate_required_keys(item, doors_and_windows_keys),
            *validate_items_value(item, doors_and_windows_keys),
        ]:
            if error:
                yield f"{item}:\n{error}\n\n"


def validate_doors(doors):
    for item in doors:
        for error in [
            *validate_data_type(item),
            *validate_required_keys(item, doors_and_windows_keys),
            *validate_items_value(item, doors_and_windows_keys),
        ]:
            if error:
                yield f"{item}:\n{error}\n\n"


def validate_floor_objects(floor_objects):
    for item in floor_objects:
        for error in [
            *validate_data_type(item),
            *validate_required_keys(item, furniture_item_keys),
            *validate_items_value(item, furniture_item_keys),
        ]:
            if error:
                yield f"\n{item}:\n{error}\n"


def validate_room(room):
    for error in [
        *validate_data_type(room),
        *validate_required_keys(room, room_keys),
        *validate_items_value(room, room_keys),
    ]:
        if error:
            yield error
