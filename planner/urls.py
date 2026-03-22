from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, WallViewSet, ElementViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'walls', WallViewSet, basename='wall')
router.register(r'elements', ElementViewSet, basename='element')

urlpatterns = [
    path('', include(router.urls)),
]
