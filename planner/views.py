from rest_framework import viewsets, permissions

from .models import Project, Wall, Element
from .permissions import CheckProjectLimit
from .serializers import ProjectSerializer, WallSerializer, ElementSerializer


class IsProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        current_owner_id = getattr(request, 'owner_id', None)
        if not current_owner_id:
            return False

        if isinstance(obj, Project):
            return str(obj.owner_id) == str(current_owner_id)

        return str(obj.project.owner_id) == str(current_owner_id)


class WallViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WallSerializer
    permission_classes = [IsProjectOwner]

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        return Wall.objects.filter(
            project_id=project_id,
            project__owner_id=self.request.owner_id
        )


class ElementViewSet(viewsets.ModelViewSet):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [CheckProjectLimit, IsProjectOwner]

    def get_queryset(self):
        owner_id = getattr(self.request, 'owner_id', None)
        return Project.objects.filter(owner=owner_id).prefetch_related(
            'walls',
            'placed_elements__element'
        )

    def perform_create(self, serializer):
        owner_id = getattr(self.request, 'owner_id', None)
        sub_data = getattr(self.request, 'subscription_data', None)

        sub_id = sub_data.get('id') if sub_data else None

        serializer.save(owner=owner_id, subscription_id=sub_id)
