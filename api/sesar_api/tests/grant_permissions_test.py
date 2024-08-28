from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from sesar_api.permissions import *
from django.core.management import call_command


class GrantPermissionsTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()
        self.sample_type = SampleType.objects.create(name="Sample Type")

        # get all auth groups
        self.R_group = AuthGroup.objects.get(name="read_only")
        self.RE_group = AuthGroup.objects.get(name="read_edit")
        self.CR_group = AuthGroup.objects.get(name="read_create")
        self.CRE_group = AuthGroup.objects.get(name="read_create_edit")
        self.CRED_group = AuthGroup.objects.get(name="read_create_edit_deactivate")

        # sample owner
        self.sample_owner = User.objects.create(username='SampleOwner')
        self.sample_owner_su = SesarUser.objects.create(
            auth_user=self.sample_owner, 
            fname='Sample', lname='Owner')
        self.user_code_1 = SesarUserCode.objects.create(user_code="IE001", sesar_user=self.sample_owner_su)
        self.sample_owner_sample = Sample.objects.create(name="Sample1", igsn="10.58052/IE001TEST", igsn_prefix=self.user_code_1, cur_owner=self.sample_owner_su, sample_type=self.sample_type, cur_registrant=self.sample_owner_su)

        # user code owner
        self.user_code_owner = User.objects.create(username='UserCodeOwner')
        self.user_code_owner_su = SesarUser.objects.create(
            auth_user=self.user_code_owner, 
            fname='UserCode', lname='Owner')
        self.user_code_2 = SesarUserCode.objects.create(user_code="IE002", sesar_user=self.user_code_owner_su)

        # permission denied user
        self.random_user = User.objects.create(username='RandomUser')
        self.random_user_su = SesarUser.objects.create(
            auth_user=self.random_user, 
            fname='Random', lname='User')

        # group 1(with ownership) admin
        self.group1_admin = User.objects.create(username='Admin1')
        self.group1_admin_su = SesarUser.objects.create(auth_user=self.group1_admin)

        # group 1 owns sample and user code
        self.group1 = Group.objects.create(name="Group1", owner=self.group1_admin_su)
        GroupMember.objects.create(group=self.group1, sesar_user=self.group1_admin_su, is_admin=True)
        self.user_code_3 = SesarUserCode.objects.create(user_code="IE003", group=self.group1)
        self.group_owner_sample = Sample.objects.create(name="Sample2", igsn="10.58052/IE003TEST", igsn_prefix=self.user_code_3, group_owner=self.group1, sample_type=self.sample_type, cur_registrant=self.group1_admin_su)

        # group 1 member
        self.group1_member = User.objects.create(username='Member1')
        self.group1_member_su = SesarUser.objects.create(auth_user=self.group1_member)
        GroupMember.objects.create(group=self.group1, sesar_user=self.group1_member_su, is_admin=False)

        # group 2 (with shared permissions) admin
        self.group2_admin = User.objects.create(username='Admin2')
        self.group2_admin_su = SesarUser.objects.create(auth_user=self.group2_admin)

        # group 2 with shared permissions
        self.group2 = Group.objects.create(name="Group2", owner=self.group2_admin_su)
        GroupMember.objects.create(group=self.group2, sesar_user=self.group2_admin_su, is_admin=True)

        # group 2 member
        self.group2_member = User.objects.create(username='Member2')
        self.group2_member_su = SesarUser.objects.create(auth_user=self.group2_member)
        GroupMember.objects.create(group=self.group2, sesar_user=self.group2_member_su, is_admin=False)

        # grant permission to the group
        Permission.objects.create(user_code=self.user_code_1, auth_group=self.CRE_group, group=self.group2)
        Permission.objects.create(sample=self.group_owner_sample, auth_group=self.CRE_group, group=self.group2)


    def test_sample_owner(self):
        """Can grant permission on owned sample"""
        request = self.factory.get('/')

        # Test sample owner
        request.user = self.sample_owner
        self.assertTrue(CanGrantSamplePermission().has_object_permission(request, None, self.sample_owner_sample))

        # Test not sample owner
        request.user = self.random_user
        self.assertFalse(CanGrantSamplePermission().has_object_permission(request, None, self.sample_owner_sample))

    def test_user_code_owner(self):
        """Can grant permission on owned user code"""
        request = self.factory.get('/')

        # Test user code owner
        request.user = self.user_code_owner
        self.assertTrue(CanGrantUserCodePermission().has_object_permission(request, None, self.user_code_2))

        # Test not sample owner
        request.user = self.random_user
        self.assertFalse(CanGrantUserCodePermission().has_object_permission(request, None, self.user_code_2))

    def test_group_sample_owner(self):
        """Can grant permission on group owned sample"""
        request = self.factory.get('/')

        # Test group admin
        request.user = self.group1_admin
        self.assertTrue(CanGrantSamplePermission().has_object_permission(request, None, self.group_owner_sample))

        # Test group member
        request.user = self.group1_member
        self.assertFalse(CanGrantSamplePermission().has_object_permission(request, None, self.group_owner_sample))

        # Test other user
        request.user = self.random_user
        self.assertFalse(CanGrantSamplePermission().has_object_permission(request, None, self.group_owner_sample))

    def test_group_user_code_owner(self):
        """Can grant permission on group owned user code"""
        request = self.factory.get('/')

        # Test group admin
        request.user = self.group1_admin
        self.assertTrue(CanGrantUserCodePermission().has_object_permission(request, None, self.user_code_3))

        # Test group member
        request.user = self.group1_member
        self.assertFalse(CanGrantUserCodePermission().has_object_permission(request, None, self.user_code_3))

        # Test other user
        request.user = self.random_user
        self.assertFalse(CanGrantUserCodePermission().has_object_permission(request, None, self.user_code_3))

    def test_group_shared_user_code_permissions(self):
        """Can grant permission user codes that have been shared with the group"""
        request = self.factory.get('/')

        # Test group admin
        request.user = self.group2_admin
        # Test permissions granted to group
        self.assertTrue(CanGrantUserCodePermission(group=self.group2,permissions_to_grant=['add_sample', 'view_sample']).has_object_permission(request, None, self.user_code_1))
        # Test permission not granted to group
        self.assertFalse(CanGrantUserCodePermission(group=self.group2,permissions_to_grant=['add_sample', 'deactivate_sample']).has_object_permission(request, None, self.user_code_1))

        # Test not admin
        request.user = self.group2_member
        self.assertFalse(CanGrantUserCodePermission(group=self.group2,permissions_to_grant=['add_sample', 'view_sample']).has_object_permission(request, None, self.user_code_1))

    def test_group_shared_sample_permissions(self):
        """Can grant permission on samples that have been shared with the group"""
        request = self.factory.get('/')

        # Test group admin
        request.user = self.group2_admin
        # Test permissions granted to group
        self.assertTrue(CanGrantSamplePermission(group=self.group2,permissions_to_grant=['add_sample', 'view_sample']).has_object_permission(request, None, self.group_owner_sample))
        # Test permission not granted to group
        self.assertFalse(CanGrantSamplePermission(group=self.group2,permissions_to_grant=['add_sample', 'deactivate_sample']).has_object_permission(request, None, self.group_owner_sample))

        # Test not admin
        request.user = self.group2_member
        self.assertFalse(CanGrantSamplePermission(group=self.group2,permissions_to_grant=['add_sample', 'view_sample']).has_object_permission(request, None, self.group_owner_sample))