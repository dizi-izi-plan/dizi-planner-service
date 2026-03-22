from django.db import transaction
from rest_framework import serializers
from .models import Project, Wall, Element, ProjectElement


class WallSerializer(serializers.ModelSerializer):
    length = serializers.ReadOnlyField()

    class Meta:
        model = Wall
        fields = ['id', 'x1', 'y1', 'x2', 'y2', 'thickness', 'length']
        read_only_fields = ['id']


class ElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = ['id', 'type', 'width', 'height', 'meta']


class ProjectElementSerializer(serializers.ModelSerializer):
    details = ElementSerializer(source='element', read_only=True)
    element_id = serializers.PrimaryKeyRelatedField(
        queryset=Element.objects.all(),
        source='element',
        write_only=True
    )

    class Meta:
        model = ProjectElement
        fields = ['element_id', 'details', 'x', 'y', 'rotation']


class ProjectSerializer(serializers.ModelSerializer):
    area_sq_m = serializers.ReadOnlyField()
    walls = WallSerializer(many=True, required=False)
    elements = ProjectElementSerializer(many=True, required=False, source='placed_elements')

    class Meta:
        model = Project
        fields = ['id', 'name', 'status', 'width', 'height', 'area_sq_m', 'walls', 'elements', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

    @transaction.atomic
    def create(self, validated_data):
        walls_data = validated_data.pop('walls', [])
        elements_data = validated_data.pop('placed_elements', [])

        project = Project.objects.create(**validated_data)

        Wall.objects.bulk_create([Wall(project=project, **w) for w in walls_data])

        ProjectElement.objects.bulk_create([
            ProjectElement(project=project, **e) for e in elements_data
        ])

        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        walls_data = validated_data.pop('walls', None)
        elements_data = validated_data.pop('placed_elements', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if walls_data is not None:
            instance.walls.all().delete()
            Wall.objects.bulk_create([Wall(project=instance, **w) for w in walls_data])

        if elements_data is not None:
            instance.placed_elements.all().delete()
            ProjectElement.objects.bulk_create([
                ProjectElement(project=instance, **e) for e in elements_data
            ])

        return instance
