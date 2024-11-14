from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class GroupTeamTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.admin = User.objects.create(username='Owner')
        self.admin_su = SesarUser.objects.create(auth_user=self.admin, fname='User', lname='1')

        self.member1 = User.objects.create(username='Member1')
        self.member1_su = SesarUser.objects.create(auth_user=self.member1, fname='User', lname='2')

        self.member2 = User.objects.create(username='Member2')
        self.member2_su = SesarUser.objects.create(auth_user=self.member2, fname='User', lname='2')

        # setup group structure
        self.group = Group.objects.create(name="test1", owner=self.admin_su)
        self.group_admin = GroupMember.objects.create(group=self.group, sesar_user=self.admin_su, auth_group=AuthGroup.objects.get(name='Group Admin'))
        self.group_member1 = GroupMember.objects.create(group=self.group, sesar_user=self.member1_su)
        self.group_member2 = GroupMember.objects.create(group=self.group, sesar_user=self.member2_su)

        self.team = Group.objects.create(part_of_group=self.group,name='team1',description='team1 description')
        self.team.members.add(self.member1_su)


    def test_view_group_teams(self):
        """Can view an groups teams"""
        request = self.factory.get('/api/group/test1/teams/')
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = view_group_teams(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    
    def test_view_group_team(self):
        """Can view an groups team"""
        request = self.factory.get('/api/group/test1/teams/team1')
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = view_group_team(request, group='test1', team='team1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['team']['name'], 'team1')


    def test_create_group_team(self):
        """Can create a new group team"""
        request = self.factory.post('/api/group/teams/create/',{'part_of_group': self.group.pk, 'name': 'team2', 'description': 'team2 description'})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = create_group_team(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.group.teams.filter(name='team2').exists())


    def test_update_group_team(self):
        """Can update an group team"""
        request = self.factory.post('/api/group/teams/update/',{'id':self.team.pk, 'name': 'newname'})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = update_group_team(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(id=self.team.pk, name='newname').exists())


    def test_delete_group_team(self):
        """Can delete an group team"""
        request = self.factory.post('/api/group/teams/delete/',{'id':self.team.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        self.assertTrue(GroupMember.objects.filter(group=self.team.pk).exists())
        response = delete_group_team(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Group.objects.filter(id=self.team.pk).exists())
        self.assertFalse(GroupMember.objects.filter(group=self.team.pk).exists())

    def test_add_group_team_member(self):
        """Can add member to an group team"""
        request = self.factory.post('/api/group/teams/add-member/',{'team':self.team.pk,'member':self.member2_su.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = add_group_team_member(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(GroupMember.objects.filter(group=self.team.pk,sesar_user=self.member2_su.pk).exists())


    def test_remove_group_team_member(self):
        """Can remove member to an group team"""
        request = self.factory.post('/api/group/teams/remove-member/',{'team':self.team.pk,'member':self.member1_su.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = remove_group_team_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GroupMember.objects.filter(group=self.team.pk,sesar_user=self.member1_su.pk).exists())