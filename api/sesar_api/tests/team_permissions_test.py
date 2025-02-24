from django.test import TestCase, RequestFactory
from sesar_api.models import *
from django.contrib.auth.models import Group as AuthGroup
from sesar_api.permissions import *
from django.core.management import call_command
from sesar_api.util import get_team_user_codes_with_permission


class TeamPermissionTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = RequestFactory()

        self.team_owner = User.objects.create(username='Owner')
        self.team_owner_su = SesarUser.objects.create(auth_user=self.team_owner)

        self.team_admin = User.objects.create(username='Admin')
        self.team_admin_su = SesarUser.objects.create(auth_user=self.team_admin)

        self.team_member = User.objects.create(username='Member')
        self.team_member_su = SesarUser.objects.create(auth_user=self.team_member)

        self.team_member2 = User.objects.create(username='Member2')
        self.team_member2_su = SesarUser.objects.create(auth_user=self.team_member2)

        self.team = Team.objects.create(name="Team", owner=self.team_owner_su)
        self.owner = TeamMember.objects.create(team=self.team, sesar_user=self.team_owner_su, auth_group=AuthGroup.objects.get(name='Team Owner'))
        self.admin = TeamMember.objects.create(team=self.team, sesar_user=self.team_admin_su, auth_group=AuthGroup.objects.get(name='Team Admin'))
        self.member = TeamMember.objects.create(team=self.team, sesar_user=self.team_member_su, auth_group=AuthGroup.objects.get(name="Read Only"))
        self.member2 = TeamMember.objects.create(team=self.team, sesar_user=self.team_member2_su)

        self.user_code1 = SesarUserCode.objects.create(user_code="IE001", team=self.team)
        self.user_code2 = SesarUserCode.objects.create(user_code="IE002", team=self.team)

        self.subteam = Team.objects.create(name="subteam", part_of_team=self.team)
        TeamMember.objects.create(team=self.subteam, sesar_user=self.team_member2_su)
        Permission.objects.create(user_code=self.user_code1, team=self.subteam, auth_group=AuthGroup.objects.get(name="Read Create"))


    def test_is_team_owner(self):
        """Team owner is correctly identified"""
        # Test team owner
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(IsTeamOwner().has_object_permission(request, None, self.team))

        # Test not team owner
        request.user = self.team_member
        self.assertFalse(IsTeamOwner().has_object_permission(request, None, self.team))

    def test_can_add_team_member(self):
        """Add team member permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanAddTeamMember().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member
        self.assertFalse(CanAddTeamMember().has_object_permission(request, None, self.team))

    def test_can_change_team_member(self):
        """Change team member permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanChangeTeamMember().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member
        self.assertFalse(CanChangeTeamMember().has_object_permission(request, None, self.team))

    def test_can_delete_team_member(self):
        """Delete team member permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanDeleteTeamMember().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member
        self.assertFalse(CanDeleteTeamMember().has_object_permission(request, None, self.team))

    def test_can_add_team(self):
        """Add team permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanAddTeam().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member
        self.assertFalse(CanAddTeam().has_object_permission(request, None, self.team))

    def test_can_change_team(self):
        """Change team permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanChangeTeam().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member
        self.assertFalse(CanChangeTeam().has_object_permission(request, None, self.team))

    def test_can_delete_team(self):
        """Delete team permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanDeleteTeam().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member
        self.assertFalse(CanDeleteTeam().has_object_permission(request, None, self.team))


    def test_can_view_team_samples(self):
        """View team sample permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanViewTeamSamples().has_object_permission(request, None, self.team))
        self.assertTrue(CanViewTeamSamples().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member2
        self.assertFalse(CanViewTeamSamples().has_object_permission(request, None, self.team))

    
    def test_can_add_user_code(self):
        """Add user code permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanAddTeamUserCode().has_object_permission(request, None, self.team))
        self.assertTrue(CanAddTeamUserCode().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member2
        self.assertFalse(CanAddTeamUserCode().has_object_permission(request, None, self.team))


    def test_can_delete_user_code(self):
        """Delete user code permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanDeleteTeamUserCode().has_object_permission(request, None, self.team))
        self.assertTrue(CanDeleteTeamUserCode().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member2
        self.assertFalse(CanDeleteTeamUserCode().has_object_permission(request, None, self.team))


    def test_can_transfer_sample(self):
        """Transfer sample permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertTrue(CanTransferTeamSample().has_object_permission(request, None, self.team))
        self.assertTrue(CanTransferTeamSample().has_object_permission(request, None, self.team))

        # Test does not have permission
        request.user = self.team_member2
        self.assertFalse(CanTransferTeamSample().has_object_permission(request, None, self.team))

    
    def test_get_team_user_codes_with_permission(self):
        """Team user codes with permission are correctly identified"""

        # Test owner/admin permission
        request = self.factory.get('/')
        request.user = self.team_owner
        self.assertEqual(get_team_user_codes_with_permission(self.team_owner_su, self.team, 'add_sample'), 'all')
        self.assertEqual(get_team_user_codes_with_permission(self.team_owner_su, self.team, 'view_sample'), 'all')
        self.assertEqual(get_team_user_codes_with_permission(self.team_owner_su, self.team, 'change_sample'), 'all')

        # Test team level permission
        request = self.factory.get('/')
        request.user = self.team_member
        self.assertEqual(get_team_user_codes_with_permission(self.team_member_su, self.team, 'add_sample'), [])
        self.assertEqual(get_team_user_codes_with_permission(self.team_member_su, self.team, 'view_sample'), 'all')

        # Test subteam level permission
        request = self.factory.get('/')
        request.user = self.team_member2
        self.assertEqual(get_team_user_codes_with_permission(self.team_member2_su, self.team, 'add_sample'), ['IE001'])
        self.assertEqual(get_team_user_codes_with_permission(self.team_member2_su, self.team, 'view_sample'), ['IE001'])
        self.assertEqual(get_team_user_codes_with_permission(self.team_member2_su, self.team, 'change_sample'), [])