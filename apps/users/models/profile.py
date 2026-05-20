import uuid
from django.db import models
from apps.users.models.user import User


class InfluencerProfile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="influencer_profile",
    )

    bio = models.TextField(blank=True, null=True)

    niche = models.CharField(max_length=100,blank=True,default="-")

    followers_count = models.PositiveIntegerField(default=0)

    instagram_url = models.URLField(blank=True, null=True)
    tiktok_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)

    engagement_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "influencer_profiles"


class MarketerProfile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="marketer_profile",
    )

    agency_name = models.CharField(max_length=255, blank=True, null=True)

    years_of_experience = models.PositiveIntegerField(default=0)

    specialization = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "marketer_profiles"


class LocalBrandProfile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="brand_profile",
    )

    brand_name = models.CharField(max_length=255)

    business_type = models.CharField(max_length=100)

    website = models.URLField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    location = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "local_brand_profiles"