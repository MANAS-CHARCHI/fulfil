from django.db import models
from django.db.models.functions import Lower


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