from django.db import migrations

# add special sequence for adding external_sample_id to the sample_additional_name table with conflicting ids
# found a gap in the existing ids large enough to all external_sample_ids with some headroom, begins at 407440
class Migration(migrations.Migration):

    dependencies = [
        ('sesar_api', '0008_remove_sample_individual_collector_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE SEQUENCE IF NOT EXISTS sample_additional_name_import_id_seq
            START WITH 407440
            INCREMENT BY 1
            NO MINVALUE
            NO MAXVALUE
            CACHE 1;
            """,
            reverse_sql="DROP SEQUENCE IF EXISTS sample_additional_name_import_id_seq;"
        )
    ]
