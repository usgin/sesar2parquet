import sys
import time
from django.core.management.base import BaseCommand

from sesar_api.models import Sample
from sesar_api.classes import IGSNToDatacite


REGISTERED_STATUS = 'registered-datacite-v2'
PREVIOUS_REGISTERED_STATUS = 'registered-datacite'
MAX_RETRIES = 3
RETRY_DELAY = 5


class Command(BaseCommand):
    help = 'Updating Datacite Sample Metadata Mapping'

    def update_igsn_metadata_mapping(self):
        samples = (
            Sample.objects
            .filter(
                metadata_store_status=PREVIOUS_REGISTERED_STATUS,
                archive_date__isnull=True
            )
            .select_related(
                'cur_registrant',
                'sample_type',
                'origin_sample',
                'classification',
                'top_level_classification'
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

                    response = igsn_handler.update_igsn()
                    if response.status_code == 200:
                        sample.metadata_store_status = REGISTERED_STATUS
                        sample.save()
                        self.stdout.write(f"IGSN Metadata Update Success: '{sample.igsn}'.")
                        break  # success, exit retry loop
                    else:
                        self.stdout.write(str(response.json()))
                        self.stdout.write(f"IGSN Metadata Update Failure (attempt {attempt}): '{sample.igsn}'.")

                except Exception as e:
                    self.stdout.write(f"Exception on attempt {attempt} for '{sample.igsn}': {e}")

                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    self.stdout.write(f"Max retries reached for '{sample.igsn}'. Moving on.")


    def handle(self, *args, **options):
        self.update_igsn_metadata_mapping()
        sys.exit()        
