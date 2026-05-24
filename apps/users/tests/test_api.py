from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, InfluencerProfile
from apps.users.helpers.constants import UserRole


class UserAPITest(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpassword",
            role=UserRole.ADMIN
        )
        self.influencer_user = User.objects.create_user(
            username="influencer1",
            email="influencer1@example.com",
            password="password123",
            role=UserRole.INFLUENCER
        )
        InfluencerProfile.objects.create(
            user=self.influencer_user,
            niche="travel",
            category="vlog"
        )
        self.marketer_user = User.objects.create_user(
            username="marketer1",
            email="marketer1@example.com",
            password="password123",
            role=UserRole.MARKETER
        )

    # ==================== REGISTRATION ====================
    def test_registration_api_success(self):
        url = reverse('users_v1:register')
        data = {
            "username": "new_influencer",
            "email": "new_inf@example.com",
            "password": "securepassword",
            "role": UserRole.INFLUENCER,
            "niche": "gaming",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], "new_influencer")

    def test_registration_admin_role_rejected(self):
        url = reverse('users_v1:register')
        data = {
            "username": "fake_admin",
            "email": "fake_admin@example.com",
            "password": "securepassword",
            "role": UserRole.ADMIN,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Admin registration is restricted", response.data.get("role", [""])[0])

    # ==================== RETRIEVE ====================
    def test_retrieve_non_admin_gets_self(self):
        url = reverse('users_v1:user-retrieve')
        self.client.force_authenticate(user=self.influencer_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.influencer_user.id))

    def test_retrieve_admin_no_params_gets_self(self):
        url = reverse('users_v1:user-retrieve')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.admin_user.id))

    def test_retrieve_admin_with_id_param(self):
        url = reverse('users_v1:user-retrieve')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f"{url}?id={self.influencer_user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.influencer_user.id))
        self.assertEqual(response.data['profile']['niche'], "travel")

    def test_retrieve_admin_with_all_param(self):
        url = reverse('users_v1:user-retrieve')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f"{url}?all=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertTrue(len(response.data['results']) >= 3)

    def test_retrieve_non_admin_ignores_id_param(self):
        """Non-admins cannot access other users even with ID param"""
        url = reverse('users_v1:user-retrieve')
        self.client.force_authenticate(user=self.influencer_user)
        # Pass marketer's ID - should still return influencer's own data
        response = self.client.get(f"{url}?id={self.marketer_user.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.influencer_user.id))  # Still self

    # ==================== UPDATE ====================
    def test_update_non_admin_self(self):
        url = reverse('users_v1:user-update')
        self.client.force_authenticate(user=self.influencer_user)
        response = self.client.patch(url, {"username": "updated_influencer"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], "updated_influencer")

    def test_update_admin_self_no_params(self):
        url = reverse('users_v1:user-update')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(url, {"username": "updated_admin"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], "updated_admin")

    def test_update_admin_other_user_with_id(self):
        url = reverse('users_v1:user-update')
        self.client.force_authenticate(user=self.admin_user)
        # Pass ID as query param in URL, not in body
        response = self.client.patch(
            f"{url}?id={self.marketer_user.id}", 
            {"username": "admin_updated_marketer"}, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.marketer_user.refresh_from_db()
        self.assertEqual(self.marketer_user.username, "admin_updated_marketer")

    def test_update_non_admin_ignores_id_param(self):
        """Non-admins cannot update others even with ID param"""
        url = reverse('users_v1:user-update')
        self.client.force_authenticate(user=self.influencer_user)
        # Query param in URL, data in body
        response = self.client.patch(
            f"{url}?id={self.marketer_user.id}", 
            {"username": "hacked"}, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have updated self, not marketer
        self.influencer_user.refresh_from_db()
        self.assertEqual(self.influencer_user.username, "hacked")
        self.marketer_user.refresh_from_db()
        self.assertEqual(self.marketer_user.username, "marketer1")  # Unchanged

    # ==================== DELETE ====================
    def test_delete_non_admin_self(self):
        url = reverse('users_v1:user-delete')
        self.client.force_authenticate(user=self.influencer_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.influencer_user.id).exists())

    def test_delete_admin_self_no_params(self):
        url = reverse('users_v1:user-delete')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.admin_user.id).exists())

    def test_delete_admin_other_user_with_id(self):
        url = reverse('users_v1:user-delete')
        self.client.force_authenticate(user=self.admin_user)
        # ID must be in URL query string for DELETE
        response = self.client.delete(f"{url}?id={self.marketer_user.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.marketer_user.id).exists())

    def test_delete_non_admin_ignores_id_param(self):
        """Non-admins cannot delete others even with ID param"""
        url = reverse('users_v1:user-delete')
        self.client.force_authenticate(user=self.influencer_user)
        # Query param in URL
        response = self.client.delete(f"{url}?id={self.marketer_user.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Should have deleted self, not marketer
        self.assertFalse(User.objects.filter(id=self.influencer_user.id).exists())
        self.assertTrue(User.objects.filter(id=self.marketer_user.id).exists())

    # ==================== LOGIN/LOGOUT ====================
    def test_login_and_logout_api(self):
        login_url = reverse('users_v1:login')
        logout_url = reverse('users_v1:logout')

        data = {"username": "influencer1@example.com", "password": "password123"}
        response = self.client.post(login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.post(logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "You have successfully logged out!")