import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.users.helpers.constants import UserRole


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, db_index=True)

    username = models.CharField(max_length=150, unique=True)

    role = models.CharField(max_length=30, choices=UserRole.choices)

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True)

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"   # primary login field
    REQUIRED_FIELDS = ["email"]    # required for createsuperuser

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
        ]

    def __str__(self):
        return f"{self.username}{self.email}"