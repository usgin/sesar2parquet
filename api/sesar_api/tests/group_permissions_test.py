from django.test import TestCase, RequestFactory
from sesar_api.models import *
from django.contrib.auth.models import Group as AuthGroup
from sesar_api.permissions import *
from django.core.management import call_command
from sesar_api.util import get_group_user_codes_with_permission


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


    def test_can_transfer_sample(self):
        """Transfer sample permission is correctly identified"""
        # Test has permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertTrue(CanTransferGroupSample().has_object_permission(request, None, self.group))
        self.assertTrue(CanTransferGroupSample().has_object_permission(request, None, self.group))

        # Test does not have permission
        request.user = self.group_member2
        self.assertFalse(CanTransferGroupSample().has_object_permission(request, None, self.group))

    
    def test_get_group_user_codes_with_permission(self):
        """Group user codes with permission are correctly identified"""

        # Test owner/admin permission
        request = self.factory.get('/')
        request.user = self.group_owner
        self.assertEqual(get_group_user_codes_with_permission(self.group_owner_su, self.group, 'add_sample'), 'all')
        self.assertEqual(get_group_user_codes_with_permission(self.group_owner_su, self.group, 'view_sample'), 'all')
        self.assertEqual(get_group_user_codes_with_permission(self.group_owner_su, self.group, 'change_sample'), 'all')

        # Test group level permission
        request = self.factory.get('/')
        request.user = self.group_member
        self.assertEqual(get_group_user_codes_with_permission(self.group_member_su, self.group, 'add_sample'), [])
        self.assertEqual(get_group_user_codes_with_permission(self.group_member_su, self.group, 'view_sample'), 'all')

        # Test team level permission
        request = self.factory.get('/')
        request.user = self.group_member2
        self.assertEqual(get_group_user_codes_with_permission(self.group_member2_su, self.group, 'add_sample'), ['IE001'])
        self.assertEqual(get_group_user_codes_with_permission(self.group_member2_su, self.group, 'view_sample'), ['IE001'])
        self.assertEqual(get_group_user_codes_with_permission(self.group_member2_su, self.group, 'change_sample'), [])