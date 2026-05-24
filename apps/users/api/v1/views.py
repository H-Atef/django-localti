from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.users.helpers.constants import UserRole
from apps.users.services.auth_service import AuthService
from apps.users.services.user_service import UserService

from apps.users.api.v1.serializers import (
    UserSerializer,
    UserUpdateSerializer,
    LoginSerializer,
    LoginResponseSerializer,
    LogoutResponseSerializer,
    InfluencerRegisterSerializer,
    MarketerRegisterSerializer,
    LocalBrandRegisterSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Authentication Views
# ---------------------------------------------------------------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        operation_id='auth_register',
        summary='Register a new user',
        description=(
            'Register a new user with a role-specific profile. '
            'Send the `role` field to determine which profile fields are required. '
            'Roles: `influencer`, `marketer`, `local_brand`. Admin registration is restricted.'
        ),
        request={
            'application/json': InfluencerRegisterSerializer,
            'multipart/form-data': InfluencerRegisterSerializer,
        },
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description='Bad request - validation errors'),
            403: OpenApiResponse(description='Forbidden - admin registration restricted'),
        },
    )
    def post(self, request, *args, **kwargs):
        role = request.data.get('role')
        if not role:
            return Response({"role": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        if role == UserRole.ADMIN:
            return Response(
                {"role": ["Admin registration is restricted. Contact system administrator."]}, 
                status=status.HTTP_403_FORBIDDEN
            )

        serializer_class = self._get_serializer_class(role)
        if not serializer_class:
            return Response({"role": [f"Invalid role: '{role}'."]}, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = AuthService.register_user(serializer.validated_data)
        response_serializer = UserSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _get_serializer_class(role):
        mapping = {
            UserRole.INFLUENCER: InfluencerRegisterSerializer,
            UserRole.MARKETER: MarketerRegisterSerializer,
            UserRole.LOCAL_BRAND: LocalBrandRegisterSerializer,
        }
        return mapping.get(role)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        operation_id='auth_login',
        summary='Log in with username or email',
        description='Authenticate using username or email. Returns access token in body and sets refresh token as httpOnly cookie.',
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username_or_email = serializer.validated_data['username']
        password = serializer.validated_data['password']

        auth_data = AuthService.authenticate_user(username_or_email, password)
        user = auth_data['user']
        access_token = auth_data['access']
        refresh_token = auth_data['refresh']

        user_serializer = UserSerializer(user)

        response = Response({
            "user": user_serializer.data,
            "access": access_token
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax'
        )
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        operation_id='auth_logout',
        summary='Log out the current user',
        description='Blacklists the refresh token stored in the httpOnly cookie and deletes the cookie.',
        request=None,
        responses={200: LogoutResponseSerializer},
    )
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        result = AuthService.logout_user(refresh_token)

        response = Response(result, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        return response


@extend_schema(tags=['Auth'], responses={200: OpenApiResponse(description='Refreshed access token')})
class TaggedTokenRefreshView(TokenRefreshView):
    """Refresh access token using the refresh token."""
    pass


# ---------------------------------------------------------------------------
# ✅ User Retrieve APIView - with proper Swagger schema
# ---------------------------------------------------------------------------
@extend_schema(
    tags=['Users'],
    summary='Retrieve user(s)',
    description=(
        'Non-admins: Returns only their own profile.\n'
        'Admins: \n'
        '- No params → returns admin\'s own profile\n'
        '- `?id=<uuid>` → returns specific user by UUID\n'
        '- `?all=true` → returns list of all users'
    ),
    parameters=[
        OpenApiParameter(name='id', description='UUID of user to retrieve (admin only)', type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(name='all', description='Return all users (admin only)', type=bool, location=OpenApiParameter.QUERY),
    ],
    responses={
        200: OpenApiResponse(
            response=UserSerializer(many=True),  # For ?all=true
            description='Single user object OR {"results": [...], "count": N} for ?all=true'
        ),
        404: OpenApiResponse(description='User not found'),
    },
)
class UserRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        if user.role != UserRole.ADMIN:
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return_all = request.query_params.get('all', '').lower() == 'true'
        target_id = request.query_params.get('id')
        
        if return_all:
            users = UserService.list_users()
            serializer = UserSerializer(users, many=True)
            return Response({"results": serializer.data, "count": users.count()}, status=status.HTTP_200_OK)
        
        elif target_id:
            target_user = get_object_or_404(User, id=target_id)
            serializer = UserSerializer(target_user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        else:
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# ✅ User Update APIView - with proper Swagger schema
# ---------------------------------------------------------------------------
@extend_schema(
    tags=['Users'],
    summary='Update user',
    description=(
        'Non-admins: Can only update their own profile.\n'
        'Admins: \n'
        '- No params → updates admin\'s own profile\n'
        '- `?id=<uuid>` → updates specific user by UUID'
    ),
    parameters=[
        OpenApiParameter(name='id', description='UUID of user to update (admin only)', type=str, location=OpenApiParameter.QUERY),
    ],
    request={
        'application/json': UserUpdateSerializer,
        'multipart/form-data': UserUpdateSerializer,
    },
    responses={
        200: UserSerializer,
        400: OpenApiResponse(description='Validation error'),
        404: OpenApiResponse(description='User not found'),
    },
)
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_target_user(self, request):
        user = request.user
        if user.role != UserRole.ADMIN:
            return user
        target_id = request.query_params.get('id')
        if target_id:
            return get_object_or_404(User, id=target_id)
        return user

    def put(self, request, *args, **kwargs):
        return self._update(request, partial=False)

    def patch(self, request, *args, **kwargs):
        return self._update(request, partial=True)

    def _update(self, request, partial=False):
        target_user = self._get_target_user(request)
        serializer = UserUpdateSerializer(target_user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        response_serializer = UserSerializer(updated_user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# ✅ User Delete APIView - with proper Swagger schema
# ---------------------------------------------------------------------------
@extend_schema(
    tags=['Users'],
    summary='Delete user',
    description=(
        'Non-admins: Can only delete their own account.\n'
        'Admins: \n'
        '- No params → deletes admin\'s own account\n'
        '- `?id=<uuid>` → deletes specific user by UUID'
    ),
    parameters=[
        OpenApiParameter(name='id', description='UUID of user to delete (admin only)', type=str, location=OpenApiParameter.QUERY),
    ],
    responses={
        204: OpenApiResponse(description='Successfully deleted'),
        404: OpenApiResponse(description='User not found'),
    },
)
class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_target_user(self, request):
        user = request.user
        if user.role != UserRole.ADMIN:
            return user
        target_id = request.query_params.get('id')
        if target_id:
            return get_object_or_404(User, id=target_id)
        return user

    def delete(self, request, *args, **kwargs):
        target_user = self._get_target_user(request)
        UserService.delete_user(target_user)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# ✅ Influencer Search View - with proper Swagger schema
# ---------------------------------------------------------------------------
@extend_schema(
    tags=['Influencers'],
    summary='Search influencers',
    description='Search influencers by name, category, niche, or any combination.',
    parameters=[
        OpenApiParameter(name='name', description='Filter by influencer name', type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(name='category', description='Filter by category', type=str, location=OpenApiParameter.QUERY),
        OpenApiParameter(name='niche', description='Filter by niche', type=str, location=OpenApiParameter.QUERY),
    ],
    responses={
        200: OpenApiResponse(response=UserSerializer(many=True), description='List of matching influencers'),
    },
)
class InfluencerSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        name = request.query_params.get('name')
        category = request.query_params.get('category')
        niche = request.query_params.get('niche')

        influencers = UserService.search_influencers(name=name, category=category, niche=niche)
        serializer = UserSerializer(influencers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)