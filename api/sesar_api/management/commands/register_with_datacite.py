import sys
import time

from django.db.models import F
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from sesar_api.models import Sample
from sesar_api.classes import IGSNToDatacite

MAX_RETRIES = 3
RETRY_DELAY = 5
REGISTERED_STATUS = 'registered-datacite-v2'
PREVIOUS_REGISTERED_STATUS = 'registered-datacite'

class Command(BaseCommand):
    help = 'Datacite connection for registering/updating/deactivating IGSN IDs'

    def register_igsns(self):
        samples = (
            Sample.objects
            .filter(
                metadata_store_status__isnull=True,
                archive_date__isnull=True,
                cur_registrant__is_admin=0,
                publish_date__lt=timezone.now()
            )
            .select_related(
                'cur_registrant',
                'sample_type',
                'origin_sample',
                'classification',
                'top_level_classification',
                'country'
            )
            .prefetch_related(
                'publication_urls',
                'other_names'
            )
            .iterator(chunk_size=100)
        )

        for sample in samples:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    igsn_handler = IGSNToDatacite(sample)
                    response = igsn_handler.register_igsn()

                    if response.status_code == 201:
                        sample.metadata_store_status = REGISTERED_STATUS
                        sample.save()
                        self.stdout.write("IGSN Registration Success: '{}'.".format(sample.igsn))
                        break  # Success, stop retrying
                    else:
                        self.stdout.write(str(response.json()))
                        self.stdout.write("IGSN Registration Failure (attempt {}): '{}'.".format(attempt, sample.igsn))

                except Exception as e:
                    self.stdout.write("Exception on attempt {} for '{}': {}".format(attempt, sample.igsn, e))

                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    self.stdout.write("Max retries reached for '{}'. Moving on.".format(sample.igsn))


    def update_igsns(self):
        yesterday = timezone.now() - timedelta(days=1)
        samples = (
            Sample.objects
            .filter(
                metadata_store_status=REGISTERED_STATUS, 
                archive_date__isnull=True, 
                last_update_date__gt=yesterday
            )
            .select_related(
                'cur_registrant',
                'sample_type',
                'origin_sample',
                'classification',
                'top_level_classification',
                'country'
            )
            .prefetch_related(
                'publication_urls',
                'other_names'
            )
            .iterator(chunk_size=100)
        )

        for sample in samples:
            igsn_handler = IGSNToDatacite(sample)
            response = igsn_handler.update_igsn()
            if response.status_code == 200:
                self.stdout.write("IGSN Metadata Update Success: '{}'.".format(sample.igsn))
            else:
                self.stdout.write(response.json())
                self.stdout.write("IGSN Metadata Update Failure: '{}'.".format(sample.igsn))

    def deactivate_igsns(self):
        samples = (
            Sample.objects
            .filter(
                metadata_store_status=REGISTERED_STATUS,
                archive_date__isnull=False
            )
            .iterator(chunk_size=100)
        )

        for sample in samples:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    igsn_handler = IGSNToDatacite(sample)
                    response = igsn_handler.deactivate_igsn()

                    if response.status_code == 200:
                        sample.metadata_store_status = "deactivated-datacite"
                        sample.save()
                        self.stdout.write("IGSN Deactivation Success: '{}'.".format(sample.igsn))
                        break  # exit retry loop on success
                    else:
                        self.stdout.write(str(response.json()))
                        self.stdout.write("IGSN Deactivation Failure (attempt {}): '{}'.".format(attempt, sample.igsn))

                except Exception as e:
                    self.stdout.write("Exception on attempt {} for '{}': {}".format(attempt, sample.igsn, e))

                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    self.stdout.write("Max retries reached for '{}'. Moving on.".format(sample.igsn))


    def handle(self, *args, **options):
        self.update_igsns()
        self.register_igsns()
        self.deactivate_igsns()
        sys.exit()        
