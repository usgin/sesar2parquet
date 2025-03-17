from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class TeamTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='User')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1', orcid='0000-0000-0000-0000')

        self.new_owner = User.objects.create(username='NewOwner')
        self.new_owner_su = SesarUser.objects.create(auth_user=self.new_owner, fname='User', lname='2', orcid='0000-0000-0000-0001')

        # setup team structure
        self.team1 = Team.objects.create(name="test1", owner=self.user_su, contact_email='test@gmail.com')
        self.team2 = Team.objects.create(name="test2", owner=self.user_su, contact_email='test@gmail.com')
        TeamMember.objects.create(team=self.team1, sesar_user=self.user_su, auth_group=AuthGroup.objects.get(name='Team Admin'))
        TeamMember.objects.create(team=self.team2, sesar_user=self.user_su, auth_group=AuthGroup.objects.get(name='Team Admin'))


    def test_view_team(self):
        """Can view an team"""
        request = self.factory.get('/api/team/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_team(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['team']['name'], self.team1.name)


    def test_view_user_teams(self):
        """Can view a user's teams"""
        request = self.factory.get('/api/team/user-membership/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_user_teams(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(any(d.get('name') == 'test1' for d in response.data))
        self.assertTrue(any(d.get('name') == 'test2' for d in response.data))


    def test_create_team(self):
        """Can create a new team"""
        request = self.factory.post('/api/team/create/',{'name': 'NewOrg', 'description': 'Test description', 'contact_email': 'test@gmail.com'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_team(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Team.objects.filter(name='neworg').exists())


    def test_update_team(self):
        """Can update an team"""
        request = self.factory.post('/api/team/update/',{'team_name':self.team1.name, 'name': 'NewName', 'description': 'New Description'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = update_team(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Team.objects.filter(name='NewName').exists())


    def test_deactivate_team(self):
        """Can deactivate an team"""
        request = self.factory.post('/api/team/deactivate/',{'name':self.team1.name})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = deactivate_team(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Team.objects.filter(id=self.team1.pk,deactivate_date__isnull=False).exists())


    def test_transfer_team(self):
        """Can transfer an team"""
        request = self.factory.post('/api/team/transfer/',{'name':self.team1.name, 'owner':self.new_owner_su.orcid})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = transfer_team(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Team.objects.filter(id=self.team1.pk,owner=self.new_owner_su.pk).exists())
