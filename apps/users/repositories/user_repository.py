from django.db import transaction
from django.db.models import Q
from apps.users.models import (
    User,
    InfluencerProfile,
    MarketerProfile,
    LocalBrandProfile,
)
from apps.users.helpers.constants import UserRole


class UserRepository:
    
    ROLE_TO_PROFILE = {
        UserRole.INFLUENCER: InfluencerProfile,
        UserRole.MARKETER: MarketerProfile,
        UserRole.LOCAL_BRAND: LocalBrandProfile,
    }

    @staticmethod
    def get_user_by_id(user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_username_or_email(username_or_email):
        try:
            field = 'email' if '@' in username_or_email else 'username'
            return User.objects.get(**{field: username_or_email})
        except User.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_user_with_profile(user_data, profile_data, role):
        password = user_data.pop("password", None)
        user = User.objects.create_user(password=password, **user_data)

        if profile_model := UserRepository.ROLE_TO_PROFILE.get(role):
            profile_model.objects.create(user=user, **profile_data)
        
        return user

    @staticmethod
    @transaction.atomic
    def update_user(user, user_data):
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def update_profile(user, profile_data):
        profile_model = UserRepository.ROLE_TO_PROFILE.get(user.role)
        
        if not profile_model:
            return None
        
        profile, _ = profile_model.objects.get_or_create(user=user)
        
        for field, value in profile_data.items():
            setattr(profile, field, value)
        
        profile.save()
        return profile

    @staticmethod
    def delete_user(user):
        user.delete()

    @staticmethod
    def list_users():
        return User.objects.all()

    @staticmethod
    def search_influencers(name=None, category=None, niche=None):
        queryset = User.objects.filter(
            role=UserRole.INFLUENCER
        ).select_related('influencer_profile')

        if name:
            queryset = queryset.filter(
                Q(username__icontains=name) |
                Q(first_name__icontains=name) |
                Q(last_name__icontains=name)
            )
        
        if category:
            queryset = queryset.filter(
                influencer_profile__category__icontains=category
            )
        
        if niche:
            queryset = queryset.filter(
                influencer_profile__niche__icontains=niche
            )

        return queryset