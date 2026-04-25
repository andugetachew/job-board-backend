from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):

    def test_create_candidate(self):
        user = User.objects.create_user(
            username="candidate", email="c@c.com", password="pass", role="candidate"
        )
        self.assertTrue(user.is_candidate)
        self.assertFalse(user.is_employer)

    def test_create_employer(self):
        user = User.objects.create_user(
            username="employer",
            email="e@e.com",
            password="pass",
            role="employer",
            company="Tech Corp",
        )
        self.assertTrue(user.is_employer)
        self.assertEqual(user.company, "Tech Corp")

    def test_str_method(self):
        user = User.objects.create_user(
            username="john", email="j@j.com", password="pass"
        )
        self.assertEqual(str(user), "john - candidate")
