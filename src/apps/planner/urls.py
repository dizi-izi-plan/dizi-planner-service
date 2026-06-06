from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ElementViewSet, GenerateLayoutView, ProjectViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"elements", ElementViewSet, basename="element")

urlpatterns = [
    path("generate/", GenerateLayoutView.as_view(), name="generate-layout"),
    path("", include(router.urls)),
]
