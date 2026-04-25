from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class AuthAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_user_can_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newuser",
                "email": "new@test.com",
                "password": "pass123",
                "role": "candidate",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["username"], "newuser")

    def test_user_can_login(self):
        self.client.post(
            "/api/auth/register/",
            {"username": "loginuser", "email": "login@test.com", "password": "pass123"},
        )
        response = self.client.post(
            "/api/auth/login/", {"username": "loginuser", "password": "pass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_login_fails(self):
        response = self.client.post(
            "/api/auth/login/", {"username": "nonexistent", "password": "wrong"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
