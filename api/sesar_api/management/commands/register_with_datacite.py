import os
import sys

import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from sesar_api.models import Sample
from sesar_api.classes import IGSNToDatacite


class Command(BaseCommand):
    help = 'Creates the initial admin user, or updates the password to reflect the latest value'

    def register_igsns(self):
        samples = Sample.objects.filter(metadata_store_status__isnull=True, archive_date__isnull=True, cur_registrant__is_admin=0)

        for sample in samples:
            igsn_handler = IGSNToDatacite(sample)
            response = igsn_handler.register_igsn()
            if response.status_code == 201:
                sample.metadata_store_status = "registered-datacite"
                sample.save()
                self.stdout.write("IGSN Registration Success: '{}'.".format(sample.igsn))
            else:
                self.stdout.write(response.json())
                self.stdout.write("IGSN Registration Failure: '{}'.".format(sample.igsn))


    def update_igsns(self):
        yesterday = timezone.now() - timedelta(days=1)
        samples = Sample.objects.filter(metadata_store_status='registered-datacite', archive_date__isnull=True, last_update_date__gt=yesterday)

        for sample in samples:
            igsn_handler = IGSNToDatacite(sample)
            response = igsn_handler.update_igsn()
            if response.status_code == 200:
                self.stdout.write("IGSN Metadata Update Success: '{}'.".format(sample.igsn))
            else:
                self.stdout.write(response.json())
                self.stdout.write("IGSN Metadata Update Failure: '{}'.".format(sample.igsn))

    def deactivate_igsns(self):
        samples = Sample.objects.filter(metadata_store_status='registered-datacite', archive_date__isnull=False)

        for sample in samples:
            igsn_handler = IGSNToDatacite(sample)
            response = igsn_handler.deactivate_igsn()
            if response.status_code == 200:
                sample.metadata_store_status = "deactivated-datacite"
                sample.save()
                self.stdout.write("IGSN Deactivation Success: '{}'.".format(sample.igsn))
            else:
                self.stdout.write(response.json())
                self.stdout.write("IGSN Deactivation Failure: '{}'.".format(sample.igsn))
    


    def handle(self, *args, **options):
        self.update_igsns()
        self.register_igsns()
        self.deactivate_igsns()
        sys.exit()        
