from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *


class OrganizationMemberTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='Owner')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1')

        self.member1 = User.objects.create(username='Member1')
        self.member1_su = SesarUser.objects.create(auth_user=self.member1, fname='User', lname='2')

        self.member2 = User.objects.create(username='Member2')
        self.member2_su = SesarUser.objects.create(auth_user=self.member2, fname='User', lname='2')

        self.new_member = User.objects.create(username='NewMember')
        self.new_member_su = SesarUser.objects.create(auth_user=self.new_member, fname='User', lname='3')

        # setup organization structure
        self.organization = Organization.objects.create(name="test1", owner=self.user_su)
        self.org_owner = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.user_su, is_admin=True)
        self.org_member1 = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.member1_su, is_admin=False)
        self.org_member2 = OrganizationMember.objects.create(organization=self.organization, sesar_user=self.member2_su, is_admin=False)


    def test_view_organization_members(self):
        """Can view an organizations members"""
        request = self.factory.get('/api/organization/test1/members/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_organization_members(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)


    def test_create_organization_member(self):
        """Can create a new organization member"""
        request = self.factory.post('/api/organization/members/create/',{'organization': self.organization.pk, 'sesar_user': self.new_member_su.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_organization_member(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.organization.members.filter(sesar_user_id=self.new_member_su.pk).exists())


    def test_update_organization_member(self):
        """Can update an organization member"""
        request = self.factory.post('/api/organization/members/update/',{'id':self.org_member1.pk, 'is_admin':True})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = update_organization_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OrganizationMember.objects.filter(id=self.org_member1.pk, is_admin=True).exists())


    def test_delete_organization_member(self):
        """Can delete an organization member"""
        request = self.factory.post('/api/organization/members/delete/',{'id':self.org_member2.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = delete_organization_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(OrganizationMember.objects.filter(id=self.org_member2.pk).exists())