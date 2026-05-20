from django.contrib import admin

from apps.users.models import (
    User,
    InfluencerProfile,
    MarketerProfile,
    LocalBrandProfile,
)

MODELS = [
    User,
    InfluencerProfile,
    MarketerProfile,
    LocalBrandProfile,
]

for model in MODELS:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass