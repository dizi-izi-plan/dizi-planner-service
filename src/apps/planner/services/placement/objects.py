import math
import random
from dataclasses import dataclass, field

from apps.planner.services.placement.constants import ROTATIONS


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Room:
    width: float
    length: float
    doors: list = field(default_factory=list)
    windows: list = field(default_factory=list)
    furnitures: list = field(default_factory=list)
    electricity_points: list = field(default_factory=list)
    walls: list = field(default_factory=list)


@dataclass
class Rectangle:
    x: float
    y: float
    width: float
    length: float
    rotation: float = 0  # в градусах


@dataclass
class BuildingObject:
    """Общий класс для объекта комнаты и манипуляции с ним"""

    id: str | None = None
    name: str | None = None
    tag: str | None = None
    dimension: str | None = None
    width: float | None = None
    length: float | None = None
    height: float | None = None
    x: float | None = 0
    y: float | None = 0
    rotation: int | None = 0

    @property
    def center(self):
        rect = self.create_rectangle()

        half_width = rect.width / 2
        half_length = rect.length / 2

        x = rect.x + half_width
        y = rect.y + half_length

        return Point(x, y)

    def create_rectangle(self) -> Rectangle:
        """Создает прямоугольник
        для данного предмета мебели"""
        corners = self.get_corners()
        cor_x_min = min(map(lambda obj: obj.x, corners))
        cor_y_min = min(map(lambda obj: obj.y, corners))
        cor_x_max = max(map(lambda obj: obj.x, corners))
        cor_y_max = max(map(lambda obj: obj.y, corners))

        rect_width = cor_x_max - cor_x_min
        rect_length = cor_y_max - cor_y_min

        return Rectangle(cor_x_min, cor_y_min, rect_width, rect_length, self.rotation)

    def get_corners(self) -> list[Point]:
        """Возвращает координаты углов прямоугольника с учетом поворота"""

        # Преобразуем градусы в радианы
        rad = math.radians(self.rotation)
        cos_val = math.cos(rad)
        sin_val = math.sin(rad)

        # Центр прямоугольника
        cx = self.x + self.width / 2
        cy = self.y + self.length / 2

        # Координаты углов относительно центра
        half_width = self.width / 2
        half_length = self.length / 2

        # Применяем поворот к каждому углу
        corners = []
        for x, y in [
            (-half_width, -half_length),
            (half_width, -half_length),
            (half_width, half_length),
            (-half_width, half_length),
        ]:
            x_rotated = cx + x * cos_val - y * sin_val
            y_rotated = cy + x * sin_val + y * cos_val

            corners.append(Point(x_rotated, y_rotated))

        # смещаем объект в его точку координат после поворота
        min_x = min(map(lambda cor: cor.x, corners))
        min_y = min(map(lambda cor: cor.y, corners))

        self.dx = self.x - min_x
        self.dy = self.y - min_y

        for corner in corners:
            corner.x += self.dx
            corner.y += self.dy

        return corners

    def get_distance(self, obj) -> float:
        """Получаем дистанцию между двумя объектами"""

        corners1 = self.get_corners()
        corners2 = obj.get_corners()

        min_distance = float("inf")
        for p1 in corners1:
            for p2 in corners2:
                dist = math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
                min_distance = min(min_distance, dist)

        return min_distance


class OpeningObject(BuildingObject):
    """Класс проёма"""

    def get_rotation(self, room):
        if self.y == 0:
            self.rotation = 0
        elif self.x == room.width:
            self.rotation = 90
            self.x -= self.length
        elif self.y == room.length:
            self.rotation = 180
            self.y -= self.width
        elif self.x == 0:
            self.rotation = 270

    def generate_door_random_placement(self, room: Room, other_obj=[]):
        """Генерирует случайное расположение проемов"""
        # Сделать проще

        other_side = list(map(lambda x: x.rotation, other_obj))

        self.rotation = random.choice(
            list(filter(lambda x: x not in other_side, [0, 90, 180, 270]))
        )

        if self.name == "дверь":
            self.width = 60
            self.length = 10
            self.height = 200

            if self.rotation == 0:
                self.x = random.choice([30, room.width - self.width - 30])
                self.y = 0

            elif self.rotation == 90:
                self.x = room.width
                self.y = random.choice([30, room.length - self.length - 30])

            elif self.rotation == 180:
                self.x = random.choice([30, room.width - self.width - 30])
                self.y = room.length

            elif self.rotation == 270:
                self.x = 0
                self.y = random.choice([30, room.length - self.length - 30])

        elif self.name == "окно":
            self.width = 150
            self.length = 10
            self.height = 100

            if self.rotation == 0:
                self.x = room.width * 0.5 - self.width * 0.5
                self.y = 0
            elif self.rotation == 90:
                self.x = room.width
                self.y = room.length * 0.5 - self.length
            elif self.rotation == 180:
                self.x = room.width * 0.5 - self.width * 0.5
                self.y = room.length
            elif self.rotation == 270:
                self.x = 0
                self.y = room.length * 0.5 - self.length


class FloorObject(BuildingObject):
    """Класс объекта на полу"""

    ...


class ElectricPoint(BuildingObject): ...


class Wall:
    def __init__(self, width, rotation):
        self.width: float = width
        self.rotation: float = rotation
        self.openings: list = []
        self.wall_divide: list = [(0, self.width)]
        self.free_lines: list = [(0, self.width)]

    def add_divide(self, obj):
        """Сокращает свободное пространство у стены при добавлении проема"""
        if self.rotation in [0, 180]:
            x1 = obj.x
            x2 = obj.x + obj.width
        else:
            x1 = obj.y
            x2 = obj.y + obj.width

        lines = []
        if isinstance(obj, OpeningObject):
            for index, line in enumerate(self.wall_divide):
                if x1 > line[0] and x2 < line[1]:
                    lines.extend(((line[0], x1), (x2, line[1])))
                    del self.wall_divide[index]
                    del self.free_lines[index]
                    self.wall_divide.extend(lines)
                    self.free_lines.extend(lines)
        else:
            for index, line in enumerate(self.free_lines):
                if x1 > line[0] and x2 < line[1]:
                    lines.extend(((line[0], x1), (x2, line[1])))
                    del self.free_lines[index]
                    self.free_lines.extend(lines)

    def update_divide(self, objects):
        """Обновляет свободные места у стены, при изменении положения зон"""
        self.free_lines: list = self.wall_divide
        for obj in objects:
            self.add_divide(obj)

    def insert_check(self, width):
        """Проверяет можно ли вставить объект в свободное пространство"""
        for line in self.free_lines:
            if width < line[1] - line[0]:
                return line
        return False


