import uuid
from django.db import models
from django.core.validators import MinValueValidator


class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )

    # Dimensions in mm
    width = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    height = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    # New JSON storage for walls
    walls_data = models.JSONField(default=list, blank=True)

    subscription_id = models.UUIDField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['subscription_id']),
        ]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.name} | {self.status}"

    @property
    def area_sq_m(self):
        return (self.width * self.height) / 1_000_000


class Element(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    width = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    height = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    meta = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.type} ({self.width}x{self.height})"


class ProjectElement(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='placed_elements'
    )
    element = models.ForeignKey(
        Element,
        on_delete=models.CASCADE,
        related_name='instances'
    )
    x = models.IntegerField()
    y = models.IntegerField()
    rotation = models.IntegerField(default=0)
