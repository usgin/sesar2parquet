from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class GroupTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='User')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1', orcid='0000-0000-0000-0000')

        self.new_owner = User.objects.create(username='NewOwner')
        self.new_owner_su = SesarUser.objects.create(auth_user=self.new_owner, fname='User', lname='2', orcid='0000-0000-0000-0001')

        # setup group structure
        self.group1 = Group.objects.create(name="test1", owner=self.user_su, contact_email='test@gmail.com')
        self.group2 = Group.objects.create(name="test2", owner=self.user_su, contact_email='test@gmail.com')
        GroupMember.objects.create(group=self.group1, sesar_user=self.user_su, auth_group=AuthGroup.objects.get(name='Group Admin'))
        GroupMember.objects.create(group=self.group2, sesar_user=self.user_su, auth_group=AuthGroup.objects.get(name='Group Admin'))


    def test_view_group(self):
        """Can view an group"""
        request = self.factory.get('/api/group/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_group(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['group']['name'], self.group1.name)


    def test_view_user_groups(self):
        """Can view a user's groups"""
        request = self.factory.get('/api/group/user-membership/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_user_groups(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(any(d.get('name') == 'test1' for d in response.data))
        self.assertTrue(any(d.get('name') == 'test2' for d in response.data))


    def test_create_group(self):
        """Can create a new group"""
        request = self.factory.post('/api/group/create/',{'name': 'NewOrg', 'description': 'Test description', 'contact_email': 'test@gmail.com'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_group(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Group.objects.filter(name='NewOrg').exists())


    def test_update_group(self):
        """Can update an group"""
        request = self.factory.post('/api/group/update/',{'group_name':self.group1.name, 'name': 'NewName', 'description': 'New Description'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = update_group(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(name='NewName').exists())


    def test_deactivate_group(self):
        """Can deactivate an group"""
        request = self.factory.post('/api/group/deactivate/',{'name':self.group1.name})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = deactivate_group(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(id=self.group1.pk,deactivate_date__isnull=False).exists())


    def test_transfer_group(self):
        """Can transfer an group"""
        request = self.factory.post('/api/group/transfer/',{'name':self.group1.name, 'owner':self.new_owner_su.orcid})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = transfer_group(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(id=self.group1.pk,owner=self.new_owner_su.pk).exists())
