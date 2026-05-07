from django.db import transaction
from rest_framework import serializers

from .models import Element, Project, ProjectElement


class ElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = ["id", "name", "type", "width", "height", "meta"]
        read_only_fields = ["id"]


class ProjectElementSerializer(serializers.ModelSerializer):
    details = ElementSerializer(source="element", read_only=True)
    element_id = serializers.PrimaryKeyRelatedField(
        queryset=Element.objects.all(), source="element", write_only=True
    )

    class Meta:
        model = ProjectElement
        fields = ["element_id", "details", "x", "y", "rotation"]


class ProjectSerializer(serializers.ModelSerializer):
    elements = ProjectElementSerializer(many=True, required=False, source="placed_elements")

    class Meta:
        model = Project
        fields = ["id", "name", "width", "height", "walls_data", "elements", "created_at"]
        read_only_fields = ["id", "created_at"]

    @transaction.atomic
    def create(self, validated_data):
        elements_data = validated_data.pop("placed_elements", [])

        project = Project.objects.create(**validated_data)

        if elements_data:
            ProjectElement.objects.bulk_create(
                [ProjectElement(project=project, **e) for e in elements_data]
            )

        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        elements_data = validated_data.pop("placed_elements", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if elements_data is not None:
            instance.placed_elements.all().delete()
            ProjectElement.objects.bulk_create(
                [ProjectElement(project=instance, **e) for e in elements_data]
            )

        return instance
