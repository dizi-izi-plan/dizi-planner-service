# Dizi Planner Service

Микросервис для управления планировками интерьеров.

## Установка и настройка

### Требования
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker (для локальной БД)

### Первый запуск

```bash
uv sync                                    # зависимости (создаст .venv)
uv run pre-commit install                  # pre-commit хук на форматирование
cp .env.example .env                       # окружение
docker compose up -d                       # postgres в контейнере
uv run python src/manage.py migrate        # миграции
uv run python src/manage.py runserver      # dev-сервер на :8000
```

### Полезные команды

```bash
uv run pytest                              # тесты
uv run ruff format src                     # форматирование
uv run ruff check src                      # линт
uv run pre-commit run --all-files          # прогнать хук на всём проекте
uv run pre-commit autoupdate               # обновить версии хуков
```

---

Документация эндпоинтов для управления элементами интерьера и дизайн-проектами.

## Общая информация
- **Базовый URL:** `/api/v1/`
- **Формат данных:** JSON
- **Аутентификация:** Bearer JWT Token (необходим для управления проектами и администрирования элементов).

---

## 1. Элементы каталога (Elements)

Эндпоинты для управления базовыми моделями мебели и конструкций.

### Получение списка элементов
`GET /elements/`

**Параметры фильтрации:**
- `type` (string): Фильтрация по типу объекта (например, `table`, `chair`, `wall`).

*Пример запроса:*
`GET /api/v1/elements/?type=table`

### Получение деталей элемента
`GET /elements/{id}/`

### Управление каталогом (Только для Admin)
`POST /elements/` | `PATCH /elements/{id}/` | `DELETE /elements/{id}/`

**Тело запроса (JSON):**
```json
{
  "name": "Стол обеденный",
  "type": "table",
  "width": 1200,
  "height": 800,
  "meta": {
    "material": "oak",
    "color": "natural"
  }
}
```

2. Проекты (Projects)
Управление пользовательскими планировками. Доступ к проектам ограничен их владельцем (owner_id из JWT).

### Список и создание проектов

`GET /projects/ — Список проектов текущего пользователя.`

`POST /projects/ — Создание нового проекта.`

### Работа с конкретным проектом

`GET /projects/{id}/ — Получение данных проекта.`

`PATCH /projects/{id}/ — Частичное обновление (редактирование).`

`DELETE /projects/{id}/ — Удаление проекта.`

### Структура данных проекта (Body)

При создании или обновлении проекта передается геометрия стен и массив расставленных элементов.

Пример запроса на обновление (PATCH):

```json
{
  "name": "Мой проект 2",
  "width": 10000,
  "height": 10000,
  "walls_data": [
    {"x1": 800, "y1": 1200, "x2": 4400, "y2": 1200, "thickness": 200},
    {"x1": 4400, "y1": 1200, "x2": 4400, "y2": 400, "thickness": 200}
  ],
  "elements": [
    {
      "element_id": "e2f860bd-d6bf-41c7-8732-7158bf8b3814",
      "x": 1500,
      "y": 2400,
      "rotation": 90
    },
    {
      "element_id": "d0455aef-744f-47b0-8f98-4880f872d3fe",
      "x": 3000,
      "y": 1200,
      "rotation": 0
    }
  ]
}
```
Описание полей:
- walls_data: Список объектов с координатами начала (x1, y1) и конца (x2, y2) каждой стены в миллиметрах.

- elements: Массив установленной мебели.

- element_id: UUID объекта из базового каталога.

- x, y: Координаты установки верхнего левого угла объекта.

- rotation: Угол поворота в градусах.

---

## 3. Генерация раскладки (Layout Generation)

Автоматическая расстановка мебели в комнате. Эндпоинт **stateless** — ничего не сохраняет в БД, принимает геометрию комнаты и список объектов, возвращает готовую раскладку.

`POST /generate/`

**Авторизация:** управляется флагом `GENERATE_LAYOUT_REQUIRE_AUTH` (env). При `True` требуется Bearer JWT; при `False` эндпоинт открыт (удобно для отладки фронта).

