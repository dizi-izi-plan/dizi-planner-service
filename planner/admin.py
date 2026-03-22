from django.contrib import admin
from .models import Project, Wall, Element, ProjectElement

class ProjectElementInline(admin.TabularInline):
    model = ProjectElement
    extra = 0
    fields = ('element', 'x', 'y', 'rotation')

class WallInline(admin.TabularInline):
    model = Wall
    extra = 0

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [WallInline, ProjectElementInline]

@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'width', 'height')
    search_fields = ('type',)

@admin.register(Wall)
class WallAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'length')

@admin.register(ProjectElement)
class ProjectElementAdmin(admin.ModelAdmin):
    list_display = ('project', 'element', 'x', 'y', 'rotation')
    list_filter = ('project', 'element__type')
