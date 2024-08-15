from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *


class OrganizationMemberTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.admin = User.objects.create(username='Owner')
        self.admin_su = SesarUser.objects.create(auth_user=self.admin, fname='User', lname='1')

        self.member1 = User.objects.create(username='Member1')
        self.member1_su = SesarUser.objects.create(auth_user=self.member1, fname='User', lname='2')

        self.member2 = User.objects.create(username='Member2')
        self.member2_su = SesarUser.objects.create(auth_user=self.member2, fname='User', lname='2')

        # setup organization structure
        self.organization = Organization.objects.create(name="test1", owner=self.admin_su)
        self.org_admin = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.admin_su, is_admin=True)
        self.org_member1 = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.member1_su, is_admin=False)
        self.org_member2 = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.member2_su, is_admin=False)

        self.team = OrganizationTeam.objects.create(organization=self.organization,name='team1',description='team1 description')
        self.team.members.add(self.org_member1)


    def test_view_organization_teams(self):
        """Can view an organizations teams"""
        request = self.factory.get('/api/organization/test1/teams/')
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = view_organization_teams(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    
    def test_view_organization_team(self):
        """Can view an organizations team"""
        request = self.factory.get('/api/organization/test1/teams/team1')
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = view_organization_team(request, organization='test1', team='team1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'team1')


    def test_create_organization_team(self):
        """Can create a new organization team"""
        request = self.factory.post('/api/organization/teams/create/',{'organization': self.organization.pk, 'name': 'team2', 'description': 'team2 description'})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = create_organization_team(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.organization.teams.filter(name='team2').exists())


    def test_update_organization_team(self):
        """Can update an organization team"""
        request = self.factory.post('/api/organization/teams/update/',{'id':self.team.pk, 'name': 'newname'})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = update_organization_team(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OrganizationTeam.objects.filter(id=self.team.pk, name='newname').exists())


    def test_delete_organization_team(self):
        """Can delete an organization team"""
        request = self.factory.post('/api/organization/teams/delete/',{'id':self.team.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        self.assertTrue(OrganizationTeamMember.objects.filter(team=self.team.pk).exists())
        response = delete_organization_team(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(OrganizationTeam.objects.filter(id=self.team.pk).exists())
        self.assertFalse(OrganizationTeamMember.objects.filter(team=self.team.pk).exists())

    def test_add_organization_team_member(self):
        """Can add member to an organization team"""
        request = self.factory.post('/api/organization/teams/add-member/',{'team':self.team.pk,'member':self.org_member2.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = add_organization_team_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OrganizationTeamMember.objects.filter(team=self.team.pk,member=self.org_member2.pk).exists())


    def test_remove_organization_team_member(self):
        """Can remove member to an organization team"""
        request = self.factory.post('/api/organization/teams/remove-member/',{'team':self.team.pk,'member':self.org_member1.pk})
        request.user = self.admin
        force_authenticate(request, user=self.admin)
        response = remove_organization_team_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(OrganizationTeamMember.objects.filter(team=self.team.pk,member=self.org_member1.pk).exists())