@dataclass
class ZoneGenerator(BuildingObject):
    """Класс для создание зоны"""

    main_object: object | None = None
    second_objects: list[object] = field(default_factory=list)
    objects_list: list[object] = field(default_factory=list)

    # ..._position выбор позиции объекта вокруг основной мебели
    def first_position(self, obj):
        obj.x = -obj.width
        obj.y = 0
        return obj

    def second_position(self, obj):
        obj.x = self.main_object.width
        obj.y = 0
        return obj

    def third_position(self, obj):
        obj.x = 0
        obj.y = -obj.length
        return obj

    def fourth_position(self, obj):
        obj.x = self.main_object.width - obj.width
        obj.y = -obj.length
        return obj

    def generate_electric_point(self, min_x, max_x, obj):
        """Генерирует розетки и их положение"""
        # Создаем электроточки
        el_point1 = ElectricPoint(name="розетка", width=30, length=3)
        el_point2 = ElectricPoint(name="розетка", width=20, length=3)

        # Задаем зоны возможного расположения
        el_zone1 = [obj.width, max_x]
        el_zone2 = [min_x - el_point2.width, 0]

        # Выбираем случайную точку
        el_point1.x = random.uniform(*el_zone1)
        el_point2.x = random.uniform(*el_zone2)

        return el_point1, el_point2

    def generate_zone(self):
        """Создает зону с объектами"""
        positions = [
            self.first_position,
            self.second_position,
            self.third_position,
            self.fourth_position,
        ]
        copy_objects = self.second_objects.copy()
        random.shuffle(copy_objects)
        objects_positions = [self.main_object]

        for i in range(len(self.second_objects)):
            new_object = positions[i](copy_objects[i])
            objects_positions.append(new_object)

        # Получаем максимальное значения x
        max_x = max(obj.x + obj.width for obj in objects_positions)

        # Получаем минимальные значения xy
        min_x = min(obj.x for obj in objects_positions)
        min_y = min(obj.y for obj in objects_positions)

        # Создаем объекты розеток
        objects_positions.extend(self.generate_electric_point(min_x, max_x, self.main_object))

        min_x = min(obj.x for obj in objects_positions)
        min_y = min(obj.y for obj in objects_positions)

        # Вычисляем смещение
        dx = -min_x
        dy = -min_y
        # Смещаем все объекты так, чтобы зона начала с (0,0)
        for obj in objects_positions:
            obj.x += dx
            obj.y += dy

        # Обновляем границы после смещения
        new_min_x = min(obj.x for obj in objects_positions)
        new_min_y = min(obj.y for obj in objects_positions)
        new_max_x = max(obj.x + obj.width for obj in objects_positions)
        new_max_y = max(obj.y + obj.length for obj in objects_positions)

        self.x = 0
        self.y = 0
        self.width = new_max_x - new_min_x
        self.length = new_max_y - new_min_y

        self.objects_list = objects_positions

    def update_object_coords(self, obj):
        """Обновляет позицию объектов области
        с учетом поворота и расположения области"""
        # Преобразуем градусы в радианы
        rad = math.radians(self.rotation)
        cos_val = math.cos(rad)
        sin_val = math.sin(rad)

        # Центр зоны
        cx = self.width / 2
        cy = self.length / 2

        # Координаты углов относительно центра зоны
        obj_corners = [
            (obj.x - self.width / 2, obj.y - self.length / 2) for obj in obj.get_corners()
        ]

        # Применяем поворот к каждому углу
        corners = []
        for x, y in obj_corners:
            x_rotated = cx + x * cos_val - y * sin_val
            y_rotated = cy + x * sin_val + y * cos_val
            corners.append(Point(x_rotated, y_rotated))

        # получаем левый верхний угол
        min_x = min(map(lambda cor: cor.x, corners))
        min_y = min(map(lambda cor: cor.y, corners))

        # Получаем дельту смещения при повороте
        dx = min_x - obj.x
        dy = min_y - obj.y

        # Вносим правки по расположению
        obj.x += self.x + dx + self.dx
        obj.y += self.y + dy + self.dy

        # Добавляем градус поворота объекта
        obj.rotation = self.rotation

    def placement_zone(self, room):
        """Задает координаты прямоугольника с учетом его поворота"""

        self.rotation = random.choice(ROTATIONS)

        if self.rotation == 0:
            rect = self.create_rectangle()
            self.x = random.uniform(0, room.width - rect.width)
            self.y = 0

        elif self.rotation == 90:
            rect = self.create_rectangle()
            self.x = room.width - rect.width
            self.y = random.uniform(0, room.length - rect.length)

        elif self.rotation == 180:
            rect = self.create_rectangle()
            self.x = random.uniform(0, room.width - self.width)
            self.y = room.length - rect.length

        elif self.rotation == 270:
            rect = self.create_rectangle()
            self.x = 0
            self.y = random.uniform(0, room.length - rect.length)

        return self


class PierGlassZone(ZoneGenerator): ...


class SleepZone(ZoneGenerator): ...


class WardrobeZone(ZoneGenerator): ...
