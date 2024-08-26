from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *


class GroupTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='User')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1')

        self.new_owner = User.objects.create(username='NewOwner')
        self.new_owner_su = SesarUser.objects.create(auth_user=self.new_owner, fname='User', lname='2')

        # setup group structure
        self.group1 = Group.objects.create(name="test1", owner=self.user_su)
        self.group2 = Group.objects.create(name="test2", owner=self.user_su)
        GroupMember.objects.create(group=self.group1, sesar_user=self.user_su, is_admin=True)
        GroupMember.objects.create(group=self.group2, sesar_user=self.user_su, is_admin=True)


    def test_view_group(self):
        """Can view an group"""
        request = self.factory.get('/api/group/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_group(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], self.group1.name)


    def test_view_user_groups(self):
        """Can view a user's groups"""
        request = self.factory.get('/api/group/user-membership/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_user_groups(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertTrue({'owner': 'User 1', 'name': 'test1', 'description': None, 'doi_prefix': '10.58052/'} in response.data)
        self.assertTrue({'owner': 'User 1', 'name': 'test2', 'description': None, 'doi_prefix': '10.58052/'} in response.data)


    def test_create_group(self):
        """Can create a new group"""
        request = self.factory.post('/api/group/create/',{'name': 'NewOrg', 'description': 'Test description'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_group(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Group.objects.filter(name='NewOrg').exists())


    def test_update_group(self):
        """Can update an group"""
        request = self.factory.post('/api/group/update/',{'id':self.group1.pk, 'name': 'NewName', 'description': 'New Description'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = update_group(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(name='NewName').exists())


    def test_deactivate_group(self):
        """Can deactivate an group"""
        request = self.factory.post('/api/group/deactivate/',{'id':self.group1.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = deactivate_group(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(id=self.group1.pk,deactivate_date__isnull=False).exists())


    def test_transfer_group(self):
        """Can transfer an group"""
        request = self.factory.post('/api/group/transfer/',{'id':self.group1.pk, 'owner':self.new_owner_su.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = transfer_group(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(id=self.group1.pk,owner=self.new_owner_su.pk).exists())
