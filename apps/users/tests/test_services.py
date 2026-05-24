from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User, InfluencerProfile, MarketerProfile, LocalBrandProfile
from apps.users.helpers.constants import UserRole
from apps.users.services.auth_service import AuthService
from apps.users.services.user_service import UserService


class AuthServiceTest(TestCase):

    def test_register_influencer(self):
        data = {
            "username": "influencer_user",
            "email": "influencer@example.com",
            "password": "securepassword123",
            "role": UserRole.INFLUENCER,
            "niche": "fashion",
            "category": "lifestyle",
            "followers_count": 5000,
        }
        user = AuthService.register_user(data)
        self.assertEqual(user.username, "influencer_user")
        self.assertEqual(user.role, UserRole.INFLUENCER)
        
        # Check profile was created
        profile = InfluencerProfile.objects.get(user=user)
        self.assertEqual(profile.niche, "fashion")
        self.assertEqual(profile.category, "lifestyle")
        self.assertEqual(profile.followers_count, 5000)

    def test_register_marketer(self):
        data = {
            "username": "marketer_user",
            "email": "marketer@example.com",
            "password": "securepassword123",
            "role": UserRole.MARKETER,
            "agency_name": "Mega Marketing",
            "years_of_experience": 4,
        }
        user = AuthService.register_user(data)
        self.assertEqual(user.username, "marketer_user")
        self.assertEqual(user.role, UserRole.MARKETER)

        # Check profile was created
        profile = MarketerProfile.objects.get(user=user)
        self.assertEqual(profile.agency_name, "Mega Marketing")
        self.assertEqual(profile.years_of_experience, 4)

    def test_register_local_brand(self):
        data = {
            "username": "brand_user",
            "email": "brand@example.com",
            "password": "securepassword123",
            "role": UserRole.LOCAL_BRAND,
            "brand_name": "Local Coffee",
            "business_type": "Food & Beverage",
        }
        user = AuthService.register_user(data)
        self.assertEqual(user.username, "brand_user")
        self.assertEqual(user.role, UserRole.LOCAL_BRAND)

        # Check profile was created
        profile = LocalBrandProfile.objects.get(user=user)
        self.assertEqual(profile.brand_name, "Local Coffee")
        self.assertEqual(profile.business_type, "Food & Beverage")

    def test_authenticate_user_username_and_email(self):
        user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="mypassword",
            role=UserRole.ADMIN
        )

        # Auth with username
        auth_data_username = AuthService.authenticate_user("testuser", "mypassword")
        self.assertEqual(auth_data_username["user"], user)
        self.assertIn("access", auth_data_username)

        # Auth with email
        auth_data_email = AuthService.authenticate_user("testuser@example.com", "mypassword")
        self.assertEqual(auth_data_email["user"], user)
        self.assertIn("access", auth_data_email)

        # Auth with wrong password
        with self.assertRaises(AuthenticationFailed):
            AuthService.authenticate_user("testuser", "wrongpassword")

    def test_logout_user(self):
        user = User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="password",
            role=UserRole.INFLUENCER
        )
        refresh = RefreshToken.for_user(user)
        refresh_token_str = str(refresh)

        # Retrieve outstanding token (automatically created by simplejwt)
        outstanding = OutstandingToken.objects.get(token=refresh_token_str)

        result = AuthService.logout_user(refresh_token_str)
        self.assertEqual(result["message"], "You have successfully logged out!")

        # Verify token is blacklisted
        self.assertTrue(BlacklistedToken.objects.filter(token=outstanding).exists())

        # Test with non-existent token
        with self.assertRaises(AuthenticationFailed):
            AuthService.logout_user("nonexistenttoken")

        # Test with empty token
        with self.assertRaises(AuthenticationFailed):
            AuthService.logout_user("")


class UserServiceTest(TestCase):

    def test_search_influencers(self):
        user1 = User.objects.create_user(
            username="fashion_icon",
            email="icon@example.com",
            password="password",
            role=UserRole.INFLUENCER
        )
        InfluencerProfile.objects.create(user=user1, niche="fashion", category="beauty")

        user2 = User.objects.create_user(
            username="tech_guru",
            email="guru@example.com",
            password="password",
            role=UserRole.INFLUENCER
        )
        InfluencerProfile.objects.create(user=user2, niche="tech", category="education")

        user3 = User.objects.create_user(
            username="marketer_guy",
            email="marketer@example.com",
            password="password",
            role=UserRole.MARKETER
        )
        # Marketer has no influencer profile

        # Search by name
        results = UserService.search_influencers(name="fashion")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], user1)

        # Search by niche
        results = UserService.search_influencers(niche="tech")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], user2)

        # Search by category
        results = UserService.search_influencers(category="beauty")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], user1)

        # Search mixture
        results = UserService.search_influencers(name="guru", niche="tech")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], user2)
