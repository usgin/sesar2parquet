from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class SesarUserTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.user1 = User.objects.create(username='user1')
        self.user1_su = SesarUser.objects.create(auth_user=self.user1, fname='User', lname='1', orcid='0000-0000-0001')

        self.user2 = User.objects.create(username='user2')
        self.user2_su = SesarUser.objects.create(auth_user=self.user2, fname='User', lname='2', orcid='0000-0000-0002')

        self.user3 = User.objects.create(username='user3')
        self.user3_su = SesarUser.objects.create(auth_user=self.user3, fname='User', lname='3', orcid='0000-0000-0003')


    def test_user_search(self):
        """Can search for user"""
        request = self.factory.get('/api/user/search/?query=user')
        request.user = self.user1
        force_authenticate(request, user=self.user1)
        response = search_users(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

        request = self.factory.get('/api/user/search/?query=2')
        request.user = self.user1
        force_authenticate(request, user=self.user1)
        response = search_users(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        request = self.factory.get('/api/user/search/?query=user%202')
        request.user = self.user1
        force_authenticate(request, user=self.user1)
        response = search_users(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        request = self.factory.get('/api/user/search/?query=0000-0000-0001')
        request.user = self.user1
        force_authenticate(request, user=self.user1)
        response = search_users(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)