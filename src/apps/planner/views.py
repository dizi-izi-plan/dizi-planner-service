from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets

from .models import Element, Project
from .permissions import CheckProjectLimit
from .serializers import ElementSerializer, ProjectSerializer


class IsProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        current_owner_id = getattr(request, "owner_id", None)
        if not current_owner_id:
            return False

        if isinstance(obj, Project):
            return str(obj.owner) == str(current_owner_id)

        return str(obj.project.owner) == str(current_owner_id)


class ElementViewSet(viewsets.ModelViewSet):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]

        return [permission() for permission in permission_classes]


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [CheckProjectLimit, IsProjectOwner]

    def get_queryset(self):
        owner_id = getattr(self.request, "owner_id", None)
        return Project.objects.filter(owner=owner_id).prefetch_related("placed_elements__element")

    def perform_create(self, serializer):
        owner_id = getattr(self.request, "owner_id", None)
        sub_data = getattr(self.request, "subscription_data", None)
        sub_id = sub_data.get("id") if sub_data else None

        serializer.save(owner=owner_id, subscription_id=sub_id)
