from django.contrib import admin

from .models import Element, Project, ProjectElement


class ProjectElementInline(admin.TabularInline):
    model = ProjectElement
    extra = 0
    fields = ("element", "x", "y", "rotation")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    list_filter = ("created_at",)
    inlines = [ProjectElementInline]


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "width", "height")
    search_fields = ("type",)


@admin.register(ProjectElement)
class ProjectElementAdmin(admin.ModelAdmin):
    list_display = ("project", "element", "x", "y", "rotation")
    list_filter = ("project", "element__type")
