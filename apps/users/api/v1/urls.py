from django.urls import path
from apps.users.api.v1.views import (
    RegisterView,
    LoginView,
    LogoutView,
    TaggedTokenRefreshView,
    UserRetrieveView,
    UserUpdateView,
    UserDeleteView,
    InfluencerSearchView,
)

app_name = 'users_v1'

urlpatterns = [
   
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TaggedTokenRefreshView.as_view(), name='token_refresh'),
    
    path('', UserRetrieveView.as_view(), name='user-retrieve'),     
    path('update/', UserUpdateView.as_view(), name='user-update'),          
    path('delete/', UserDeleteView.as_view(), name='user-delete'),          
    
    # Influencer search
    path('influencers/search/', InfluencerSearchView.as_view(), name='influencer_search'),
]