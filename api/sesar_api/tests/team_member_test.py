from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class TeamMemberTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='Owner')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1')

        self.member1 = User.objects.create(username='Member1')
        self.member1_su = SesarUser.objects.create(auth_user=self.member1, fname='User', lname='2')

        self.member2 = User.objects.create(username='Member2')
        self.member2_su = SesarUser.objects.create(auth_user=self.member2, fname='User', lname='2')

        self.new_member = User.objects.create(username='NewMember')
        self.new_member_su = SesarUser.objects.create(auth_user=self.new_member, fname='User', lname='3')

        # setup team structure
        self.team = Team.objects.create(name="test1", owner=self.user_su)
        self.org_owner = TeamMember.objects.create(team=self.team, sesar_user=self.user_su, auth_group=AuthGroup.objects.get(name='Team Owner'))
        self.org_member1 = TeamMember.objects.create(team=self.team, sesar_user=self.member1_su)
        self.org_member2 = TeamMember.objects.create(team=self.team, sesar_user=self.member2_su)


    def test_view_team_members(self):
        """Can view an teams members"""
        request = self.factory.get('/api/team/test1/members/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_team_members(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)


    def test_create_team_member(self):
        """Can create a new team member"""
        request = self.factory.post('/api/team/members/create/',{'team': self.team.pk, 'sesar_user': self.new_member_su.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_team_member(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.team.members.filter(sesar_user_id=self.new_member_su.pk).exists())


    def test_update_team_member(self):
        """Can update an team member"""
        request = self.factory.post('/api/team/members/update/',{'id':self.org_member1.pk, 'auth_group':'Team Admin'})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = update_team_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TeamMember.objects.filter(id=self.org_member1.pk, auth_group=AuthGroup.objects.get(name='Team Admin')).exists())


    def test_delete_team_member(self):
        """Can delete an team member"""
        request = self.factory.post('/api/team/members/delete/',{'id':self.org_member2.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = delete_team_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TeamMember.objects.filter(id=self.org_member2.pk).exists())