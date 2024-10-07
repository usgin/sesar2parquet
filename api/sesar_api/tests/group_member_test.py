from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command


class GroupMemberTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()

        self.user = User.objects.create(username='Owner')
        self.user_su = SesarUser.objects.create(auth_user=self.user, fname='User', lname='1')

        self.member1 = User.objects.create(username='Member1')
        self.member1_su = SesarUser.objects.create(auth_user=self.member1, fname='User', lname='2')

        self.member2 = User.objects.create(username='Member2')
        self.member2_su = SesarUser.objects.create(auth_user=self.member2, fname='User', lname='2')

        self.new_member = User.objects.create(username='NewMember')
        self.new_member_su = SesarUser.objects.create(auth_user=self.new_member, fname='User', lname='3')

        # setup group structure
        self.group = Group.objects.create(name="test1", owner=self.user_su)
        self.org_owner = GroupMember.objects.create(group=self.group, sesar_user=self.user_su, auth_group=AuthGroup.objects.get(name='group_owner'))
        self.org_member1 = GroupMember.objects.create(group=self.group, sesar_user=self.member1_su)
        self.org_member2 = GroupMember.objects.create(group=self.group, sesar_user=self.member2_su)


    def test_view_group_members(self):
        """Can view an groups members"""
        request = self.factory.get('/api/group/test1/members/')
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = view_group_members(request, name='test1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)


    def test_create_group_member(self):
        """Can create a new group member"""
        request = self.factory.post('/api/group/members/create/',{'group': self.group.pk, 'sesar_user': self.new_member_su.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = create_group_member(request)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.group.members.filter(sesar_user_id=self.new_member_su.pk).exists())


    def test_update_group_member(self):
        """Can update an group member"""
        request = self.factory.post('/api/group/members/update/',{'id':self.org_member1.pk, 'auth_group':AuthGroup.objects.get(name='group_admin').pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = update_group_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(GroupMember.objects.filter(id=self.org_member1.pk, auth_group=AuthGroup.objects.get(name='group_admin')).exists())


    def test_delete_group_member(self):
        """Can delete an group member"""
        request = self.factory.post('/api/group/members/delete/',{'id':self.org_member2.pk})
        request.user = self.user
        force_authenticate(request, user=self.user)
        response = delete_group_member(request)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GroupMember.objects.filter(id=self.org_member2.pk).exists())