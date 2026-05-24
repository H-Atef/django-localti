from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.api.v1.views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserViewSet,
    InfluencerSearchView,
    TaggedTokenRefreshView
)

app_name = 'users_v1'

router = DefaultRouter()
router.register('', UserViewSet, basename='user')

urlpatterns = [
    # Auth Endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TaggedTokenRefreshView.as_view(), name='token_refresh'),
    # Search Endpoints
    path('influencers/search/', InfluencerSearchView.as_view(), name='influencer_search'),

    # User CRUD endpoints (ViewSet including 'me')
    path('', include(router.urls)),
]
