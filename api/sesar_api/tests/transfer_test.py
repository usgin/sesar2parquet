from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from sesar_api.models import *
from sesar_api.views import *
from django.core.management import call_command
import os


class TransferTestCase(TestCase):
    def setUp(self):
        call_command('create_auth_groups')
        self.factory = APIRequestFactory()
        self.sample_type = SampleType.objects.create(name="Sample Type")

        # sesar_owner
        self.sesar_owner = User.objects.create(username='sesar_owner')
        self.sesar_owner_su = SesarUser.objects.create(sesar_user_id=int(os.environ.get('SESAR_OWNER')), auth_user=self.sesar_owner, fname='Sesar', lname='Owner', orcid='0000-0000-0000')

        # orig user
        self.orig_user = User.objects.create(username='orig_user')
        self.orig_user_su = SesarUser.objects.create(auth_user=self.orig_user, fname='Orig', lname='User', orcid='0000-0000-0001')
        # sesar codes owned by orig_user
        self.sesar_code = SesarCode.objects.create(sesar_user=self.orig_user_su, sesar_code='IE001')
        self.sesar_code2 = SesarCode.objects.create(sesar_user=self.orig_user_su, sesar_code='IE002')
        # samples owned by orig user
        self.user_sample = Sample.objects.create(name="UserSample1", igsn="10.58052/IE001TEST", igsn_prefix=self.sesar_code, cur_owner=self.orig_user_su, sample_type=self.sample_type, cur_registrant=self.orig_user_su)
        self.user_sample2 = Sample.objects.create(name="UserSample2", igsn="10.58052/IE001TEST2", igsn_prefix=self.sesar_code, cur_owner=self.orig_user_su, sample_type=self.sample_type, cur_registrant=self.orig_user_su)
        self.user_sample3 = Sample.objects.create(name="UserSample3", igsn="10.58052/IE002TEST2", igsn_prefix=self.sesar_code2, cur_owner=self.orig_user_su, sample_type=self.sample_type, cur_registrant=self.orig_user_su)

        # new user
        self.new_user = User.objects.create(username='new_user')
        self.new_user_su = SesarUser.objects.create(auth_user=self.new_user, fname='New', lname='User', orcid='0000-0000-0002')

        # team admin
        self.team_admin = User.objects.create(username='team_admin')
        self.team_admin_su = SesarUser.objects.create(auth_user=self.team_admin, fname='Team', lname='Admin', orcid='0000-0000-0003')

        # team owned by admin
        self.team = Team.objects.create(name="team", owner=self.team_admin_su, contact_email='test@gmail.com')
        TeamMember.objects.create(team=self.team, sesar_user=self.team_admin_su, auth_group=AuthGroup.objects.get(name='Team Owner'))
        # team sesar code
        self.sesar_code3 = SesarCode.objects.create(team=self.team, sesar_code='IE003')
        # team owned samples
        self.team_sample = Sample.objects.create(name="TeamSample1", igsn="10.58052/IE003TEST", igsn_prefix=self.sesar_code3, sample_type=self.sample_type, cur_registrant=self.team_admin_su, team_owner=self.team)
        self.team_sample2 = Sample.objects.create(name="TeamSample2", igsn="10.58052/IE003TEST2", igsn_prefix=self.sesar_code3, sample_type=self.sample_type, cur_registrant=self.team_admin_su, team_owner=self.team)

        # user sample pending transfer to new user
        self.user_pending_sample = Sample.objects.create(name="PendingTransferUserSample", igsn="10.58052/IE001TransferMe", igsn_prefix=self.sesar_code, cur_owner=self.sesar_owner_su, sample_type=self.sample_type, cur_registrant=self.orig_user_su)
        transfer_data = {
            'igsns': ['10.58052/IE001TransferMe']
        }
        self.user_transfer = TransferHistory.objects.create(transfer_by=self.orig_user_su, orig_user=self.orig_user_su, new_user=self.new_user_su, data=transfer_data, status='pending')
        # user sample pending transfer to new team
        self.user_pending_sample2 = Sample.objects.create(name="PendingTransferUserSample2", igsn="10.58052/IE002TransferMe", igsn_prefix=self.sesar_code2, cur_owner=self.sesar_owner_su, sample_type=self.sample_type, cur_registrant=self.orig_user_su)
        transfer_data = {
            'igsns': ['10.58052/IE002TransferMe']
        }
        self.user_transfer2 = TransferHistory.objects.create(transfer_by=self.orig_user_su, orig_user=self.orig_user_su, new_team=self.team, data=transfer_data, status='pending')
        # team sample pending transfer to new user
        self.team_pending_sample = Sample.objects.create(name="PendingTransferTeamSample", igsn="10.58052/IE003TransferMe", igsn_prefix=self.sesar_code3, cur_owner=self.sesar_owner_su, team_owner=None, sample_type=self.sample_type, cur_registrant=self.team_admin_su)
        transfer_data = {
            'igsns': ['10.58052/IE003TransferMe']
        }
        self.team_transfer = TransferHistory.objects.create(transfer_by=self.team_admin_su, new_user=self.new_user_su, orig_team=self.team, data=transfer_data, status='pending')


    def test_view_transfers(self):
        """Can view all transfers"""
        request = self.factory.get('/api/transfer/')
        request.user = self.orig_user
        force_authenticate(request, user=self.orig_user)
        response = view_transfers(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        request = self.factory.get('/api/transfer/?team=team')
        request.user = self.team_admin
        force_authenticate(request, user=self.team_admin)
        response = view_transfers(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)


    def test_create_transfer_all(self):
        """Can create transfer for all samples"""
        data = {
            'orig_user': '0000-0000-0001',
            'new_user': '0000-0000-0002',
            'transfer_type': 'all'
        }
        request = self.factory.post('/api/transfer/create/', data)
        request.user = self.orig_user
        force_authenticate(request, user=self.orig_user)
        response = create_transfer(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TransferHistory.objects.filter(orig_user=self.orig_user_su).count(), 3)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su).count(), 0)

    
    def test_create_transfer_sesar_code(self):
        """Can create transfer for all samples in sesar code"""
        data = {
            'orig_user': '0000-0000-0001',
            'new_user': '0000-0000-0002',
            'transfer_type': 'sesar_code',
            'sesar_code': 'IE001'
        }
        request = self.factory.post('/api/transfer/create/', data)
        request.user = self.orig_user
        force_authenticate(request, user=self.orig_user)
        response = create_transfer(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TransferHistory.objects.filter(orig_user=self.orig_user_su).count(), 3)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su, igsn_prefix=self.sesar_code).count(), 0)


    def test_create_transfer_igsn_list(self):
        """Can create transfer for all samples in sesar code"""
        data = {
            'orig_user': '0000-0000-0001',
            'new_user': '0000-0000-0002',
            'transfer_type': 'sample_list',
            'sample_list': '["10.58052/IE001TEST", "10.58052/IE002TEST2"]'
        }
        request = self.factory.post('/api/transfer/create/', data)
        request.user = self.orig_user
        force_authenticate(request, user=self.orig_user)
        response = create_transfer(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TransferHistory.objects.filter(orig_user=self.orig_user_su).count(), 3)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su, igsn_prefix=self.sesar_code).count(), 1)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su).count(), 1)

    
    def test_create_transfer_team(self):
        """Can create transfer for samples in team"""
        data = {
            'orig_team': 'team',
            'new_user': '0000-0000-0002',
            'transfer_type': 'all'
        }
        request = self.factory.post('/api/transfer/create/', data)
        request.user = self.team_admin
        force_authenticate(request, user=self.team_admin)
        response = create_transfer(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TransferHistory.objects.filter(orig_team=self.team).count(), 2)
        self.assertEqual(Sample.objects.filter(team_owner=self.team).count(), 0)
        self.assertEqual(Sample.objects.filter(cur_owner=self.sesar_owner_su).count(), 5)


    def test_update_transfer_to_user_complete(self):
        """Can complete transfer to user"""
        data = {
            'id': self.user_transfer.pk,
            'status': 'completed'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.new_user
        force_authenticate(request, user=self.new_user)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(cur_owner=self.new_user_su).count(), 1)


    def test_update_transfer_to_user_reject(self):
        """Can reject transfer to user"""
        data = {
            'id': self.user_transfer.pk,
            'status': 'rejected'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.new_user
        force_authenticate(request, user=self.new_user)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(cur_owner=self.new_user_su).count(), 0)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su).count(), 4)


    def test_update_transfer_to_user_cancel(self):
        """Can cancel transfer to user"""
        data = {
            'id': self.user_transfer.pk,
            'status': 'canceled'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.orig_user
        force_authenticate(request, user=self.orig_user)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(cur_owner=self.new_user_su).count(), 0)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su).count(), 4)


    def test_update_transfer_to_team_complete(self):
        """Can complete transfer to team"""
        data = {
            'id': self.user_transfer2.pk,
            'status': 'completed'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.team_admin
        force_authenticate(request, user=self.team_admin)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(team_owner=self.team).count(), 3)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su).count(), 3)

    
    def test_update_transfer_to_team_reject(self):
        """Can reject transfer to team"""
        data = {
            'id': self.user_transfer2.pk,
            'status': 'rejected'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.team_admin
        force_authenticate(request, user=self.team_admin)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(team_owner=self.team).count(), 2)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su).count(), 4)


    def test_update_transfer_to_team_cancel(self):
        """Can cancel transfer to team"""
        data = {
            'id': self.user_transfer2.pk,
            'status': 'canceled'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.orig_user
        force_authenticate(request, user=self.orig_user)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(team_owner=self.team).count(), 2)
        self.assertEqual(Sample.objects.filter(cur_owner=self.orig_user_su).count(), 4)


    def test_update_transfer_by_team_complete(self):
        """Can complete transfer to team"""
        data = {
            'id': self.team_transfer.pk,
            'status': 'completed'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.new_user
        force_authenticate(request, user=self.new_user)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(team_owner=self.team).count(), 2)
        self.assertEqual(Sample.objects.filter(cur_owner=self.new_user_su).count(), 1)


    def test_update_transfer_by_team_reject(self):
        """Can reject transfer to team"""
        data = {
            'id': self.team_transfer.pk,
            'status': 'rejected'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.new_user
        force_authenticate(request, user=self.new_user)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(team_owner=self.team).count(), 3)
        self.assertEqual(Sample.objects.filter(cur_owner=self.new_user_su).count(), 0)


    def test_update_transfer_by_team_cancel(self):
        """Can cancel transfer to team"""
        data = {
            'id': self.team_transfer.pk,
            'status': 'canceled'
        }
        request = self.factory.post('/api/transfer/update/', data)
        request.user = self.team_admin
        force_authenticate(request, user=self.team_admin)
        response = update_transfer(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sample.objects.filter(team_owner=self.team).count(), 3)
        self.assertEqual(Sample.objects.filter(cur_owner=self.new_user_su).count(), 0)