from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class SesarCodeTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='user')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1', orcid='0000-0000-0001')

        self.team = Team.objects.create(name="team", owner=self.user_su, contact_email='test@gmail.com')
        TeamMember.objects.create(team=self.team, sesar_user=self.user_su, auth_group=AuthGroup.objects.get(name='Team Owner'))
        self.sesar_code = SesarCode.objects.create(team=self.team, sesar_code='IE001')
        self.sesar_code2 = SesarCode.objects.create(sesar_user=self.user_su, sesar_code='IE002')


    def test_view_sesar_code(self):
        """Can view Sesar code"""
        request = self.factory.get('/api/sesarcode/<sesar_code>/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_sesar_code(request, sesar_code='IE001')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['sesar_code'], self.sesar_code.sesar_code)


    def test_view_user_sesar_codes(self):
        """Can view a user's Sesar codes"""
        request = self.factory.get('/api/sesarcode/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_user_sesar_codes(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertTrue({'sesar_user': '0000-0000-0001', 'team': None, 'sesar_code': 'IE002', 'doi_prefix': '10.58052/', 'sample_count': 0} in response.data)


    def test_view_team_sesar_codes(self):
        """Can view a user's Sesar codes"""
        request = self.factory.get('/api/team/<team_name>/sesarcodes/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_team_sesar_codes(request, name='team')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertTrue({'sesar_user': None, 'team': 'team', 'sesar_code': 'IE001', 'doi_prefix': '10.58052/', 'sample_count': 0} in response.data)


    def test_create_sesar_code(self):
        """Can create Sesar code"""
        data = {
            'sesar_code': 'IE003',
            'sesar_user': '0000-0000-0001'
        }
        request = self.factory.post('/api/sesarcode/create/', data)
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_sesar_code(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SesarCode.objects.filter(sesar_code='IE003').exists())

        data = {
            'sesar_code': 'IE004',
            'team': 'team'
        }
        request = self.factory.post('/api/sesarcode/create/', data)
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_sesar_code(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(SesarCode.objects.filter(sesar_code='IE004').exists())


    def test_delete_sesar_code(self):
        """Can delete Sesar code"""
        data = {
            'sesar_code': 'IE001',
        }
        request = self.factory.post('/api/sesarcode/create/', data)
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = delete_sesar_code(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SesarCode.objects.filter(sesar_code='IE001').exists())