from django.test import TestCase, RequestFactory
from parameterized import parameterized
from sesar_api.models import User, SesarUser, Team, TeamMember
from django.contrib.auth.models import Group as AuthGroup
from sesar_api.permissions import CanCreateSampleOnDoiPrefix
from django.core.management import call_command

class DoiPrefixPermissionTestCase(TestCase):
    def setUp(self):
        # Run command to create authorization groups
        call_command("create_auth_groups")

        self.factory = RequestFactory()
        self.create_auth_groups()
        self.create_users()
        self.create_team_structure()

    def create_auth_groups(self):
        """Helper to create and retrieve permission groups."""
        self.AUTH_GROUPS = {
            "R": AuthGroup.objects.get(name="Read Only"),
            "RE": AuthGroup.objects.get(name="Read Edit"),
            "CR": AuthGroup.objects.get(name="Read Create"),
            "CRE": AuthGroup.objects.get(name="Read Create Edit"),
            "CRED": AuthGroup.objects.get(name="Read Create Edit Deactivate"),
            "OWNER": AuthGroup.objects.get(name="Team Owner"),
            "ADMIN": AuthGroup.objects.get(name="Team Admin"),
        }

    def create_users(self):
        """Helper to create users and assign them to teams."""
        # Create users
        self.staff_user = User.objects.create(username="Staff", is_staff=True)
        self.no_permission_user = User.objects.create(username="NoPermissionUser")
        self.team_admin_user = User.objects.create(username="TeamAdmin")
        self.team_member_has_perms_user = User.objects.create(username="TeamMemberHasPerms")
        self.team_member_no_perms_user = User.objects.create(username="TeamMemberNoPerms")

        # Wrap users in SesarUser model
        self.staff_su = SesarUser.objects.create(auth_user=self.staff_user)
        self.no_permission_su = SesarUser.objects.create(auth_user=self.no_permission_user)
        self.team_admin_su = SesarUser.objects.create(auth_user=self.team_admin_user)
        self.team_member_has_perms_su = SesarUser.objects.create(auth_user=self.team_member_has_perms_user)
        self.team_member_no_perms_su = SesarUser.objects.create(auth_user=self.team_member_no_perms_user)

    def create_team_structure(self):
        # create team and subteam
        self.team = Team.objects.create(name="Team", owner=self.team_admin_su, doi_prefix="10.1234/")
        self.team_team = Team.objects.create(name="Team", part_of_team=self.team)

        # assign team permissions
        TeamMember.objects.create(
            team=self.team, 
            sesar_user=self.team_admin_su, 
            auth_group=self.AUTH_GROUPS['ADMIN']
        )
        TeamMember.objects.create(
            team=self.team, 
            sesar_user=self.team_member_has_perms_su, 
            auth_group=self.AUTH_GROUPS['CRED']
        )
        TeamMember.objects.create(
            team=self.team, 
            sesar_user=self.team_member_no_perms_su
        )

    @parameterized.expand([
        ("staff", "staff_user", "10.1234/", True),
        ("no_permission_user", "no_permission_user", "10.1234/", False),
        ("team_admin_user", "team_admin_user", "10.1234/", True),
        ("team_member_has_perms_user", "team_member_has_perms_user", "10.1234/", True),
        ("team_member_no_perms_user", "team_member_no_perms_user", "10.1234/", False),
    ])
    def test_can_create_sample_on_doi_prefix(self, name, user_attr, doi_prefix, expected):
        """Test CanCreateSampleOnDoiPrefix permission for different users."""
        request = self.factory.get('/')
        request.user = getattr(self, user_attr)
        self.assertEqual(CanCreateSampleOnDoiPrefix().has_object_permission(request, None, doi_prefix), expected)