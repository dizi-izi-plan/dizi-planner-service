"""Тесты эндпоинта генерации раскладки `POST /api/v1/generate/`."""

import jwt
import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

ROOM = {"width": 400, "length": 500, "height": 200}
DOORS = [{"id": "1", "name": "дверь", "x": 400, "y": 250, "width": 60, "length": 5, "height": 200}]
WINDOWS = [{"id": "3", "name": "окно", "x": 200, "y": 0, "width": 180, "length": 10, "height": 120}]
FLOOR_OBJECTS = [
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

PAYLOAD = {"room": ROOM, "doors": DOORS, "windows": WINDOWS, "floor_objects": FLOOR_OBJECTS}

# Раскладка рандомизирована — повторяем запрос, пока алгоритм не справится.
MAX_ATTEMPTS = 25


@pytest.fixture(autouse=True)
def _no_subscription_call(monkeypatch):
    """Аутентификация дёргает сервис подписок по HTTP — заглушаем."""
    monkeypatch.setattr(
        "apps.planner.auth.SubscriptionClient.get_subscription_data",
        lambda auth_header: {},
    )


@pytest.fixture
def auth_client():
    token = jwt.encode({"sub": "11111111-1111-1111-1111-111111111111"}, "secret", algorithm="HS256")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _generate(client, fmt=None, payload=PAYLOAD):
    url = reverse("generate-layout")
    if fmt:
        url = f"{url}?format={fmt}"
    response = None
    for _ in range(MAX_ATTEMPTS):
        response = client.post(url, data=payload, format="json")
        # 422 — валидные данные, но раскладка не удалась; пробуем ещё раз.
        if response.status_code != 422:
            return response
    return response


def test_generate_json(auth_client):
    """Проверить что при формате по умолчанию возвращается JSON с раскладкой."""
    response = _generate(auth_client)
    assert response.status_code == 200
    data = response.json()
    assert data["room"] == ROOM
    assert len(data["furnitures"]) == 6
    assert len(data["doors"]) == 1
    assert len(data["windows"]) == 1
    assert all({"x", "y", "rotation", "name"} <= set(obj) for obj in data["furnitures"])


def test_generate_svg(auth_client):
    """Проверить что при format=svg возвращается изображение SVG."""
    response = _generate(auth_client, fmt="svg")
    assert response.status_code == 200
    assert response["Content-Type"] == "image/svg+xml"
    body = response.content.decode()
    assert body.startswith("<svg")
    assert "</svg>" in body


def test_generate_png(auth_client):
    """Проверить что при format=png возвращается изображение PNG."""
    response = _generate(auth_client, fmt="png")
    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_unsupported_format(auth_client):
    """Проверить что неподдерживаемый format возвращает 400."""
    url = f"{reverse('generate-layout')}?format=pdf"
    response = auth_client.post(url, data=PAYLOAD, format="json")
    assert response.status_code == 400


def test_validation_error_returns_400(auth_client):
    """Проверить что невалидные входные данные возвращают 400 со списком ошибок."""
    bad_payload = {"room": {"width": 400}, "floor_objects": FLOOR_OBJECTS}
    response = auth_client.post(reverse("generate-layout"), data=bad_payload, format="json")
    assert response.status_code == 400
    assert "errors" in response.json()


@override_settings(GENERATE_LAYOUT_REQUIRE_AUTH=True)
def test_requires_authentication():
    """Проверить что при включённом флаге запрос без токена возвращает 403."""
    response = APIClient().post(reverse("generate-layout"), data=PAYLOAD, format="json")
    assert response.status_code == 403


@override_settings(GENERATE_LAYOUT_REQUIRE_AUTH=False)
def test_auth_can_be_disabled_via_flag():
    """Проверить что при выключенном флаге запрос без токена проходит (200)."""
    # Без токена, но с выключенным флагом — доступ разрешён.
    response = _generate(APIClient())
    assert response.status_code == 200
