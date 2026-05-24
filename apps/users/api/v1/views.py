from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets, generics, serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.users.helpers.constants import UserRole
from apps.users.permissions import IsAdminOrSelf
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
    AdminRegisterSerializer,
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
            'Roles: `influencer`, `marketer`, `local_brand`, `admin`.'
        ),
        request={
            'multipart/form-data': InfluencerRegisterSerializer 
        },
        responses={201: UserSerializer},
    )
    def post(self, request, *args, **kwargs):
        role = request.data.get('role')
        if not role:
            return Response({"role": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

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
            UserRole.ADMIN: AdminRegisterSerializer,
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

        # Set refresh token as an httpOnly cookie
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
    


@extend_schema(tags=['Auth'])
class TaggedTokenRefreshView(TokenRefreshView):
    """
    Refresh access token using the refresh token (sent as httpOnly cookie or request body).
    """
    pass


# ---------------------------------------------------------------------------
# User CRUD ViewSet
# ---------------------------------------------------------------------------
@extend_schema_view(
    list=extend_schema(
        tags=['Users'],
        summary='List users',
        description='Admins see all users. Non-admins see only themselves.',
    ),
    retrieve=extend_schema(
        tags=['Users'],
        summary='Retrieve a user by ID',
        description='Admins can retrieve any user. Non-admins can only retrieve themselves.',
    ),
    create=extend_schema(
        tags=['Users'],
        summary='Create a user (admin)',
    ),
    update=extend_schema(
        tags=['Users'],
        summary='Full update a user by ID',
        request={
            'multipart/form-data': UserUpdateSerializer  
        },
    ),
    partial_update=extend_schema(
        tags=['Users'],
        summary='Partial update a user by ID',
        request={
            'multipart/form-data': UserUpdateSerializer  
        },
    ),
    destroy=extend_schema(
        tags=['Users'],
        summary='Delete a user by ID',
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrSelf]

    def get_queryset(self):
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return UserService.list_users()
        return UserService.list_users().filter(id=user.id)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        UserService.delete_user(instance)

    @extend_schema(
        tags=['Users'],
        summary='Get / Update / Delete current user (from token)',
        description='Operates on the authenticated user extracted from the JWT. Supports GET, PUT, PATCH, DELETE.',
        methods=['GET'],
        request=None,
        responses={200: UserSerializer},
    )
    @extend_schema(
        tags=['Users'],
        methods=['PUT', 'PATCH'],
        request={
            'multipart/form-data': UserUpdateSerializer  
        },
        responses={200: UserSerializer},
    )
    @extend_schema(
        tags=['Users'],
        methods=['DELETE'],
        request=None,
        responses={204: None},
    )
    @action(detail=False, methods=['get', 'put', 'patch', 'delete'], url_path='me')
    def me(self, request, *args, **kwargs):
        """Endpoint to get/update/delete the authenticated user's own data from token"""
        user = request.user
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method in ['PUT', 'PATCH']:
            partial = (request.method == 'PATCH')
            serializer = UserUpdateSerializer(user, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            updated_user = serializer.save()
            response_serializer = UserSerializer(updated_user)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            UserService.delete_user(user)
            return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Influencer Search View
# ---------------------------------------------------------------------------
@extend_schema(
    tags=['Influencers'],
    summary='Search influencers',
    description='Search influencers by name, category, niche, or any combination.',
    parameters=[
        OpenApiParameter(name='name', description='Filter by influencer name (username, first or last name)', type=str),
        OpenApiParameter(name='category', description='Filter by category', type=str),
        OpenApiParameter(name='niche', description='Filter by niche', type=str),
    ],
)
class InfluencerSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        name = self.request.query_params.get('name')
        category = self.request.query_params.get('category')
        niche = self.request.query_params.get('niche')

        return UserService.search_influencers(name=name, category=category, niche=niche)
