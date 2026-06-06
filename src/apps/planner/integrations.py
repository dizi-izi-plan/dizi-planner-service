import httpx
import jwt
from django.conf import settings
from rest_framework import exceptions


class AuthServiceHelper:
    @staticmethod
    def get_user_id_from_jwt(auth_header: str) -> str:
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, options={"verify_signature": False})

            user_id = payload.get("sub") or payload.get("user_id")
            if not user_id:
                raise exceptions.AuthenticationFailed("ID пользователя не найден в токене")
            return user_id
        except (IndexError, jwt.DecodeError):
            raise exceptions.AuthenticationFailed("Некорректный формат токена")


class SubscriptionClient:
    URL = settings.SUBSCRIPTION_SERVICE_URL

    @classmethod
    def get_subscription_data(cls, auth_header: str) -> dict:
        try:
            with httpx.Client() as client:
                response = client.get(cls.URL, headers={"Authorization": auth_header}, timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                return None
        except httpx.RequestError:
            raise exceptions.APIException("Сервис подписок временно недоступен")
