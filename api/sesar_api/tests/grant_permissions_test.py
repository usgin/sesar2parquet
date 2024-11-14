from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from sesar_api.permissions import *
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth.models import Group as AuthGroup


class GrantPermissionsTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()
        self.sample_type = SampleType.objects.create(name="Sample Type")

        # get all auth groups
        self.R_group = AuthGroup.objects.get(name="Read Only")
        self.RE_group = AuthGroup.objects.get(name="Read Edit")
        self.CR_group = AuthGroup.objects.get(name="Read Create")
        self.CRE_group = AuthGroup.objects.get(name="Read Create Edit")
        self.CRED_group = AuthGroup.objects.get(name="Read Create Edit Deactivate")

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
        GroupMember.objects.create(group=self.group1, sesar_user=self.group1_admin_su, auth_group=AuthGroup.objects.get(name='Group Owner'))
        self.user_code_3 = SesarUserCode.objects.create(user_code="IE003", group=self.group1)
        self.group_owner_sample = Sample.objects.create(name="Sample2", igsn="10.58052/IE003TEST", igsn_prefix=self.user_code_3, group_owner=self.group1, sample_type=self.sample_type, cur_registrant=self.group1_admin_su)

        # group 1 member
        self.group1_member = User.objects.create(username='Member1')
        self.group1_member_su = SesarUser.objects.create(auth_user=self.group1_member)
        GroupMember.objects.create(group=self.group1, sesar_user=self.group1_member_su)

        # group 1 team with permissions
        self.group1_team = Group.objects.create(name='Group1Team1', part_of_group=self.group1)
        GroupMember.objects.create(group=self.group1_team, sesar_user=self.group1_member_su)
        self.permission1 = Permission.objects.create(user_code=self.user_code_3, auth_group=self.CRED_group, group=self.group1_team, granted_by_group=self.group1)

        # group 2 (with shared permissions) admin
        self.group2_admin = User.objects.create(username='Admin2')
        self.group2_admin_su = SesarUser.objects.create(auth_user=self.group2_admin)

        # group 2 with shared permissions
        self.group2 = Group.objects.create(name="Group2", owner=self.group2_admin_su)
        GroupMember.objects.create(group=self.group2, sesar_user=self.group2_admin_su, auth_group=AuthGroup.objects.get(name='Group Admin'))

        # group 2 member
        self.group2_member = User.objects.create(username='Member2')
        self.group2_member_su = SesarUser.objects.create(auth_user=self.group2_member)
        GroupMember.objects.create(group=self.group2, sesar_user=self.group2_member_su)

        # grant permission to the group
        self.permission2 = Permission.objects.create(user_code=self.user_code_1, auth_group=self.CRE_group, group=self.group2)
        self.permission3 = Permission.objects.create(sample=self.group_owner_sample, auth_group=self.CRE_group, group=self.group2, granted_by_group=self.group1)

        # user with shared permissions
        self.user_shared_perms = User.objects.create(username='HasSharedPermissions')
        self.user_shared_perms_su = SesarUser.objects.create(auth_user=self.user_shared_perms, fname='Has', lname='Shared')
        self.permission4 = Permission.objects.create(sample=self.sample_owner_sample, auth_group=self.CRE_group, sesar_user=self.user_shared_perms_su, orcid_id='0000-0000-0000-0001', geopass_id='test@gmail.com')


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
        self.assertTrue(CanGrantUserCodePermission(group=self.group2,permissions_to_grant='Read Create').has_object_permission(request, None, self.user_code_1))
        # Test permission not granted to group
        self.assertFalse(CanGrantUserCodePermission(group=self.group2,permissions_to_grant='Read Create_edit_deactivate').has_object_permission(request, None, self.user_code_1))

        # Test not admin
        request.user = self.group2_member
        self.assertFalse(CanGrantUserCodePermission(group=self.group2,permissions_to_grant='Read Create').has_object_permission(request, None, self.user_code_1))


    def test_group_shared_sample_permissions(self):
        """Can grant permission on samples that have been shared with the group"""
        request = self.factory.get('/')

        # Test group admin
        request.user = self.group2_admin
        # Test permissions granted to group
        self.assertTrue(CanGrantSamplePermission(group=self.group2,permissions_to_grant='Read Create').has_object_permission(request, None, self.group_owner_sample))
        # Test permission not granted to group
        self.assertFalse(CanGrantSamplePermission(group=self.group2,permissions_to_grant='Read Create Edit Deactivate').has_object_permission(request, None, self.group_owner_sample))

        # Test not admin
        request.user = self.group2_member
        self.assertFalse(CanGrantSamplePermission(group=self.group2,permissions_to_grant='Read Create').has_object_permission(request, None, self.group_owner_sample))


    def test_can_edit_permission(self):
        """Can edit permissions of managed samples/usercodes"""
        request = self.factory.get('/')

        # Test sample owner
        request.user = self.sample_owner
        self.assertFalse(CanEditPermission().has_object_permission(request, None, self.permission1))
        self.assertTrue(CanEditPermission().has_object_permission(request, None, self.permission2))
        self.assertFalse(CanEditPermission().has_object_permission(request, None, self.permission3))
        self.assertTrue(CanEditPermission().has_object_permission(request, None, self.permission4))

        # Test group admin
        request.user = self.group1_admin
        self.assertTrue(CanEditPermission().has_object_permission(request, None, self.permission1))
        self.assertFalse(CanEditPermission().has_object_permission(request, None, self.permission2))
        self.assertTrue(CanEditPermission().has_object_permission(request, None, self.permission3))
        self.assertFalse(CanEditPermission().has_object_permission(request, None, self.permission4))


    def test_view_user_permissions(self):
        """Can view permissions shared to user"""
        request = self.factory.get('/api/permissions/user/')
        request.user = self.user_shared_perms
        force_authenticate(request, user=self.user_shared_perms)
        response = view_user_permissions(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertTrue(any(perm.get('sample') == '10.58052/IE001TEST' and perm.get('sesar_user') == 'Has Shared' for perm in response.data))


    def test_view_user_permissions_shared_to_others(self):
        """Can view permissions shared by user to others"""
        request = self.factory.get('/api/permissions/user-shared/')
        request.user = self.sample_owner
        force_authenticate(request, user=self.sample_owner)
        response = view_user_permissions_shared_to_others(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertTrue(any(perm.get('sample') == '10.58052/IE001TEST' and perm.get('sesar_user') == 'Has Shared' for perm in response.data))


    def test_group_permissions(self):
        """Can view group permissions"""

        # Test group permissions
        request = self.factory.get('/api/permissions/group/')
        request.user = self.sample_owner
        force_authenticate(request, user=self.sample_owner)
        response = view_group_permissions(request, name='Group1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['shared_to_group'], [])
        self.assertTrue(any(perm.get('user_code') == 'IE003' and perm.get('group') == 'Group1Team1' for perm in response.data['shared_by_group']))

        # Test view works with sub groups
        request = self.factory.get('/api/permissions/group/?part_of_group=Group1')
        request.user = self.sample_owner
        force_authenticate(request, user=self.sample_owner)
        response = view_group_permissions(request, name='Group1Team1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(perm.get('user_code') == 'IE003' and perm.get('group') == 'Group1Team1' for perm in response.data['shared_to_group']))
        self.assertEqual(response.data['shared_by_group'], [])


    def test_create_permission(self):
        """Can create permission"""
        self.test_user = User.objects.create(username='TestUser')
        self.test_user_su = SesarUser.objects.create(
            auth_user=self.test_user, 
            fname='Test', lname='User')
        request = self.factory.post('/api/permissions/create/', 
            {'user_code': 'IE001', 
            'auth_group': 'Read Create Edit Deactivate',
            'sesar_user': self.test_user_su.pk})
        request.user = self.sample_owner
        force_authenticate(request, user=self.sample_owner)
        
        response = create_permission(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Permission.objects.filter(user_code='IE001', sesar_user=self.test_user_su).exists())


    def test_update_permission(self):
        """Can update permission"""
        request = self.factory.post('/api/permissions/update/',{'id':self.permission4.pk, 'deactivate_date': '2024-12-25 00:00'})
        request.user = self.sample_owner
        force_authenticate(request, user=self.sample_owner)
        self.assertIsNone(Permission.objects.get(id=self.permission4.pk).deactivate_date)
        response = update_permission(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Permission.objects.get(id=self.permission4.pk).deactivate_date)


    def test_delete_permission(self):
        """Can delete permission"""
        request = self.factory.post('/api/permissions/delete/',{'id':self.permission2.pk})
        request.user = self.sample_owner
        force_authenticate(request, user=self.sample_owner)
        self.assertTrue(Permission.objects.filter(id=self.permission2.pk).exists())
        response = delete_permission(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Permission.objects.filter(id=self.permission2.pk).exists())