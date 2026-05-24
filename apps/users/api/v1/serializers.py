from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from apps.users.models import (
    InfluencerProfile,
    MarketerProfile,
    LocalBrandProfile,
)
from apps.users.helpers.constants import UserRole

User = get_user_model()


# ---------------------------------------------------------------------------
# Profile Serializers
# ---------------------------------------------------------------------------
class InfluencerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfluencerProfile
        fields = [
            'bio', 'niche', 'category', 'followers_count',
            'instagram_url', 'tiktok_url', 'youtube_url', 'engagement_rate'
        ]


class MarketerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketerProfile
        fields = ['agency_name', 'years_of_experience', 'specialization']


class LocalBrandProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalBrandProfile
        fields = ['brand_name', 'business_type', 'website', 'description', 'location']


# ---------------------------------------------------------------------------
# User Serializer
# ---------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    

   
    ROLE_TO_PROFILE = {
        UserRole.INFLUENCER: ('influencer_profile', InfluencerProfileSerializer),
        UserRole.MARKETER: ('marketer_profile', MarketerProfileSerializer),
        UserRole.LOCAL_BRAND: ('brand_profile', LocalBrandProfileSerializer),
    }

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'phone_number',
            'avatar', 'is_verified', 'created_at', 'updated_at',
            'profile'
        ]
        read_only_fields = ['id', 'role', 'is_verified', 'created_at', 'updated_at']

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_profile(self, obj):
        if profile_config := self.ROLE_TO_PROFILE.get(obj.role):
            profile_attr, serializer_class = profile_config
            if hasattr(obj, profile_attr):
                profile = getattr(obj, profile_attr)
                return serializer_class(profile).data
        return None

# ---------------------------------------------------------------------------
# User Update Serializer (Dynamic Nested Validation)
# ---------------------------------------------------------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    profile = serializers.JSONField(required=False)

    
    ROLE_TO_PROFILE = {
        UserRole.INFLUENCER: ('influencer_profile', InfluencerProfileSerializer),
        UserRole.MARKETER: ('marketer_profile', MarketerProfileSerializer),
        UserRole.LOCAL_BRAND: ('brand_profile', LocalBrandProfileSerializer),
    }

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'avatar', 'profile']

    def validate(self, attrs):
        user = self.instance
        profile_data = attrs.get('profile')

        if profile_data is not None and user is not None:
            if profile_config := self.ROLE_TO_PROFILE.get(user.role):
                profile_attr, serializer_class = profile_config
                instance = getattr(user, profile_attr, None)
                
                serializer = serializer_class(
                    instance=instance,
                    data=profile_data,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                attrs['profile'] = serializer.validated_data

        return attrs

    def update(self, instance, validated_data):
        from apps.users.services.user_service import UserService
        return UserService.update_user(instance, validated_data)
    
# ---------------------------------------------------------------------------
# Registration Serializers
# ---------------------------------------------------------------------------
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=UserRole.choices, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number', 'avatar', 'role']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value


class InfluencerRegisterSerializer(UserRegisterSerializer):
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    niche = serializers.CharField(required=False, default="-")
    category = serializers.CharField(required=False, default="-")
    followers_count = serializers.IntegerField(required=False, default=0)
    instagram_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tiktok_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    youtube_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    engagement_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)

    class Meta(UserRegisterSerializer.Meta):
        fields = UserRegisterSerializer.Meta.fields + [
            'bio', 'niche', 'category', 'followers_count',
            'instagram_url', 'tiktok_url', 'youtube_url', 'engagement_rate'
        ]


class MarketerRegisterSerializer(UserRegisterSerializer):
    agency_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    years_of_experience = serializers.IntegerField(required=False, default=0)
    specialization = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta(UserRegisterSerializer.Meta):
        fields = UserRegisterSerializer.Meta.fields + [
            'agency_name', 'years_of_experience', 'specialization'
        ]


class LocalBrandRegisterSerializer(UserRegisterSerializer):
    brand_name = serializers.CharField(required=True)
    business_type = serializers.CharField(required=True)
    website = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    location = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta(UserRegisterSerializer.Meta):
        fields = UserRegisterSerializer.Meta.fields + [
            'brand_name', 'business_type', 'website', 'description', 'location'
        ]


class AdminRegisterSerializer(UserRegisterSerializer):
    class Meta(UserRegisterSerializer.Meta):
        pass


# ---------------------------------------------------------------------------
# Login Serializer
# ---------------------------------------------------------------------------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, help_text="Enter username or email")
    password = serializers.CharField(write_only=True, required=True)


# ---------------------------------------------------------------------------
# Swagger Response Serializers
# ---------------------------------------------------------------------------
class LoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    access = serializers.CharField()


class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
