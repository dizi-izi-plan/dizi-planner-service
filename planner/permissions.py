from rest_framework import permissions
from .models import Project


class CheckProjectLimit(permissions.BasePermission):
    message = "Лимит тарифа закончен. Создание проекта невозможно."

    def has_permission(self, request, view):
        if request.method != 'POST':
            return True

        sub = getattr(request, 'subscription_data', None)
        owner_id = getattr(request, 'owner_id', None)

        if not owner_id:
            return False

        allowed_limit = 1
        if sub and isinstance(sub, dict) and 'tariff' in sub:
            allowed_limit = sub['tariff'].get('project_limit', 1)

        current_count = Project.objects.filter(owner=owner_id).count()
        return current_count < allowed_limit
