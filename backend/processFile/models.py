from django.db import models
from django.db.models.functions import Lower
import uuid

class UploadJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=512)
    status = models.CharField(max_length=32, default="pending")  # pending/processing/staging_loaded/merging/completed/failed
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.status}"
    
class Product(models.Model):
    name = models.CharField(max_length=512, blank=True)
    sku = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('sku'), name='case_insensitive')
        ]
        def __str__(self):
            return f"{self.sku} - {self.name}"