from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *


class JWTTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='User')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1', upload_permission_status=1)


    def test_get_jwt(self):
        """Can get a jwt token pair"""
        request = self.factory.get('/api/auth/token/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = get_jwt_for_user(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['access'])


    def test_revoke_all_jwts(self):
        """Can revoke all jwts"""
        request = self.factory.get('/api/auth/token/blacklist-all/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = revoke_all_jwt_for_user(request)
        self.assertEqual(response.status_code, 200)
