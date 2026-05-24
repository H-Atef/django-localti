from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from apps.users.models import User, InfluencerProfile
from apps.users.helpers.constants import UserRole


class UserAPITest(APITestCase):

    def setUp(self):
        # Create an admin user
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpassword",
            role=UserRole.ADMIN
        )

        # Create standard user (influencer)
        self.influencer_user = User.objects.create_user(
            username="influencer1",
            email="influencer1@example.com",
            password="password123",
            role=UserRole.INFLUENCER
        )
        self.influencer_profile = InfluencerProfile.objects.create(
            user=self.influencer_user,
            niche="travel",
            category="vlog"
        )

        # Create another standard user (marketer)
        self.marketer_user = User.objects.create_user(
            username="marketer1",
            email="marketer1@example.com",
            password="password123",
            role=UserRole.MARKETER
        )

    def test_registration_api(self):
        url = reverse('users_v1:register')
        data = {
            "username": "new_influencer",
            "email": "new_inf@example.com",
            "password": "securepassword",
            "role": UserRole.INFLUENCER,
            "niche": "gaming",
            "category": "entertainment"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], "new_influencer")
        self.assertEqual(response.data['profile']['niche'], "gaming")

    def test_login_and_logout_api(self):
        login_url = reverse('users_v1:login')
        logout_url = reverse('users_v1:logout')

        # Test login with email
        data = {
            "username": "influencer1@example.com",
            "password": "password123"
        }
        response = self.client.post(login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh_token', self.client.cookies)

        # Authenticate client
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test logout
        response = self.client.post(logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "You have successfully logged out!")
        self.assertEqual(self.client.cookies.get('refresh_token').value, '')

    def test_get_users_list_permissions(self):
        list_url = reverse('users_v1:user-list')

        # Unauthorized
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated as standard user
        self.client.force_authenticate(user=self.influencer_user)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only list self
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.influencer_user.id))

        # Authenticated as admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should list all users
        self.assertTrue(len(response.data['results']) >= 3)

    def test_me_endpoint(self):
        me_url = reverse('users_v1:user-me')

        # Authenticated as standard user
        self.client.force_authenticate(user=self.influencer_user)
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.influencer_user.id))
        self.assertEqual(response.data['profile']['niche'], "travel")

        # Update via 'me'
        update_data = {
            "username": "influencer_updated",
            "profile": {
                "niche": "photography"
            }
        }
        response = self.client.patch(me_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], "influencer_updated")
        self.assertEqual(response.data['profile']['niche'], "photography")

        # Delete self via 'me'
        response = self.client.delete(me_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.influencer_user.id).exists())

    def test_influencer_search(self):
        search_url = reverse('users_v1:influencer_search')
        self.client.force_authenticate(user=self.marketer_user)

        response = self.client.get(search_url, {"niche": "travel"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.influencer_user.id))
