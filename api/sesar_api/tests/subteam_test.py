from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class SubTeamTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.admin = User.objects.create(username='Owner')
        self.admin_su = SesarUser.objects.create(auth_user=self.admin, fname='User', lname='1')

        self.member1 = User.objects.create(username='Member1')
        self.member1_su = SesarUser.objects.create(auth_user=self.member1, fname='User', lname='2')

        self.member2 = User.objects.create(username='Member2')
        self.member2_su = SesarUser.objects.create(auth_user=self.member2, fname='User', lname='2')

        # setup team structure
        self.team = Team.objects.create(name="test1", owner=self.admin_su)
        self.team_admin = TeamMember.objects.create(team=self.team, sesar_user=self.admin_su, auth_group=AuthGroup.objects.get(name='Team Admin'))
        self.team_member1 = TeamMember.objects.create(team=self.team, sesar_user=self.member1_su)
        self.team_member2 = TeamMember.objects.create(team=self.team, sesar_user=self.member2_su)

        self.subteam = Team.objects.create(part_of_team=self.team,name='subteam1',description='subteam1 description')
        self.subteam.members.add(self.member1_su)


    def test_view_subteams(self):
        """Can view subteams"""
        request = self.factory.get('/api/team/test1/subteams/')
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = view_subteams(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    
    def test_view_subteam(self):
        """Can view an subteam"""
        request = self.factory.get('/api/team/test1/subteams/subteam1')
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = view_subteam(request, team='test1', subteam='subteam1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['subteam']['name'], 'subteam1')


    def test_create_subteam(self):
        """Can create a new subteam"""
        request = self.factory.post('/api/team/subteams/create/',{'part_of_team': self.team.pk, 'name': 'subteam2', 'description': 'subteam2 description'})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = create_subteam(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.team.subteams.filter(name='subteam2').exists())


    def test_update_subteam(self):
        """Can update an subteam"""
        request = self.factory.post('/api/team/subteams/update/',{'id':self.subteam.pk, 'name': 'newname'})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = update_subteam(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Team.objects.filter(id=self.subteam.pk, name='newname').exists())


    def test_delete_subteam(self):
        """Can delete an subteam"""
        request = self.factory.post('/api/team/subteams/delete/',{'id':self.subteam.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        self.assertTrue(TeamMember.objects.filter(team=self.subteam.pk).exists())
        response = delete_subteam(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Team.objects.filter(id=self.subteam.pk).exists())
        self.assertFalse(TeamMember.objects.filter(team=self.subteam.pk).exists())

    def test_add_subteam_member(self):
        """Can add member to an subteam"""
        request = self.factory.post('/api/team/subteams/add-member/',{'subteam':self.subteam.pk,'member':self.member2_su.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = add_subteam_member(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(TeamMember.objects.filter(team=self.subteam.pk,sesar_user=self.member2_su.pk).exists())


    def test_remove_subteam_member(self):
        """Can remove member from a subteam"""
        request = self.factory.post('/api/team/subteams/remove-member/',{'subteam':self.subteam.pk,'member':self.member1_su.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = remove_subteam_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TeamMember.objects.filter(team=self.subteam.pk,sesar_user=self.member1_su.pk).exists())