from rest_framework import authentication

from .integrations import AuthServiceHelper, SubscriptionClient


class ExternalJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        request.owner_id = AuthServiceHelper.get_user_id_from_jwt(auth_header)

        request.subscription_data = SubscriptionClient.get_subscription_data(auth_header)

        return (None, None)
