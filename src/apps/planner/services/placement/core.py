import itertools
import random
from copy import deepcopy

from apps.planner.services.placement.constants import ROTATIONS
from apps.planner.services.placement.objects import (
    FloorObject,
    OpeningObject,
    Room,
    Wall,
    ZoneGenerator,
)
from apps.planner.services.placement.sandbox import intersects_checks
from apps.planner.services.placement.validators import validate_constructor


class Core:
    """Основной алгоритм"""

    def __init__(self, room_data, doors_data, windows_data, floor_objects_data):

        self.room_data = room_data
        self.doors_data = doors_data
        self.windows_data = windows_data
        self.floor_objects_data = floor_objects_data

        val = validate_constructor(
            {
                "room": self.room_data,
                "doors": self.doors_data,
                "windows": self.windows_data,
                "floor_objects": self.floor_objects_data,
            }
        )
        if not val:
            self.floor_objects_data.sort(key=lambda x: x["width"] * x["length"], reverse=True)

            self.get_room = self.get_room()
            self.get_walls = self.get_walls()

            self.get_openings = self.get_openings()
            self.get_floor_objects = self.get_floor_objects()
            self.get_zones = self.get_zones()
        else:
            print(*val)

    def get_room(self):
        """Создаем объект комнаты"""

        room = Room(
            self.room_data["width"],
            self.room_data["length"],
            self.room_data["height"],
        )
        self.room = room

        return room

    def get_openings(self) -> list[OpeningObject]:
        """Создаем список объектов (проёмов)"""

        openings = []

        names_list = list(map(lambda x: x["name"], self.doors_data + self.windows_data))

        # Создаем объекты переданных проёмов если они есть
        for obj in self.doors_data + self.windows_data:
            new_obj = OpeningObject(**obj)
            new_obj.get_rotation(self.room)
            openings.append(new_obj)

        # Создаем дверь если её не передали
        if "дверь" not in names_list:
            random_door = OpeningObject(name="дверь")
            random_door.generate_door_random_placement(self.room, openings)
            random_door.uturn()
            openings.append(random_door)

        # Создаем окно если ее не передали
        if "окно" not in names_list:
            random_window = OpeningObject(name="окно")
            random_window.generate_door_random_placement(self.room, openings)
            random_window.uturn()
            openings.append(random_window)

        for opening in openings:
            wall = list(filter(lambda x: x.rotation == opening.rotation, self.get_walls))[0]
            wall.add_divide(opening)
            wall.openings.append(opening)

        return openings

    def get_floor_objects(self) -> list[FloorObject]:
        """Создаем объекты на полу"""
        objects = []
        for obj in self.floor_objects_data:
            objects.append(FloorObject(**obj))
        return objects

    def get_walls(self):
        """Создаем стены"""
        walls = []

        for rotation in ROTATIONS:
            if rotation in [0, 180]:
                wall = Wall(self.room.width, rotation)
            else:
                wall = Wall(self.room.length, rotation)
            walls.append(wall)
        return walls

    def forced_insertion(self, zone, zone_list):
        """Принудительно размещает зоны"""
        for wall in self.get_walls:
            # Получаем зоны у выбранной стены
            zones_at_wall = list(filter(lambda x: x.rotation == wall.rotation, zone_list)) + [zone]
            other_wall_zones = list(filter(lambda x: x.rotation != wall.rotation, zone_list))
            free_lines = wall.wall_divide
            place_combines = self.generate_distributions(len(free_lines), zones_at_wall)
            correct_placements_list = []

            for comb in place_combines:
                flag = True
                correct_placement = []

                for i in range(len(free_lines)):
                    all_width = sum(map(lambda x: x.width, comb[i]))
                    line_width = max(free_lines[i]) - min(free_lines[i])
                    if all_width >= line_width:
                        flag = False
                        break
                    # Задать положение зон и провести чек на пересечение
                    indent = min(free_lines[i])
                    for zone in comb[i]:
                        if wall.rotation == 0:
                            zone.x = indent
                            zone.y = 0
                        elif wall.rotation == 90:
                            zone.x = self.room.width - zone.length
                            zone.y = indent
                        elif wall.rotation == 180:
                            zone.x = indent
                            zone.y = self.room.length - zone.length
                        elif wall.rotation == 270:
                            zone.x = 0
                            zone.y = indent

                        indent += zone.width
                        zone.rotation = wall.rotation

                        # Проверка пересечений
                        if not intersects_checks(zone, other_wall_zones, self.get_openings):
                            flag = False
                            break
                        else:
                            correct_placement.append(zone)

                if flag:
                    # В correct_placement Лучше добавлять проверенные списки расположения зон
                    correct_placements_list.append(correct_placement)

            if correct_placements_list:
                return random.choice(correct_placements_list), wall.rotation
            else:
                return False, wall.rotation

    def free_space_search(self, zone, added_zones):
        """Ищет свободное место"""

        for wall in self.get_walls:
            free_line = wall.insert_check(zone.width)

            if free_line:
                indent = min(free_line)
                if wall.rotation == 0:
                    zone.x = indent
                    zone.y = 0
                elif wall.rotation == 90:
                    zone.x = self.room.width - zone.length
                    zone.y = indent
                elif wall.rotation == 180:
                    zone.x = indent
                    zone.y = self.room.length - zone.length
                elif wall.rotation == 270:
                    zone.x = 0
                    zone.y = indent

                zone.rotation = wall.rotation

                # Проверяем новое положение на пересечение с другими зонами и проемами
                if intersects_checks(zone, added_zones, self.get_openings):
                    return zone

        return False

    def get_zones(self):
        """Создаем зоны комнаты"""
        # создаем списки элементов по уровню
        large_furniture = list(
            filter(lambda x: x.dimension == "large_furniture", self.get_floor_objects)
        )
        medium_furniture = list(
            filter(lambda x: x.dimension == "medium_furniture", self.get_floor_objects)
        )
        # получаем варианты распределения средних объектов по зонам

        distribution_variants = self.generate_distributions(len(large_furniture), medium_furniture)
        random.shuffle(distribution_variants)
        zones = []

        for obj in large_furniture:
            zones.append(ZoneGenerator(main_object=obj))

        for variant in distribution_variants:
            placement_zones = []

            for i in range(len(zones)):
                zones[i].second_objects = variant[i]
                attempts = 0

                while attempts < 50:
                    zone_copy = deepcopy(zones[i])
                    zone_copy.generate_zone()
                    zone_copy.placement_zone(self.get_room)

                    if not intersects_checks(zone_copy, placement_zones, self.get_openings):
                        # Если случайное расположение не подошло, ищем свободное место
                        new_zone = self.free_space_search(zone_copy, placement_zones)
                        if new_zone:
                            zone_copy = new_zone

                        # Если не нашли свободное место, пытаемся сдвинуть другие области и вставить область
                        else:
                            new_zones, rotation = self.forced_insertion(zone_copy, placement_zones)
                            if new_zones:
                                oth_zones = list(
                                    filter(
                                        lambda x: x.rotation != rotation,
                                        placement_zones,
                                    )
                                )
                                placement_zones = oth_zones + new_zones

                        attempts += 1

                    else:
                        for obj in zone_copy.objects_list:
                            zone_copy.update_object_coords(obj)
                        placement_zones.append(zone_copy)
                        wall = list(
                            filter(
                                lambda x: x.rotation == zone_copy.rotation,
                                self.get_walls,
                            )
                        )[0]
                        wall.add_divide(zone_copy)
                        break

            if len(zones) > len(placement_zones):
                print("Не удалось расположить все объекты!!!")

            else:
                return placement_zones

    def generate_distributions(self, part_count, objects):
        """Комбинирует варианты распределения
        второстепенных объектов по количеству зон"""
        results = []

        def recursive_distribute(remaining_objects, zones_left, current_distribution):
            if zones_left == 1:
                # Остальные объекты идут в последнюю зону,
                # если не превышают лимит
                if len(remaining_objects) <= 4:
                    current_distribution.append(remaining_objects)
                    yield current_distribution
                return
            else:
                max_objects_in_zone = min(4, len(remaining_objects))
                # Для первой зоны выбираем возможные количества объектов
                for count in range(1, max_objects_in_zone + 1):
                    # Генерируем все комбинации из remaining_objects по count
                    for combo in itertools.combinations(remaining_objects, count):
                        remaining = list(remaining_objects)
                        for obj in combo:
                            remaining.remove(obj)
                        # Рекурсия для оставшихся зон
                        yield from recursive_distribute(
                            remaining,
                            zones_left - 1,
                            current_distribution + [list(combo)],
                        )

        # Запускаем рекурсию
        for distribution in recursive_distribute(objects, part_count, []):
            results.append(distribution)

        return results

    def run_algorithm(self):
        """Основной алгоритм"""

        doors = list(filter(lambda obj: obj.name == "дверь", self.get_openings))
        windows = list(filter(lambda obj: obj.name == "окно", self.get_openings))

        zones = self.get_zones

        furnitures = [obj for zone in zones for obj in zone.objects_list if obj.name != "розетка"]
        electricity_points = [
            obj for zone in zones for obj in zone.objects_list if obj.name == "розетка"
        ]

        self.room.doors = doors
        self.room.walls = self.get_walls
        self.room.windows = windows
        self.room.furnitures = furnitures
        self.room.electricity_points = electricity_points

        return zones
