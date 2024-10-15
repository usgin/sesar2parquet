from django.test import TestCase, RequestFactory
from sesar_api.models import *
from django.contrib.auth.models import Group as AuthGroup
from sesar_api.permissions import *
from django.core.management import call_command
from sesar_api.util import get_group_user_codes_with_permission

class SamplePermissionTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = RequestFactory()

        # get all auth groups
        self.R_group = AuthGroup.objects.get(name="Read Only")
        self.RE_group = AuthGroup.objects.get(name="Read Edit")
        self.CR_group = AuthGroup.objects.get(name="Read Create")
        self.CRE_group = AuthGroup.objects.get(name="Read Create Edit")
        self.CRED_group = AuthGroup.objects.get(name="Read Create Edit Deactivate")
        self.OWNER_group = AuthGroup.objects.get(name="Group Owner")
        self.ADMIN_group = AuthGroup.objects.get(name="Group Admin")

        # user without permissions
        self.user_no_perm = User.objects.create(username='NoPermissionUser')
        self.user_no_perm_su = SesarUser.objects.create(auth_user=self.user_no_perm)

        # test user with changing permissions
        self.test_user = User.objects.create(username='TestUser')
        self.test_user_su = SesarUser.objects.create(auth_user=self.test_user)

        # sesar staff
        self.staff = User.objects.create(username='Staff', is_staff=True)
        self.staff_su = SesarUser.objects.create(auth_user=self.staff)
        
        # sample owner
        self.sample_owner = User.objects.create(username='SampleOwner')
        self.sample_owner_su = SesarUser.objects.create(auth_user=self.sample_owner)

        # user code owner (usually identical to sample owner)
        self.user_code_owner = User.objects.create(username='UserCodeOwner')
        self.user_code_owner_su = SesarUser.objects.create(auth_user=self.user_code_owner)

        # group (with user code ownership) admin
        self.group_admin = User.objects.create(username='Admin')
        self.group_admin_su = SesarUser.objects.create(auth_user=self.group_admin)

        # group (with user code ownership) team (with permissions granted) member
        self.group_member_has_perms = User.objects.create(username='MemberHasPerms')
        self.group_member_has_perms_su = SesarUser.objects.create(auth_user=self.group_member_has_perms)

        # group (with user code ownership) no permission member
        self.group_member_no_perms = User.objects.create(username='MemberNoPerms')
        self.group_member_no_perms_su = SesarUser.objects.create(auth_user=self.group_member_no_perms)

        # setup group (with user code ownership) structure
        self.group = Group.objects.create(name="Group", owner=self.group_admin_su)
        self.group_team = Group.objects.create(name="Team", part_of_group=self.group)
        self.admin = GroupMember.objects.create(group=self.group, sesar_user=self.group_admin_su, auth_group=self.ADMIN_group)
        self.member_has_perms = GroupMember.objects.create(group=self.group, sesar_user=self.group_member_has_perms_su)
        GroupMember.objects.create(group=self.group_team,sesar_user=self.group_member_has_perms_su)
        self.member_no_perms = GroupMember.objects.create(group=self.group, sesar_user=self.group_member_no_perms_su)

        # create user code and sample
        self.user_code = SesarUserCode.objects.create(user_code="IE001", sesar_user=self.user_code_owner_su, group=self.group)
        self.user_code_2 = SesarUserCode.objects.create(user_code="IE002", sesar_user=self.user_code_owner_su, group=self.group)
        self.sample_type = SampleType.objects.create(name="Sample Type")
        self.sample = Sample.objects.create(name="Sample", igsn="10.58052/IE001TEST", igsn_prefix=self.user_code, cur_owner=self.sample_owner_su, sample_type=self.sample_type, cur_registrant=self.sample_owner_su)
        self.sample_2 = Sample.objects.create(name="Sample", igsn="10.58052/IE002TEST", igsn_prefix=self.user_code_2, cur_owner=self.sample_owner_su, sample_type=self.sample_type, cur_registrant=self.sample_owner_su, group_owner=self.group)

        

        # grant permission to the group team
        self.team_permission = Permission.objects.create(id=1, user_code=self.user_code, auth_group=self.CRED_group, group=self.group_team)

        # grant permission to the test user
        self.test_user_code_permission = Permission.objects.create(id=2, user_code=self.user_code, auth_group=self.CRED_group, sesar_user=self.test_user_su)
        self.test_sample_permission = Permission.objects.create(id=3, sample=self.sample_2, auth_group=self.CRED_group, sesar_user=self.test_user_su)
        self.test_group_permission = Permission.objects.create(id=4, user_code=self.user_code, auth_group=self.CRED_group)

    def test_is_sample_owner(self):
        """Sample owner is correctly identified"""
        # Test sample owner
        request = self.factory.get('/')
        request.user = self.sample_owner
        self.assertTrue(IsSampleOwner().has_object_permission(request, None, self.sample))

        # Test not sample owner
        request.user = self.user_no_perm
        self.assertFalse(IsSampleOwner().has_object_permission(request, None, self.sample))


    def test_can_create_sample(self):
        """Sample creation permission is correctly identified"""
        request = self.factory.get('/')

        # Test staff
        request.user = self.staff
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test sample owner
        request.user = self.sample_owner
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test user code owner
        request.user = self.user_code_owner
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on user code
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test read only permissions
        Permission.objects.filter(id=2).update(auth_group=self.R_group)
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test read create permissions
        Permission.objects.filter(id=2).update(auth_group=self.CR_group)
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test read edit permissions
        Permission.objects.filter(id=2).update(auth_group=self.RE_group)
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test read create edit permissions
        Permission.objects.filter(id=2).update(auth_group=self.CRE_group)
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on individual sample
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test read only permissions
        Permission.objects.filter(id=3).update(auth_group=self.R_group)
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test read create permissions
        Permission.objects.filter(id=3).update(auth_group=self.CR_group)
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test read edit permissions
        Permission.objects.filter(id=3).update(auth_group=self.RE_group)
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test read create edit permissions
        Permission.objects.filter(id=3).update(auth_group=self.CRE_group)
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test group level permissions when group owns user code
        # Test group admin
        request.user = self.group_admin
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test group member with permissions
        request.user = self.group_member_has_perms
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test group member without permissions
        request.user = self.group_member_no_perms
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test group admin has permission on group owned samples
        request.user = self.group_admin
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        request.user = self.group_member_no_perms
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Remove group ownership of user code and test permission shared to group
        SesarUserCode.objects.filter(user_code="IE001").update(group=None)
        Permission.objects.filter(id=4).update(group=self.group)

        request.user = self.group_admin
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))


    def test_can_edit_sample(self):
        """Sample creation permission is correctly identified"""
        request = self.factory.get('/')

        # Test staff
        request.user = self.staff
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test sample owner
        request.user = self.sample_owner
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test user code owner
        request.user = self.user_code_owner
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on user code
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test read only permissions
        Permission.objects.filter(id=2).update(auth_group=self.R_group)
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample))

        # Test read create permissions
        Permission.objects.filter(id=2).update(auth_group=self.CR_group)
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample))

        # Test read edit permissions
        Permission.objects.filter(id=2).update(auth_group=self.RE_group)
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test read create edit permissions
        Permission.objects.filter(id=2).update(auth_group=self.CRE_group)
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on individual sample
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test read only permissions
        Permission.objects.filter(id=3).update(auth_group=self.R_group)
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test read create permissions
        Permission.objects.filter(id=3).update(auth_group=self.CR_group)
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test read edit permissions
        Permission.objects.filter(id=3).update(auth_group=self.RE_group)
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test read create edit permissions
        Permission.objects.filter(id=3).update(auth_group=self.CRE_group)
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test group level permissions when group owns user code
        # Test group admin
        request.user = self.group_admin
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test group member with permissions
        request.user = self.group_member_has_perms
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test group member without permissions
        request.user = self.group_member_no_perms
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample))

        # Test group admin has permission on group owned samples
        request.user = self.group_admin
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        request.user = self.group_member_no_perms
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Remove group ownership of user code and test permission shared to group
        SesarUserCode.objects.filter(user_code="IE001").update(group=None)
        Permission.objects.filter(id=4).update(group=self.group)

        request.user = self.group_admin
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))


    def test_can_deactivate_sample(self):
        """Sample creation permission is correctly identified"""
        request = self.factory.get('/')

        # Test staff
        request.user = self.staff
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test sample owner
        request.user = self.sample_owner
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test user code owner
        request.user = self.user_code_owner
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on user code
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test read only permissions
        Permission.objects.filter(id=2).update(auth_group=self.R_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test read create permissions
        Permission.objects.filter(id=2).update(auth_group=self.CR_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test read edit permissions
        Permission.objects.filter(id=2).update(auth_group=self.RE_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test read create edit permissions
        Permission.objects.filter(id=2).update(auth_group=self.CRE_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on individual sample
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test read only permissions
        Permission.objects.filter(id=3).update(auth_group=self.R_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test read create permissions
        Permission.objects.filter(id=3).update(auth_group=self.CR_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test read edit permissions
        Permission.objects.filter(id=3).update(auth_group=self.RE_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test read create edit permissions
        Permission.objects.filter(id=3).update(auth_group=self.CRE_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test group level permissions when group owns user code
        # Test group admin
        request.user = self.group_admin
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test group member with permissions
        request.user = self.group_member_has_perms
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test group member without permissions
        request.user = self.group_member_no_perms
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test group admin has permission on group owned samples
        request.user = self.group_admin
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        request.user = self.group_member_no_perms
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Remove group ownership of user code and test permission shared to group
        SesarUserCode.objects.filter(user_code="IE001").update(group=None)
        Permission.objects.filter(id=4).update(group=self.group)

        request.user = self.group_admin
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))


class UserCodePermissionTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user_code_owner = User.objects.create(username='Owner')
        self.user_code_owner_su = SesarUser.objects.create(auth_user=self.user_code_owner)

        self.not_user_code_owner = User.objects.create(username='NotOwner')
        self.not_user_code_owner_su = SesarUser.objects.create(auth_user=self.not_user_code_owner)

        self.owner_group = Group.objects.create(name="Owner", owner=self.not_user_code_owner_su)
        self.not_owner_group = Group.objects.create(name="NotOwner", owner=self.not_user_code_owner_su)

        self.user_code = SesarUserCode.objects.create(user_code="IE001", sesar_user=self.user_code_owner_su, group=self.owner_group)

    def test_is_user_code_owner(self):
        """User code owner is correctly identified"""
        # Test user code owner
        request = self.factory.get('/')
        request.user = self.user_code_owner
        self.assertTrue(IsUserCodeOwner().has_object_permission(request, None, self.user_code))

        # Test not user code owner
        request.user = self.not_user_code_owner
        self.assertFalse(IsUserCodeOwner().has_object_permission(request, None, self.user_code))

        # Test owned by group
        self.assertTrue(IsUserCodeOwner(self.owner_group).has_object_permission(request, None, self.user_code))
        
        # Test not owned by group
        self.assertFalse(IsUserCodeOwner(self.not_owner_group).has_object_permission(request, None, self.user_code))

class GroupPermissionTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = RequestFactory()

        self.group_owner = User.objects.create(username='Owner')
        self.group_owner_su = SesarUser.objects.create(auth_user=self.group_owner)

        self.group_admin = User.objects.create(username='Admin')
        self.group_admin_su = SesarUser.objects.create(auth_user=self.group_admin)

        self.group_member = User.objects.create(username='Member')
        self.group_member_su = SesarUser.objects.create(auth_user=self.group_member)

        self.group_member2 = User.objects.create(username='Member2')
        self.group_member2_su = SesarUser.objects.create(auth_user=self.group_member2)

        self.group = Group.objects.create(name="Group", owner=self.group_owner_su)
        self.owner = GroupMember.objects.create(group=self.group, sesar_user=self.group_owner_su, auth_group=AuthGroup.objects.get(name='Group Owner'))
        self.admin = GroupMember.objects.create(group=self.group, sesar_user=self.group_admin_su, auth_group=AuthGroup.objects.get(name='Group Admin'))
        self.member = GroupMember.objects.create(group=self.group, sesar_user=self.group_member_su, auth_group=AuthGroup.objects.get(name="Read Only"))
        self.member2 = GroupMember.objects.create(group=self.group, sesar_user=self.group_member2_su)

        self.user_code1 = SesarUserCode.objects.create(user_code="IE001", group=self.group)
        self.user_code2 = SesarUserCode.objects.create(user_code="IE002", group=self.group)

        self.team = Group.objects.create(name="team", part_of_group=self.group)
        GroupMember.objects.create(group=self.team, sesar_user=self.group_member2_su)
        Permission.objects.create(user_code=self.user_code1, group=self.team, auth_group=AuthGroup.objects.get(name="Read Create"))


    def test_is_group_owner(self):
        """Group owner is correctly identified"""
        # Test group owner
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(IsGroupOwner().has_object_permission(request, None, self.group))

        # Test not group owner
        request.user = self.group_member
        self.assertFalse(IsGroupOwner().has_object_permission(request, None, self.group))

    def test_can_add_group_member(self):
        """Add group member permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanAddGroupMember().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member
        self.assertFalse(CanAddGroupMember().has_object_permission(request, None, self.group))

    def test_can_change_group_member(self):
        """Change group member permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanChangeGroupMember().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member
        self.assertFalse(CanChangeGroupMember().has_object_permission(request, None, self.group))

    def test_can_delete_group_member(self):
        """Delete group member permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanDeleteGroupMember().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member
        self.assertFalse(CanDeleteGroupMember().has_object_permission(request, None, self.group))

    def test_can_add_group(self):
        """Add group permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanAddGroup().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member
        self.assertFalse(CanAddGroup().has_object_permission(request, None, self.group))

    def test_can_change_group(self):
        """Change group permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanChangeGroup().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member
        self.assertFalse(CanChangeGroup().has_object_permission(request, None, self.group))

    def test_can_delete_group(self):
        """Delete group permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanDeleteGroup().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member
        self.assertFalse(CanDeleteGroup().has_object_permission(request, None, self.group))


    def test_can_view_group_samples(self):
        """View group sample permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanViewGroupSamples().has_object_permission(request, None, self.group))
        self.assertTrue(CanViewGroupSamples().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member2
        self.assertFalse(CanViewGroupSamples().has_object_permission(request, None, self.group))

    
    def test_can_add_user_code(self):
        """Add user code permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanAddGroupUserCode().has_object_permission(request, None, self.group))
        self.assertTrue(CanAddGroupUserCode().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member2
        self.assertFalse(CanAddGroupUserCode().has_object_permission(request, None, self.group))


    def test_can_delete_user_code(self):
        """Delete user code permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanDeleteGroupUserCode().has_object_permission(request, None, self.group))
        self.assertTrue(CanDeleteGroupUserCode().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member2
        self.assertFalse(CanDeleteGroupUserCode().has_object_permission(request, None, self.group))

    
    def test_get_group_user_codes_with_permission(self):
        """Group user codes with permission are correctly identified"""

        # Test owner/admin permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertEqual(get_group_user_codes_with_permission(self.group_owner_su, self.group, 'add_sample'), ['IE001', 'IE002'])
        self.assertEqual(get_group_user_codes_with_permission(self.group_owner_su, self.group, 'view_sample'), ['IE001', 'IE002'])
        self.assertEqual(get_group_user_codes_with_permission(self.group_owner_su, self.group, 'change_sample'), ['IE001', 'IE002'])

        # Test group level permission
        request = self.factory.get('/')
        request.user = self.group_member
        self.assertEqual(get_group_user_codes_with_permission(self.group_member_su, self.group, 'add_sample'), [])
        self.assertEqual(get_group_user_codes_with_permission(self.group_member_su, self.group, 'view_sample'), ['IE001', 'IE002'])

        # Test team level permission
        request = self.factory.get('/')
        request.user = self.group_member2
        self.assertEqual(get_group_user_codes_with_permission(self.group_member2_su, self.group, 'add_sample'), ['IE001'])
        self.assertEqual(get_group_user_codes_with_permission(self.group_member2_su, self.group, 'view_sample'), ['IE001'])
        self.assertEqual(get_group_user_codes_with_permission(self.group_member2_su, self.group, 'change_sample'), [])