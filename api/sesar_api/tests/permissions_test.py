from django.test import TestCase, RequestFactory
from sesar_api.models import *
from django.contrib.auth.models import Group
from sesar_api.permissions import *
from django.core.management import call_command



class SamplePermissionTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = RequestFactory()

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

        # organization (with user code ownership) admin
        self.organization_admin = User.objects.create(username='Admin')
        self.organization_admin_su = SesarUser.objects.create(auth_user=self.organization_admin)

        # organization (with user code ownership) team (with permissions granted) member
        self.organization_member_has_perms = User.objects.create(username='MemberHasPerms')
        self.organization_member_has_perms_su = SesarUser.objects.create(auth_user=self.organization_member_has_perms)

        # organization (with user code ownership) no permission member
        self.organization_member_no_perms = User.objects.create(username='MemberNoPerms')
        self.organization_member_no_perms_su = SesarUser.objects.create(auth_user=self.organization_member_no_perms)

        # setup organization (with user code ownership) structure
        self.organization = Organization.objects.create(name="Organization", owner=self.organization_admin_su)
        self.organization_team = OrganizationTeam.objects.create(name="Team", organization=self.organization)
        self.admin = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.organization_admin_su, is_admin=True)
        self.member_has_perms = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.organization_member_has_perms_su, is_admin=False)
        OrganizationTeamMember.objects.create(team=self.organization_team,member=self.member_has_perms)
        self.member_no_perms = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.organization_member_no_perms_su, is_admin=False)

        # create user code and sample
        self.user_code = SesarUserCode.objects.create(user_code="IE001", sesar_user=self.user_code_owner_su, organization=self.organization)
        self.user_code_2 = SesarUserCode.objects.create(user_code="IE002", sesar_user=self.user_code_owner_su, organization=self.organization)
        self.sample_type = SampleType.objects.create(name="Sample Type")
        self.sample = Sample.objects.create(name="Sample", igsn="10.58052/IE001TEST", igsn_prefix=self.user_code, cur_owner=self.sample_owner_su, sample_type=self.sample_type, cur_registrant=self.sample_owner_su)
        self.sample_2 = Sample.objects.create(name="Sample", igsn="10.58052/IE002TEST", igsn_prefix=self.user_code_2, cur_owner=self.sample_owner_su, sample_type=self.sample_type, cur_registrant=self.sample_owner_su)

        # get all auth groups
        self.R_group = Group.objects.get(name="read_only")
        self.RE_group = Group.objects.get(name="read_edit")
        self.CR_group = Group.objects.get(name="read_create")
        self.CRE_group = Group.objects.get(name="read_create_edit")
        self.CRED_group = Group.objects.get(name="read_create_edit_deactivate")

        # grant permission to the organization team
        self.team_permission = SamplePermission.objects.create(id=1, user_code=self.user_code, auth_group=self.CRED_group, organization_team=self.organization_team)

        # grant permission to the test user
        self.test_user_code_permission = SamplePermission.objects.create(id=2, user_code=self.user_code, auth_group=self.CRED_group, sesar_user=self.test_user_su)
        self.test_sample_permission = SamplePermission.objects.create(id=3, sample=self.sample_2, auth_group=self.CRED_group, sesar_user=self.test_user_su)
        self.test_organization_permission = SamplePermission.objects.create(id=4, user_code=self.user_code, auth_group=self.CRED_group)

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
        SamplePermission.objects.filter(id=2).update(auth_group=self.R_group)
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test read create permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.CR_group)
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test read edit permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.RE_group)
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test read create edit permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.CRE_group)
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on individual sample
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test read only permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.R_group)
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test read create permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.CR_group)
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test read edit permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.RE_group)
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test read create edit permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.CRE_group)
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample_2))

        # Test organization level permissions when organization owns user code
        # Test organization admin
        request.user = self.organization_admin
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test organization member with permissions
        request.user = self.organization_member_has_perms
        self.assertTrue(CanCreateSample().has_object_permission(request, None, self.sample))

        # Test organization member without permissions
        request.user = self.organization_member_no_perms
        self.assertFalse(CanCreateSample().has_object_permission(request, None, self.sample))

        # Remove organization ownership of user code and test permission shared to organization
        SesarUserCode.objects.filter(user_code="IE001").update(organization=None)
        SamplePermission.objects.filter(id=4).update(organization=self.organization)

        request.user = self.organization_admin
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
        SamplePermission.objects.filter(id=2).update(auth_group=self.R_group)
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample))

        # Test read create permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.CR_group)
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample))

        # Test read edit permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.RE_group)
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test read create edit permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.CRE_group)
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on individual sample
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test read only permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.R_group)
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test read create permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.CR_group)
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test read edit permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.RE_group)
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test read create edit permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.CRE_group)
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample_2))

        # Test organization level permissions when organization owns user code
        # Test organization admin
        request.user = self.organization_admin
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test organization member with permissions
        request.user = self.organization_member_has_perms
        self.assertTrue(CanEditSample().has_object_permission(request, None, self.sample))

        # Test organization member without permissions
        request.user = self.organization_member_no_perms
        self.assertFalse(CanEditSample().has_object_permission(request, None, self.sample))

        # Remove organization ownership of user code and test permission shared to organization
        SesarUserCode.objects.filter(user_code="IE001").update(organization=None)
        SamplePermission.objects.filter(id=4).update(organization=self.organization)

        request.user = self.organization_admin
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
        SamplePermission.objects.filter(id=2).update(auth_group=self.R_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test read create permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.CR_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test read edit permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.RE_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test read create edit permissions
        SamplePermission.objects.filter(id=2).update(auth_group=self.CRE_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test individual with permissions on individual sample
        # Test create read edit deactivate permissions
        request.user = self.test_user
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test read only permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.R_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test read create permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.CR_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test read edit permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.RE_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test read create edit permissions
        SamplePermission.objects.filter(id=3).update(auth_group=self.CRE_group)
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample_2))

        # Test organization level permissions when organization owns user code
        # Test organization admin
        request.user = self.organization_admin
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test organization member with permissions
        request.user = self.organization_member_has_perms
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Test organization member without permissions
        request.user = self.organization_member_no_perms
        self.assertFalse(CanDeactivateSample().has_object_permission(request, None, self.sample))

        # Remove organization ownership of user code and test permission shared to organization
        SesarUserCode.objects.filter(user_code="IE001").update(organization=None)
        SamplePermission.objects.filter(id=4).update(organization=self.organization)

        request.user = self.organization_admin
        self.assertTrue(CanDeactivateSample().has_object_permission(request, None, self.sample))


class UserCodePermissionTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.user_code_owner = User.objects.create(username='Owner')
        self.user_code_owner_su = SesarUser.objects.create(auth_user=self.user_code_owner)

        self.not_user_code_owner = User.objects.create(username='NotOwner')
        self.not_user_code_owner_su = SesarUser.objects.create(auth_user=self.not_user_code_owner)

        self.owner_organization = Organization.objects.create(name="Owner", owner=self.not_user_code_owner_su)
        self.not_owner_organization = Organization.objects.create(name="NotOwner", owner=self.not_user_code_owner_su)

        self.user_code = SesarUserCode.objects.create(user_code="IE001", sesar_user=self.user_code_owner_su, organization=self.owner_organization)

    def test_is_user_code_owner(self):
        """User code owner is correctly identified"""
        # Test user code owner
        request = self.factory.get('/')
        request.user = self.user_code_owner
        self.assertTrue(IsUserCodeOwner().has_object_permission(request, None, self.user_code))

        # Test not user code owner
        request.user = self.not_user_code_owner
        self.assertFalse(IsUserCodeOwner().has_object_permission(request, None, self.user_code))

        # Test owned by organization
        self.assertTrue(IsUserCodeOwner(self.owner_organization).has_object_permission(request, None, self.user_code))
        
        # Test not owned by organization
        self.assertFalse(IsUserCodeOwner(self.not_owner_organization).has_object_permission(request, None, self.user_code))

class OrganizationPermissionTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.organization_owner = User.objects.create(username='Owner')
        self.organization_owner_su = SesarUser.objects.create(auth_user=self.organization_owner)

        self.organization_admin = User.objects.create(username='Admin')
        self.organization_admin_su = SesarUser.objects.create(auth_user=self.organization_admin)

        self.organization_member = User.objects.create(username='Member')
        self.organization_member_su = SesarUser.objects.create(auth_user=self.organization_member)

        self.organization = Organization.objects.create(name="Organization", owner=self.organization_owner_su)
        self.admin = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.organization_admin_su, is_admin=True)
        self.member = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.organization_member_su, is_admin=False)

    def test_is_organization_owner(self):
        """Organization owner is correctly identified"""
        # Test organization owner
        request = self.factory.get('/')
        request.user = self.organization_owner
        self.assertTrue(IsOrganizationOwner().has_object_permission(request, None, self.organization))

        # Test not organization owner
        request.user = self.organization_member
        self.assertFalse(IsOrganizationOwner().has_object_permission(request, None, self.organization))

    def test_is_organization_admin(self):
        """Organization admin is correctly identified"""
        # Test organization admin
        request = self.factory.get('/')
        request.user = self.organization_admin
        self.assertTrue(IsOrganizationAdmin().has_object_permission(request, None, self.organization))

        # Test not organization admin
        request.user = self.organization_member
        self.assertFalse(IsOrganizationAdmin().has_object_permission(request, None, self.organization))
        