"""Точка входа для генерации раскладки из API.

Связывает валидацию входных данных, запуск алгоритма (`Core`)
и сериализацию результата в обычные dict/list для JSON-ответа.
Экземпляр `Core` отдаётся наружу для рендеринга в SVG/PNG (см. `render`).
"""

from apps.planner.services.placement.core import Core
from apps.planner.services.placement.validators import validate_constructor


class LayoutGenerationError(Exception):
    """Алгоритму не удалось построить раскладку для переданных данных."""


def build_core(room: dict, doors: list, windows: list, floor_objects: list):
    """Валидирует вход и запускает алгоритм.

    Возвращает кортеж ``(core, errors)``:
    - при ошибках валидации ``core`` = ``None``, ``errors`` — список строк;
    - при успехе ``errors`` = ``None``, ``core`` — готовый `Core` после
      `run_algorithm()`.

    Бросает :class:`LayoutGenerationError`, если данные валидны,
    но алгоритм не смог разместить объекты.
    """
    errors = validate_constructor(
        {
            "room": room,
            "doors": doors,
            "windows": windows,
            "floor_objects": floor_objects,
        }
    )
    if errors:
        return None, errors

    core = Core(room, doors, windows, floor_objects)

    # `Core.__init__` запускает раскладку зон; если разместить не удалось,
    # `get_zones` остаётся пустым/None.
    if not getattr(core, "get_zones", None):
        raise LayoutGenerationError("Не удалось разместить все объекты в комнате")

    core.run_algorithm()
    return core, None


def _serialize_object(obj) -> dict:
    """Сериализует объект комнаты (мебель/проём/розетку) в dict."""
    return {
        "id": obj.id,
        "name": obj.name,
        "tag": obj.tag,
        "dimension": obj.dimension,
        "x": round(obj.x, 2),
        "y": round(obj.y, 2),
        "width": obj.width,
        "length": obj.length,
        "height": obj.height,
        "rotation": obj.rotation,
    }


def serialize_layout(core, room: dict) -> dict:
    """Собирает JSON-представление раскладки из готового `Core`."""
    placed_room = core.room
    return {
        "room": {
            "width": room["width"],
            "length": room["length"],
            "height": room["height"],
        },
        "doors": [_serialize_object(obj) for obj in placed_room.doors],
        "windows": [_serialize_object(obj) for obj in placed_room.windows],
        "furnitures": [_serialize_object(obj) for obj in placed_room.furnitures],
        "electricity_points": [_serialize_object(obj) for obj in placed_room.electricity_points],
    }
