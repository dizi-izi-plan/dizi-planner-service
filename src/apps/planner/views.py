from django.conf import settings
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Element, Project
from .permissions import CheckProjectLimit, HasOwnerId
from .serializers import (
    ElementSerializer,
    GenerateLayoutSerializer,
    ProjectSerializer,
)
from .services.placement.render import render_to_png, render_to_svg
from .services.placement.service import (
    LayoutGenerationError,
    build_core,
    serialize_layout,
)


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


class GenerateLayoutView(APIView):
    """Генерирует и возвращает раскладку мебели (без сохранения в БД).

    Формат ответа задаётся query-параметром ``?format=``:
    ``json`` (по умолчанию), ``svg`` или ``png``.

    Авторизация управляется флагом ``GENERATE_LAYOUT_REQUIRE_AUTH``.
    """

    SUPPORTED_FORMATS = ("json", "svg", "png")

    def get_permissions(self):
        if settings.GENERATE_LAYOUT_REQUIRE_AUTH:
            return [HasOwnerId()]
        return [permissions.AllowAny()]

    def post(self, request):
        fmt = request.query_params.get("format", "json").lower()
        if fmt not in self.SUPPORTED_FORMATS:
            return Response(
                {"detail": f"Неподдерживаемый format. Допустимо: {self.SUPPORTED_FORMATS}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GenerateLayoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            core, errors = build_core(**serializer.validated_data)
        except LayoutGenerationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if fmt == "svg":
            return HttpResponse(render_to_svg(core), content_type="image/svg+xml")
        if fmt == "png":
            return HttpResponse(render_to_png(core), content_type="image/png")

        layout = serialize_layout(core, serializer.validated_data["room"])
        return Response(layout, status=status.HTTP_200_OK)
