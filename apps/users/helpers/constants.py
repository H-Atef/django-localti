
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    INFLUENCER = "influencer", "Influencer"
    MARKETER = "marketer", "Marketer"
    LOCAL_BRAND = "local_brand", "Local Brand"