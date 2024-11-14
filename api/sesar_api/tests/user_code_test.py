from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class UserCodeTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='user')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1', orcid='0000-0000-0001')

        self.group = Group.objects.create(name="group", owner=self.user_su, contact_email='test@gmail.com')
        GroupMember.objects.create(group=self.group, sesar_user=self.user_su, auth_group=AuthGroup.objects.get(name='Group Owner'))
        self.user_code = SesarUserCode.objects.create(group=self.group, user_code='IE001')
        self.user_code2 = SesarUserCode.objects.create(sesar_user=self.user_su, user_code='IE002')


    def test_view_user_code(self):
        """Can view user code"""
        request = self.factory.get('/api/usercode/<user_code>/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_user_code(request, user_code='IE001')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_code'], self.user_code.user_code)


    def test_view_user_user_codes(self):
        """Can view a user's user codes"""
        request = self.factory.get('/api/usercode/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_user_user_codes(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertTrue({'sesar_user': '0000-0000-0001', 'group': None, 'user_code': 'IE002', 'doi_prefix': '10.58052/', 'sample_count': 0} in response.data)


    def test_view_group_user_codes(self):
        """Can view a user's user codes"""
        request = self.factory.get('/api/group/<group_name>/usercodes/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_group_user_codes(request, name='group')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertTrue({'sesar_user': None, 'group': 'group', 'user_code': 'IE001', 'doi_prefix': '10.58052/', 'sample_count': 0} in response.data)


    def test_create_user_code(self):
        """Can create user code"""
        data = {
            'user_code': 'IE003',
            'sesar_user': '0000-0000-0001'
        }
        request = self.factory.post('/api/usercode/create/', data)
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_user_code(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SesarUserCode.objects.filter(user_code='IE003').exists())

        data = {
            'user_code': 'IE004',
            'group': 'group'
        }
        request = self.factory.post('/api/usercode/create/', data)
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_user_code(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SesarUserCode.objects.filter(user_code='IE004').exists())


    def test_delete_user_code(self):
        """Can delete user code"""
        data = {
            'user_code': 'IE001',
        }
        request = self.factory.post('/api/usercode/create/', data)
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = delete_user_code(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SesarUserCode.objects.filter(user_code='IE001').exists())