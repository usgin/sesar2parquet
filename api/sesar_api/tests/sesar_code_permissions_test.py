from django.test import TestCase, RequestFactory
from parameterized import parameterized
from sesar_api.models import User, SesarUser, SampleType, Sample, SesarCode, Team, TeamMember, Permission
from django.contrib.auth.models import Group as AuthGroup
from sesar_api.permissions import IsSesarCodeOwner, CanCreateSampleOnSesarCode, CanEditSampleOnSesarCode, CanDeactivateSampleOnSesarCode
from django.core.management import call_command

class SesarCodePermissionTestCase(TestCase):
    def setUp(self):
        # Run command to create authorization groups
        call_command("create_auth_groups")

        self.factory = RequestFactory()
        self.create_auth_groups()
        self.create_users()
        self.create_team_structure()
        self.create_samples()
        self.create_permissions()

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
        self.sample_owner_user = User.objects.create(username="SampleOwner")
        self.sesar_code_owner_user = User.objects.create(username="SesarCodeOwner")
        self.no_permission_user = User.objects.create(username="NoPermissionUser")
        self.team_admin_user = User.objects.create(username="TeamAdmin")
        self.team_member_has_perms_user = User.objects.create(username="TeamMemberHasPerms")
        self.subteam_member_has_perms_user = User.objects.create(username="SubteamMemberHasPerms")
        self.team_member_no_perms_user = User.objects.create(username="TeamMemberNoPerms")
        self.r_user = User.objects.create(username="r_user")
        self.re_user = User.objects.create(username="re_user")
        self.cr_user = User.objects.create(username="cr_user")
        self.cre_user = User.objects.create(username="cre_user")
        self.cred_user = User.objects.create(username="cred_user")

        # Wrap users in SesarUser model
        self.staff_su = SesarUser.objects.create(auth_user=self.staff_user)
        self.sample_owner_su = SesarUser.objects.create(auth_user=self.sample_owner_user)
        self.sesar_code_owner_su = SesarUser.objects.create(auth_user=self.sesar_code_owner_user)
        self.no_permission_su = SesarUser.objects.create(auth_user=self.no_permission_user)
        self.team_admin_su = SesarUser.objects.create(auth_user=self.team_admin_user)
        self.team_member_has_perms_su = SesarUser.objects.create(auth_user=self.team_member_has_perms_user)
        self.subteam_member_has_perms_su = SesarUser.objects.create(auth_user=self.subteam_member_has_perms_user)
        self.team_member_no_perms_su = SesarUser.objects.create(auth_user=self.team_member_no_perms_user)
        self.r_su = SesarUser.objects.create(auth_user=self.r_user)
        self.re_su = SesarUser.objects.create(auth_user=self.re_user)
        self.cr_su = SesarUser.objects.create(auth_user=self.cr_user)
        self.cre_su = SesarUser.objects.create(auth_user=self.cre_user)
        self.cred_su = SesarUser.objects.create(auth_user=self.cred_user)

    def create_team_structure(self):
        # create team and subteam
        self.team = Team.objects.create(name="Team", owner=self.team_admin_su)
        self.subteam = Team.objects.create(name="Subteam", part_of_team=self.team)

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
            team=self.subteam,
            sesar_user=self.subteam_member_has_perms_su, 
            auth_group=self.AUTH_GROUPS['CRED']
        )
        TeamMember.objects.create(
            team=self.team, 
            sesar_user=self.team_member_no_perms_su
        )

    def create_samples(self):
        """Helper to create sample-related objects."""
        self.sample_type = SampleType.objects.create(name="Sample Type")

        self.sesar_code = SesarCode.objects.create(
            sesar_code="IE001", 
            sesar_user=self.sesar_code_owner_su
        )
        self.team_sesar_code = SesarCode.objects.create(
            sesar_code="IE002", 
            team=self.team
        )
        self.user_sample = Sample.objects.create(
            name="Sample", 
            igsn="10.58052/IE001TEST", 
            igsn_prefix=self.sesar_code, 
            cur_owner=self.sample_owner_su, 
            sample_type=self.sample_type, 
            cur_registrant=self.sample_owner_su
        )
        self.team_sample = Sample.objects.create(
            name="Sample", 
            igsn="10.58052/IE002TEST", 
            igsn_prefix=self.team_sesar_code,
            sample_type=self.sample_type, 
            cur_registrant=self.sample_owner_su, 
            team_owner=self.team
        )

    def create_permissions(self):
        # assign subteam permission
        Permission.objects.create(
            sesar_code=self.team_sesar_code, 
            auth_group=self.AUTH_GROUPS['CRED'], 
            team=self.subteam
        )

        sesar_code_permissions_to_assign = [
            {
                'sesar_user': self.r_su,
                'auth_group': self.AUTH_GROUPS['R']
            },
            {
                'sesar_user': self.re_su,
                'auth_group': self.AUTH_GROUPS['RE']
            },
            {
                'sesar_user': self.cr_su,
                'auth_group': self.AUTH_GROUPS['CR']
            },
            {
                'sesar_user': self.cre_su,
                'auth_group': self.AUTH_GROUPS['CRE']
            },
            {
                'sesar_user': self.cred_su,
                'auth_group': self.AUTH_GROUPS['CRED']
            },
        ]

        # assign permissions to test users
        for permission in sesar_code_permissions_to_assign:
            Permission.objects.create(
                sesar_code=self.sesar_code,
                sesar_user=permission['sesar_user'],
                auth_group=permission['auth_group']
            )

    def test_is_sesar_code_owner(self):
        """Sesar code owner is correctly identified"""
        # Test Sesar code owner
        request = self.factory.get('/')
        request.user = self.sesar_code_owner_user
        self.assertTrue(IsSesarCodeOwner().has_object_permission(request, None, self.sesar_code))

        # Test not Sesar code owner
        request.user = self.no_permission_user
        self.assertFalse(IsSesarCodeOwner().has_object_permission(request, None, self.sesar_code))

        # Test owned by team
        self.assertTrue(IsSesarCodeOwner(self.team).has_object_permission(request, None, self.team_sesar_code))
        
        # Test not owned by team
        self.assertFalse(IsSesarCodeOwner(self.subteam).has_object_permission(request, None, self.team_sesar_code))

    @parameterized.expand([
        ("staff", "staff_user", "sesar_code", True),
        ("sesar_code_owner", "sesar_code_owner_user", "sesar_code", True),
        ("no_permission_user", "no_permission_user", "sesar_code", False),
        ("r_user", "r_user", "sesar_code", False),
        ("re_user", "re_user", "sesar_code", False),
        ("cr_user", "cr_user", "sesar_code", True),
        ("cre_user", "cre_user", "sesar_code", True),
        ("cred_user", "cred_user", "sesar_code", True),
        ("team_admin_user", "team_admin_user", "team_sesar_code", True),
        ("team_member_has_perms_user", "team_member_has_perms_user", "team_sesar_code", True),
        ("subteam_member_has_perms_user", "subteam_member_has_perms_user", "team_sesar_code", True),
        ("team_member_no_perms_user", "team_member_no_perms_user", "team_sesar_code", False),
    ])
    def test_can_create_sample_on_sesar_code(self, name, user_attr, sample, expected):
        """Test CanCreateSampleOnSesarCode permission for different users."""
        request = self.factory.get('/')
        request.user = getattr(self, user_attr)
        obj = getattr(self, sample)
        self.assertEqual(CanCreateSampleOnSesarCode().has_object_permission(request, None, obj), expected)


    @parameterized.expand([
        ("staff", "staff_user", "sesar_code", True),
        ("sesar_code_owner", "sesar_code_owner_user", "sesar_code", True),
        ("no_permission_user", "no_permission_user", "sesar_code", False),
        ("r_user", "r_user", "sesar_code", False),
        ("re_user", "re_user", "sesar_code", True),
        ("cr_user", "cr_user", "sesar_code", False),
        ("cre_user", "cre_user", "sesar_code", True),
        ("cred_user", "cred_user", "sesar_code", True),
        ("team_admin_user", "team_admin_user", "team_sesar_code", True),
        ("team_member_has_perms_user", "team_member_has_perms_user", "team_sesar_code", True),
        ("subteam_member_has_perms_user", "subteam_member_has_perms_user", "team_sesar_code", True),
        ("team_member_no_perms_user", "team_member_no_perms_user", "team_sesar_code", False),
    ])
    def test_can_edit_sample_on_sesar_code(self, name, user_attr, sample, expected):
        """Test CanEditSampleOnSesarCode permission for different users."""
        request = self.factory.get('/')
        request.user = getattr(self, user_attr)
        obj = getattr(self, sample)
        self.assertEqual(CanEditSampleOnSesarCode().has_object_permission(request, None, obj), expected)


    @parameterized.expand([
        ("staff", "staff_user", "sesar_code", True),
        ("sesar_code_owner", "sesar_code_owner_user", "sesar_code", True),
        ("no_permission_user", "no_permission_user", "sesar_code", False),
        ("r_user", "r_user", "sesar_code", False),
        ("re_user", "re_user", "sesar_code", False),
        ("cr_user", "cr_user", "sesar_code", False),
        ("cre_user", "cre_user", "sesar_code", False),
        ("cred_user", "cred_user", "sesar_code", True),
        ("team_admin_user", "team_admin_user", "team_sesar_code", True),
        ("team_member_has_perms_user", "team_member_has_perms_user", "team_sesar_code", True),
        ("subteam_member_has_perms_user", "subteam_member_has_perms_user", "team_sesar_code", True),
        ("team_member_no_perms_user", "team_member_no_perms_user", "team_sesar_code", False),
    ])
    def test_can_deactivate_sample_on_sesar_code(self, name, user_attr, sample, expected):
        """Test CanDeactivateSampleOnSesarCode permission for different users."""
        request = self.factory.get('/')
        request.user = getattr(self, user_attr)
        obj = getattr(self, sample)
        self.assertEqual(CanDeactivateSampleOnSesarCode().has_object_permission(request, None, obj), expected)