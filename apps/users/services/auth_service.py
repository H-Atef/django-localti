from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.repositories.user_repository import UserRepository
from apps.users.helpers.constants import UserRole


class AuthService:

    @staticmethod
    @transaction.atomic
    def register_user(validated_data):
        role = validated_data.get("role")
        user_fields = ["username", "email", "password", "phone_number", "avatar", "role"]

        # Extract user specific data
        user_data = {k: validated_data[k] for k in user_fields if k in validated_data}

        # Extract profile specific data
        profile_data = {k: v for k, v in validated_data.items() if k not in user_fields}

        user = UserRepository.create_user_with_profile(user_data, profile_data, role)
        return user

    @staticmethod
    def authenticate_user(username_or_email, password):
        user = UserRepository.get_user_by_username_or_email(username_or_email)
        if not user or not user.check_password(password):
            raise AuthenticationFailed("Invalid username/email or password.")

        refresh = RefreshToken.for_user(user)
        return {
            "user": user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def logout_user(refresh_token):
        """Blacklist refresh token to log out user"""
        if not refresh_token:
            raise AuthenticationFailed('No refresh token found in cookies.')
        try:
            outstanding_token = OutstandingToken.objects.get(token=refresh_token)
            BlacklistedToken.objects.create(token=outstanding_token)
            return {"message": "You have successfully logged out!"}
        except ObjectDoesNotExist:
            raise AuthenticationFailed('Refresh token does not exist in OutstandingToken.')
        except Exception as e:
            raise AuthenticationFailed(f'message : error occurred while logging out process')