### Формат ответа

Задаётся query-параметром `?format=`:

| Значение | Content-Type | Результат |
|----------|--------------|-----------|
| `json` (по умолчанию) | `application/json` | Координаты объектов |
| `svg` | `image/svg+xml` | Векторная отрисовка |
| `png` | `image/png` | Растровая отрисовка |

### Тело запроса (Body)

```json
{
  "room": {"width": 400, "length": 500, "height": 200},
  "doors": [
    {"id": "1", "name": "дверь", "x": 400, "y": 250, "width": 60, "length": 5, "height": 200}
  ],
  "windows": [
    {"id": "3", "name": "окно", "x": 200, "y": 0, "width": 180, "length": 10, "height": 120}
  ],
  "floor_objects": [
    {"id": "1", "name": "Кровать", "tag": "sz", "dimension": "large_furniture", "width": 180, "length": 200, "height": 40},
    {"id": "2", "name": "Шкаф",    "tag": "wz", "dimension": "large_furniture", "width": 120, "length": 60,  "height": 200},
    {"id": "3", "name": "Стол",    "tag": "pz", "dimension": "large_furniture", "width": 90,  "length": 60,  "height": 60},
    {"id": "4", "name": "Стул",    "tag": "sz", "dimension": "medium_furniture", "width": 60, "length": 40,  "height": 30},
    {"id": "5", "name": "Тумба",   "tag": "sz", "dimension": "medium_furniture", "width": 100, "length": 50, "height": 40},
    {"id": "6", "name": "Тумба",   "tag": "sz", "dimension": "medium_furniture", "width": 100, "length": 50, "height": 40}
  ]
}
```

Описание полей:
- `room`: габариты комнаты в сантиметрах (`width`, `length`, `height`).
- `doors` / `windows`: проёмы (необязательны). `x`, `y` — положение на стене; алгоритм определяет стену по координате.
- `floor_objects`: мебель для расстановки.
  - `dimension`: `large_furniture` (формирует зону) или `medium_furniture` (распределяется вокруг крупных).
  - `tag`: тип зоны (`sz` — сон, `wz` — шкаф, `pz` — туалетный столик).

### Структура ответа (JSON)

```json
{
  "room": {"width": 400, "length": 500, "height": 200},
  "doors": [ ... ],
  "windows": [ ... ],
  "furnitures": [
    {"id": "1", "name": "Кровать", "tag": "sz", "dimension": "large_furniture",
     "x": 0.0, "y": 328.56, "width": 180, "length": 200, "height": 40, "rotation": 270}
  ],
  "electricity_points": [ ... ]
}
```
Координаты `x`, `y` — левый верхний угол объекта, `rotation` — поворот в градусах (0/90/180/270). Розетки (`electricity_points`) генерируются автоматически.

### Коды ответов
- `200` — успех.
- `400` — ошибка валидации входных данных (`{"errors": [...]}`) или неподдерживаемый `format`.
- `422` — данные валидны, но алгоритму не удалось разместить объекты (раскладка рандомизирована — можно повторить запрос).
- `403` — требуется авторизация.

### Примеры curl

**JSON:**
```bash
curl -X POST 'http://localhost:8000/api/v1/generate/' \
  -H 'Content-Type: application/json' \
  -d @payload.json
```

**SVG / PNG в файл:**
```bash
curl -X POST 'http://localhost:8000/api/v1/generate/?format=svg' \
  -H 'Content-Type: application/json' -d @payload.json -o layout.svg

curl -X POST 'http://localhost:8000/api/v1/generate/?format=png' \
  -H 'Content-Type: application/json' -d @payload.json --output layout.png
```

**С авторизацией** (если `GENERATE_LAYOUT_REQUIRE_AUTH=True`):
```bash
curl -X POST 'http://localhost:8000/api/v1/generate/' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d @payload.json
```

> `payload.json` — тело запроса из примера выше.
