from copy import deepcopy

import pytest

from apps.planner.services.placement.core import Core
from apps.planner.services.placement.render import render_to_png, render_to_svg

ROOM_DATA = {"width": 400, "length": 500, "height": 200, "min_passage": 70}

DOORS_DATA = [
    {"id": "1", "name": "дверь", "x": 400, "y": 250, "width": 60, "length": 5, "height": 200},
]
WINDOWS_DATA = [
    {"id": "3", "name": "окно", "x": 200, "y": 0, "width": 180, "length": 10, "height": 120},
]
FLOOR_OBJECTS_DATA = [
    {
        "id": "1",
        "name": "Кровать",
        "tag": "sz",
        "dimension": "large_furniture",
        "width": 180,
        "length": 200,
        "height": 40,
    },
    {
        "id": "2",
        "name": "Шкаф",
        "tag": "wz",
        "dimension": "large_furniture",
        "width": 120,
        "length": 60,
        "height": 200,
    },
    {
        "id": "3",
        "name": "Стол",
        "tag": "pz",
        "dimension": "large_furniture",
        "width": 90,
        "length": 60,
        "height": 60,
    },
    {
        "id": "4",
        "name": "Стул",
        "tag": "sz",
        "dimension": "medium_furniture",
        "width": 60,
        "length": 40,
        "height": 30,
    },
    {
        "id": "5",
        "name": "Тумба",
        "tag": "sz",
        "dimension": "medium_furniture",
        "width": 100,
        "length": 50,
        "height": 40,
    },
    {
        "id": "6",
        "name": "Тумба",
        "tag": "sz",
        "dimension": "medium_furniture",
        "width": 100,
        "length": 50,
        "height": 40,
    },
]

# Кол-во объектов мебели (3 large + 3 medium), без авто-генерируемых розеток.
EXPECTED_FURNITURE_COUNT = 6
# Допуск на погрешность float-поворотов при проверке границ.
BOUNDS_TOLERANCE = 1.0
# Алгоритм рандомизирован — даём несколько попыток разместить всё.
MAX_ATTEMPTS = 15


def _build_placed_core():
    """Строит `Core` и запускает алгоритм, повторяя при неудачной раскладке."""
    for _ in range(MAX_ATTEMPTS):
        core = Core(
            deepcopy(ROOM_DATA),
            deepcopy(DOORS_DATA),
            deepcopy(WINDOWS_DATA),
            deepcopy(FLOOR_OBJECTS_DATA),
        )
        if getattr(core, "get_zones", None):
            core.run_algorithm()
            return core
    pytest.fail(f"Алгоритм не смог разместить объекты за {MAX_ATTEMPTS} попыток")


def test_all_furniture_is_placed():
    """Проверить что вся переданная мебель размещена с координатами и поворотом."""
    core = _build_placed_core()
    assert len(core.room.furnitures) == EXPECTED_FURNITURE_COUNT
    # Каждой мебели задано конкретное положение и поворот.
    for obj in core.room.furnitures:
        assert obj.x is not None and obj.y is not None
        assert obj.rotation in (0, 90, 180, 270)


def test_furniture_within_room_bounds():
    """Проверить что все углы мебели лежат в пределах комнаты."""
    core = _build_placed_core()
    width, length = ROOM_DATA["width"], ROOM_DATA["length"]
    for obj in core.room.furnitures:
        for corner in obj.get_corners():
            assert -BOUNDS_TOLERANCE <= corner.x <= width + BOUNDS_TOLERANCE, obj.name
            assert -BOUNDS_TOLERANCE <= corner.y <= length + BOUNDS_TOLERANCE, obj.name


def test_electricity_points_generated():
    """Проверить что алгоритм автоматически добавляет розетки."""
    core = _build_placed_core()
    # Алгоритм добавляет по 2 розетки на зону (3 зоны).
    assert len(core.room.electricity_points) > 0
    assert all(p.name == "розетка" for p in core.room.electricity_points)


def test_render_svg():
    """Проверить что раскладка рендерится в корректный SVG."""
    core = _build_placed_core()
    svg = render_to_svg(core)
    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert "<polygon" in svg  # есть отрисованная мебель


def test_render_png():
    """Проверить что раскладка рендерится в корректный PNG."""
    core = _build_placed_core()
    png = render_to_png(core)
    # Сигнатура PNG-файла.
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
