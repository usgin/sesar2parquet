from django.test import TestCase, RequestFactory
from parameterized import parameterized
from sesar_api.models import User, SesarUser, SampleType, Sample, SesarUserCode, Group, GroupMember, Permission
from django.contrib.auth.models import Group as AuthGroup
from sesar_api.permissions import IsUserCodeOwner, CanCreateSampleOnUserCode, CanEditSampleOnUserCode, CanDeactivateSampleOnUserCode
from django.core.management import call_command

class UserCodePermissionTestCase(TestCase):
    def setUp(self):
        # Run command to create authorization groups
        call_command("create_auth_groups")

        self.factory = RequestFactory()
        self.create_auth_groups()
        self.create_users()
        self.create_user_group_structure()
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
            "OWNER": AuthGroup.objects.get(name="Group Owner"),
            "ADMIN": AuthGroup.objects.get(name="Group Admin"),
        }

    def create_users(self):
        """Helper to create users and assign them to groups."""
        # Create users
        self.staff_user = User.objects.create(username="Staff", is_staff=True)
        self.sample_owner_user = User.objects.create(username="SampleOwner")
        self.user_code_owner_user = User.objects.create(username="UserCodeOwner")
        self.no_permission_user = User.objects.create(username="NoPermissionUser")
        self.group_admin_user = User.objects.create(username="GroupAdmin")
        self.group_member_has_perms_user = User.objects.create(username="GroupMemberHasPerms")
        self.team_member_has_perms_user = User.objects.create(username="TeamMemberHasPerms")
        self.group_member_no_perms_user = User.objects.create(username="GroupMemberNoPerms")
        self.r_user = User.objects.create(username="r_user")
        self.re_user = User.objects.create(username="re_user")
        self.cr_user = User.objects.create(username="cr_user")
        self.cre_user = User.objects.create(username="cre_user")
        self.cred_user = User.objects.create(username="cred_user")

        # Wrap users in SesarUser model
        self.staff_su = SesarUser.objects.create(auth_user=self.staff_user)
        self.sample_owner_su = SesarUser.objects.create(auth_user=self.sample_owner_user)
        self.user_code_owner_su = SesarUser.objects.create(auth_user=self.user_code_owner_user)
        self.no_permission_su = SesarUser.objects.create(auth_user=self.no_permission_user)
        self.group_admin_su = SesarUser.objects.create(auth_user=self.group_admin_user)
        self.group_member_has_perms_su = SesarUser.objects.create(auth_user=self.group_member_has_perms_user)
        self.team_member_has_perms_su = SesarUser.objects.create(auth_user=self.team_member_has_perms_user)
        self.group_member_no_perms_su = SesarUser.objects.create(auth_user=self.group_member_no_perms_user)
        self.r_su = SesarUser.objects.create(auth_user=self.r_user)
        self.re_su = SesarUser.objects.create(auth_user=self.re_user)
        self.cr_su = SesarUser.objects.create(auth_user=self.cr_user)
        self.cre_su = SesarUser.objects.create(auth_user=self.cre_user)
        self.cred_su = SesarUser.objects.create(auth_user=self.cred_user)

    def create_user_group_structure(self):
        # create group and subgroup
        self.group = Group.objects.create(name="Group", owner=self.group_admin_su)
        self.group_team = Group.objects.create(name="Team", part_of_group=self.group)

        # assign group permissions
        GroupMember.objects.create(
            group=self.group, 
            sesar_user=self.group_admin_su, 
            auth_group=self.AUTH_GROUPS['ADMIN']
        )
        GroupMember.objects.create(
            group=self.group, 
            sesar_user=self.group_member_has_perms_su, 
            auth_group=self.AUTH_GROUPS['CRED']
        )
        GroupMember.objects.create(
            group=self.group_team,
            sesar_user=self.team_member_has_perms_su, 
            auth_group=self.AUTH_GROUPS['CRED']
        )
        GroupMember.objects.create(
            group=self.group, 
            sesar_user=self.group_member_no_perms_su
        )

    def create_samples(self):
        """Helper to create sample-related objects."""
        self.sample_type = SampleType.objects.create(name="Sample Type")

        self.user_code = SesarUserCode.objects.create(
            user_code="IE001", 
            sesar_user=self.user_code_owner_su
        )
        self.group_user_code = SesarUserCode.objects.create(
            user_code="IE002", 
            group=self.group
        )
        self.user_sample = Sample.objects.create(
            name="Sample", 
            igsn="10.58052/IE001TEST", 
            igsn_prefix=self.user_code, 
            cur_owner=self.sample_owner_su, 
            sample_type=self.sample_type, 
            cur_registrant=self.sample_owner_su
        )
        self.group_sample = Sample.objects.create(
            name="Sample", 
            igsn="10.58052/IE002TEST", 
            igsn_prefix=self.group_user_code,
            sample_type=self.sample_type, 
            cur_registrant=self.sample_owner_su, 
            group_owner=self.group
        )

    def create_permissions(self):
        # assign team permission
        Permission.objects.create(
            user_code=self.group_user_code, 
            auth_group=self.AUTH_GROUPS['CRED'], 
            group=self.group_team
        )

        user_code_permissions_to_assign = [
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
        for permission in user_code_permissions_to_assign:
            Permission.objects.create(
                user_code=self.user_code,
                sesar_user=permission['sesar_user'],
                auth_group=permission['auth_group']
            )

    def test_is_user_code_owner(self):
        """User code owner is correctly identified"""
        # Test user code owner
        request = self.factory.get('/')
        request.user = self.user_code_owner_user
        self.assertTrue(IsUserCodeOwner().has_object_permission(request, None, self.user_code))

        # Test not user code owner
        request.user = self.no_permission_user
        self.assertFalse(IsUserCodeOwner().has_object_permission(request, None, self.user_code))

        # Test owned by group
        self.assertTrue(IsUserCodeOwner(self.group).has_object_permission(request, None, self.group_user_code))
        
        # Test not owned by group
        self.assertFalse(IsUserCodeOwner(self.group_team).has_object_permission(request, None, self.group_user_code))

    @parameterized.expand([
        ("staff", "staff_user", "user_code", True),
        ("user_code_owner", "user_code_owner_user", "user_code", True),
        ("no_permission_user", "no_permission_user", "user_code", False),
        ("r_user", "r_user", "user_code", False),
        ("re_user", "re_user", "user_code", False),
        ("cr_user", "cr_user", "user_code", True),
        ("cre_user", "cre_user", "user_code", True),
        ("cred_user", "cred_user", "user_code", True),
        ("group_admin_user", "group_admin_user", "group_user_code", True),
        ("group_member_has_perms_user", "group_member_has_perms_user", "group_user_code", True),
        ("team_member_has_perms_user", "team_member_has_perms_user", "group_user_code", True),
        ("group_member_no_perms_user", "group_member_no_perms_user", "group_user_code", False),
    ])
    def test_can_create_sample_on_user_code(self, name, user_attr, sample, expected):
        """Test CanCreateSampleOnUserCode permission for different users."""
        request = self.factory.get('/')
        request.user = getattr(self, user_attr)
        obj = getattr(self, sample)
        self.assertEqual(CanCreateSampleOnUserCode().has_object_permission(request, None, obj), expected)


    @parameterized.expand([
        ("staff", "staff_user", "user_code", True),
        ("user_code_owner", "user_code_owner_user", "user_code", True),
        ("no_permission_user", "no_permission_user", "user_code", False),
        ("r_user", "r_user", "user_code", False),
        ("re_user", "re_user", "user_code", True),
        ("cr_user", "cr_user", "user_code", False),
        ("cre_user", "cre_user", "user_code", True),
        ("cred_user", "cred_user", "user_code", True),
        ("group_admin_user", "group_admin_user", "group_user_code", True),
        ("group_member_has_perms_user", "group_member_has_perms_user", "group_user_code", True),
        ("team_member_has_perms_user", "team_member_has_perms_user", "group_user_code", True),
        ("group_member_no_perms_user", "group_member_no_perms_user", "group_user_code", False),
    ])
    def test_can_edit_sample_on_user_code(self, name, user_attr, sample, expected):
        """Test CanEditSampleOnUserCode permission for different users."""
        request = self.factory.get('/')
        request.user = getattr(self, user_attr)
        obj = getattr(self, sample)
        self.assertEqual(CanEditSampleOnUserCode().has_object_permission(request, None, obj), expected)


    @parameterized.expand([
        ("staff", "staff_user", "user_code", True),
        ("user_code_owner", "user_code_owner_user", "user_code", True),
        ("no_permission_user", "no_permission_user", "user_code", False),
        ("r_user", "r_user", "user_code", False),
        ("re_user", "re_user", "user_code", False),
        ("cr_user", "cr_user", "user_code", False),
        ("cre_user", "cre_user", "user_code", False),
        ("cred_user", "cred_user", "user_code", True),
        ("group_admin_user", "group_admin_user", "group_user_code", True),
        ("group_member_has_perms_user", "group_member_has_perms_user", "group_user_code", True),
        ("team_member_has_perms_user", "team_member_has_perms_user", "group_user_code", True),
        ("group_member_no_perms_user", "group_member_no_perms_user", "group_user_code", False),
    ])
    def test_can_deactivate_sample_on_user_code(self, name, user_attr, sample, expected):
        """Test CanDeactivateSampleOnUserCode permission for different users."""
        request = self.factory.get('/')
        request.user = getattr(self, user_attr)
        obj = getattr(self, sample)
        self.assertEqual(CanDeactivateSampleOnUserCode().has_object_permission(request, None, obj), expected)