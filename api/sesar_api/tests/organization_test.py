from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *


class OrganizationTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='User')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1')

        self.new_owner = User.objects.create(username='NewOwner')
        self.new_owner_su = SesarUser.objects.create(auth_user=self.new_owner, fname='User', lname='2')

        # setup organization structure
        self.organization1 = Organization.objects.create(name="test1", owner=self.user_su)
        self.organization2 = Organization.objects.create(name="test2", owner=self.user_su)
        OrganizationMember.objects.create(organization=self.organization1, sesar_user=self.user_su, is_admin=True)
        OrganizationMember.objects.create(organization=self.organization2, sesar_user=self.user_su, is_admin=True)


    def test_view_organization(self):
        """Can view an organization"""
        request = self.factory.get('/api/organization/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_organization(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], self.organization1.name)


    def test_view_user_organizations(self):
        """Can view a user's organizations"""
        request = self.factory.get('/api/organization/user-membership/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_user_organizations(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertTrue({'owner': 'User 1', 'name': 'test1', 'description': None, 'doi_prefix': '10.58052/'} in response.data)
        self.assertTrue({'owner': 'User 1', 'name': 'test2', 'description': None, 'doi_prefix': '10.58052/'} in response.data)


    def test_create_organization(self):
        """Can create a new organization"""
        request = self.factory.post('/api/organization/create/',{'name': 'NewOrg', 'description': 'Test description'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_organization(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Organization.objects.filter(name='NewOrg').exists())


    def test_update_organization(self):
        """Can update an organization"""
        request = self.factory.post('/api/organization/update/',{'id':self.organization1.pk, 'name': 'NewName', 'description': 'New Description'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = update_organization(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Organization.objects.filter(name='NewName').exists())


    def test_deactivate_organization(self):
        """Can deactivate an organization"""
        request = self.factory.post('/api/organization/deactivate/',{'id':self.organization1.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = deactivate_organization(request)
        print (response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Organization.objects.filter(id=self.organization1.pk,deactivate_date__isnull=False).exists())


    def test_transfer_organization(self):
        """Can transfer an organization"""
        request = self.factory.post('/api/organization/transfer/',{'id':self.organization1.pk, 'owner':self.new_owner_su.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = transfer_organization(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Organization.objects.filter(id=self.organization1.pk,owner=self.new_owner_su.pk).exists())
