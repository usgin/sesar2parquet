# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.conf import settings
from django.db.models.functions import Now


# Extend Django User Model, add custom fields as neccessary
class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'

class SesarUser(models.Model):
    auth_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, blank=True, null=True)
    sesar_user_id = models.AutoField(primary_key=True)
    sso_account_id = models.IntegerField(blank=True, null=True)
    is_admin = models.IntegerField(default=0)
    fname = models.CharField(max_length=100, blank=True, null=True)
    lname = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state_province = models.CharField(max_length=255, blank=True, null=True)
    country = models.ForeignKey('Country', models.DO_NOTHING, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    institution_detail = models.CharField(max_length=255, blank=True, null=True)
    note = models.CharField(max_length=2000, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    upload_permission_status = models.IntegerField(blank=True, null=True, default=0)
    upload_permission_date = models.DateField(blank=True, null=True)
    registration_date = models.DateTimeField(blank=True, null=True, default=Now())
    deactivation_date = models.DateTimeField(blank=True, null=True)
    legacy_user_id = models.IntegerField(blank=True, null=True)
    geopass_id = models.CharField(unique=True, max_length=255, blank=True, null=True)
    orcid = models.CharField(unique=True, max_length=19, blank=True, null=True)
    doi_prefix = models.CharField(max_length=10, default='10.58052/')
    last_login = models.DateTimeField(blank=True, null=True, default=Now())
    class Meta:
        managed = True
        db_table = 'sesar_user'

    def __str__(self):
        return self.fname + ' ' + self.lname

class Organization(models.Model):
    owner = models.ForeignKey(SesarUser, models.DO_NOTHING)
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    create_date = models.DateTimeField(default=Now())
    deactivate_date = models.DateTimeField(blank=True, null=True)
    doi_prefix = models.CharField(max_length=16, default='10.58052/')
    members = models.ManyToManyField(SesarUser, related_name='organizations', through='OrganizationMember')

    class Meta:
        db_table = 'organization'


class OrganizationTeam(models.Model):
    organization = models.ForeignKey(Organization, models.DO_NOTHING)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    activate_date = models.DateTimeField(default=Now())
    deactivate_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'organization_team'

class OrganizationMember(models.Model):
    organization = models.ForeignKey(Organization, models.DO_NOTHING)
    sesar_user = models.ForeignKey(SesarUser, models.DO_NOTHING)
    is_admin = models.BooleanField(default=False)
    join_date = models.DateTimeField(default=Now())
    teams = models.ManyToManyField(OrganizationTeam, related_name='members', through='OrganizationTeamMember')

    class Meta:
        db_table = 'organization_member'

class OrganizationTeamMember(models.Model):
    member = models.ForeignKey(OrganizationMember, models.DO_NOTHING)
    team = models.ForeignKey(OrganizationTeam, models.DO_NOTHING)

    class Meta:
        db_table = 'organization_team_member'


class Classification(models.Model):
    classification_id = models.AutoField(primary_key=True)
    parent_classification = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=2000, blank=True, null=True)
    legacy_id = models.IntegerField(blank=True, null=True)
    legacy_parent_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'classification'


class Country(models.Model):
    country_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255, blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'country'


class LaunchType(models.Model):
    launch_type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=2000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'launch_type'


class NavType(models.Model):
    nav_type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=2000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'nav_type'


class SampleType(models.Model):
    sample_type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    parent_sample_type = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    legacy_id = models.IntegerField(blank=True, null=True)
    legacy_parent_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample_type'


class Sample(models.Model):
    sample_id = models.AutoField(primary_key=True)
    origin_sample = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    external_parent_sample_type = models.ForeignKey('SampleType', models.DO_NOTHING, blank=True, null=True)
    external_parent_name = models.CharField(max_length=1000, blank=True, null=True)
    sample_type = models.ForeignKey(SampleType, models.DO_NOTHING, related_name='sample_sample_type_set')
    cur_registrant = models.ForeignKey(SesarUser, models.DO_NOTHING)
    req_registrant = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='sample_req_registrant_set', blank=True, null=True)
    igsn = models.CharField(unique=True, max_length=64)
    igsn_prefix = models.ForeignKey('SesarUserCode', models.DO_NOTHING, db_column='igsn_prefix', to_field='user_code')
    igsn_digit = models.CharField(max_length=29, blank=True, null=True)
    igsn_to_int = models.BigIntegerField(unique=True, blank=True, null=True)
    igsn_is_system_assigned = models.IntegerField(blank=True, null=True)
    external_sample_id = models.CharField(max_length=100, blank=True, null=True)
    publish_date = models.DateTimeField(blank=True, null=True)
    archive_date = models.DateTimeField(blank=True, null=True)
    registration_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=255)
    current_archive = models.CharField(max_length=300, blank=True, null=True)
    current_archive_contact = models.CharField(max_length=1000, blank=True, null=True)
    original_archive = models.CharField(max_length=300, blank=True, null=True)
    original_archive_contact = models.CharField(max_length=1000, blank=True, null=True)
    collection_method = models.CharField(max_length=255, blank=True, null=True)
    collection_method_descr = models.CharField(max_length=1000, blank=True, null=True)
    size = models.CharField(max_length=255, blank=True, null=True)
    size_unit = models.CharField(max_length=255, blank=True, null=True)
    classification = models.ForeignKey(Classification, models.DO_NOTHING, blank=True, null=True)
    classification_comment = models.CharField(max_length=2000, blank=True, null=True)
    top_level_classification = models.ForeignKey(Classification, models.DO_NOTHING, related_name='sample_top_level_classification_set', blank=True, null=True)
    description = models.CharField(max_length=2000, blank=True, null=True)
    sample_comment = models.CharField(max_length=2000, blank=True, null=True)
    depth_min = models.FloatField(blank=True, null=True)
    depth_max = models.FloatField(blank=True, null=True)
    depth_scale = models.CharField(max_length=255, blank=True, null=True)
    age_min = models.FloatField(blank=True, null=True)
    age_max = models.FloatField(blank=True, null=True)
    age_unit = models.CharField(max_length=255, blank=True, null=True)
    geological_age = models.CharField(max_length=500, blank=True, null=True)
    geological_unit = models.CharField(max_length=500, blank=True, null=True)
    sample_unit = models.IntegerField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    latitude_end = models.FloatField(blank=True, null=True)
    longitude_end = models.FloatField(blank=True, null=True)
    elevation = models.FloatField(blank=True, null=True)
    elevation_end = models.FloatField(blank=True, null=True)
    elevation_unit = models.CharField(max_length=255, blank=True, null=True)
    primary_location_type = models.CharField(max_length=255, blank=True, null=True)
    primary_location_name = models.CharField(max_length=255, blank=True, null=True)
    location_description = models.CharField(max_length=2000, blank=True, null=True)
    locality = models.CharField(max_length=255, blank=True, null=True)
    locality_description = models.CharField(max_length=2000, blank=True, null=True)
    country = models.ForeignKey(Country, models.DO_NOTHING, blank=True, null=True)
    field_name = models.CharField(max_length=255, blank=True, null=True)
    province = models.CharField(max_length=255, blank=True, null=True)
    county = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    cruise_field_prgrm = models.CharField(max_length=255, blank=True, null=True)
    platform_type = models.CharField(max_length=255, blank=True, null=True)
    platform_name = models.CharField(max_length=2000, blank=True, null=True)
    platform_descr = models.CharField(max_length=2000, blank=True, null=True)
    collector = models.CharField(max_length=255, blank=True, null=True)
    collector_detail = models.CharField(max_length=2000, blank=True, null=True)
    collection_start_date = models.DateTimeField(blank=True, null=True)
    collection_end_date = models.DateTimeField(blank=True, null=True)
    collection_date_precision = models.CharField(max_length=200, blank=True, null=True)
    last_changed_by = models.ForeignKey(SesarUser, models.DO_NOTHING, db_column='last_changed_by', related_name='sample_last_changed_by_set', blank=True, null=True)
    last_registrant_id = models.IntegerField(blank=True, null=True)
    geom_latlong = models.TextField(blank=True, null=True)  #TODO: Change this to a geometry field type
    nav_type = models.ForeignKey(NavType, models.DO_NOTHING, blank=True, null=True)
    launch_platform_name = models.CharField(max_length=100, blank=True, null=True)
    launch_type = models.ForeignKey(LaunchType, models.DO_NOTHING, blank=True, null=True)
    launch_id = models.CharField(max_length=100, blank=True, null=True)
    purpose = models.CharField(max_length=100, blank=True, null=True)
    easting = models.CharField(max_length=128, blank=True, null=True)
    northing = models.CharField(max_length=128, blank=True, null=True)
    zone = models.CharField(max_length=128, blank=True, null=True)
    vertical_datum = models.CharField(max_length=128, blank=True, null=True)
    metadata_store_status = models.CharField(max_length=25, blank=True, null=True)
    orig_owner = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='sample_orig_owner_set', blank=True, null=True)
    cur_owner = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='owned_samples_set', blank=True, null=True)
    organization_owner = models.ForeignKey(Organization, models.DO_NOTHING, related_name='owned_samples_set', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'sample'


class SampleAdditionalName(models.Model):
    sample_additional_name_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample_additional_name'


class SampleDoc(models.Model):
    sample_doc_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=True, null=True)
    primary_image = models.IntegerField(blank=True, null=True)
    file_name = models.CharField(max_length=2048, blank=True, null=True)
    path_to_file = models.CharField(max_length=400, blank=True, null=True)
    uploaded_by = models.ForeignKey(SesarUser, models.DO_NOTHING, db_column='uploaded_by', blank=True, null=True)
    uploaded_date = models.DateTimeField(blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    file_type = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample_doc'


class SampleExternalIdentifier(models.Model):
    sample_external_identifier_id = models.IntegerField(primary_key=True)
    sample_id = models.IntegerField()
    sample_column_external_identifier_system_id = models.IntegerField()
    identifier_value = models.CharField(max_length=256)

    class Meta:
        managed = False
        db_table = 'sample_external_identifier'
        db_table_comment = 'link sample id to its exteranal identifier for certain columns'


class SamplePublicationUrl(models.Model):
    sample_publication_url_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=True, null=True)
    url = models.CharField(max_length=300, blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    url_type = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample_publication_url'
        unique_together = (('sample', 'url'),)


class Groups(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    group_owner = models.ForeignKey('SesarUser', models.DO_NOTHING, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    group_type = models.CharField(max_length=64, blank=True, null=True, db_comment="type of group such as 'award' or 'user defined'")
    is_private = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'groups'
        unique_together = (('name', 'group_owner'),)


class GroupSample(models.Model):
    group = models.ForeignKey('Groups', models.DO_NOTHING, blank=True, null=True)
    sample = models.ForeignKey('Sample', models.DO_NOTHING, blank=True, null=True)
    id = models.BigAutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'group_sample'
        unique_together = (('group', 'sample'),)



class SesarRole(models.Model):
    sesar_role_id = models.AutoField(primary_key=True)
    sesar_role_name = models.CharField(max_length=16)
    sesar_role_description = models.CharField(max_length=2000)

    class Meta:
        managed = False
        db_table = 'sesar_role'


class SesarUserCode(models.Model):
    sesar_user = models.ForeignKey(SesarUser, models.DO_NOTHING, blank=True, null=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    user_code = models.CharField(unique=True, max_length=5, blank=True, null=True)
    is_available = models.IntegerField(blank=True, null=True)
    igsn_count = models.BigIntegerField(blank=True, null=True)
    is_grandfather_code = models.BooleanField(blank=True, null=True)
    id = models.BigAutoField(primary_key=True)
    doi_prefix = models.CharField(max_length=16, default='10.58052/')

    class Meta:
        managed = True
        db_table = 'sesar_user_code'


class SamplePermission(models.Model):
    id = models.AutoField(primary_key=True)
    geopass_id = models.CharField(max_length=250, blank=True, null=True)
    user_code = models.ForeignKey(SesarUserCode, models.CASCADE, to_field='user_code', db_column='user_code', related_name='permissions', max_length=5, blank=True, null=True)
    sample = models.ForeignKey(Sample, models.CASCADE, related_name='permissions', blank=True, null=True)
    sesar_role = models.ForeignKey(SesarRole, models.DO_NOTHING, blank=True, null=True)
    activate_date = models.DateTimeField(blank=True, null=True)
    deactivate_date = models.DateTimeField(blank=True, null=True)
    orcid_id = models.CharField(max_length=19, blank=True, null=True)
    sesar_user = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='permissions', blank=True, null=True)
    organization = models.ForeignKey(Organization, models.CASCADE, related_name='permissions', blank=True, null=True)
    organization_team = models.ForeignKey(OrganizationTeam, models.CASCADE, related_name='permissions', blank=True, null=True)
    auth_group = models.ForeignKey(Group, on_delete=models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'sample_permission'
        unique_together = (('geopass_id', 'user_code'),)


class BatchHistory(models.Model):
    batch_history_id = models.AutoField(primary_key=True)
    batch_type = models.CharField(max_length=10)
    user_code = models.CharField(max_length=5)
    sample_count = models.IntegerField(blank=True, null=True)
    upload_time = models.DateTimeField()
    upload_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='upload_by')
    processed_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='processed_by', related_name='batchhistory_processed_by_set', blank=True, null=True)
    processed_time = models.DateTimeField(blank=True, null=True)
    filename = models.CharField(max_length=64, blank=True, null=True)
    deleted_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'batch_history'


class DownloadHistory(models.Model):
    download_history_id = models.AutoField(primary_key=True)
    filters = models.TextField()  # This field type is a guess.
    download_time = models.DateTimeField()
    download_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='download_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'download_history'


class SampleUploadHistory(models.Model):
    sample_upload_history_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=True, null=True)
    upload_from = models.CharField(max_length=256, blank=True, null=True)
    upload_time = models.DateTimeField(blank=True, null=True)
    upload_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='upload_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample_upload_history'


class AnnualStats(models.Model):
    year = models.IntegerField(primary_key=True)
    batches_processed = models.IntegerField(blank=True, null=True)
    new_users = models.IntegerField(blank=True, null=True)
    active_users = models.IntegerField(blank=True, null=True)
    download_count = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'annual_stats'


class SampleRegistrationStats(models.Model):
    time = models.DateField(unique=True)
    samples_registered = models.IntegerField(blank=True, null=True)
    samples_updated = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample_registration_stats'


class SampleDeleteRequest(models.Model):
    sample_id = models.IntegerField(blank=True, null=True)
    requestor_user_id = models.IntegerField(blank=True, null=True)
    delete_reason = models.CharField(max_length=200, blank=True, null=True)
    duplicate_igsns = models.CharField(max_length=1000, blank=True, null=True)
    other_reason = models.CharField(max_length=250, blank=True, null=True)
    deleted_by = models.IntegerField(blank=True, null=True)
    deleted_date = models.DateTimeField(blank=True, null=True)
    deactivated_by = models.IntegerField(blank=True, null=True)
    deactivated_date = models.DateTimeField(blank=True, null=True)
    id = models.BigAutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'sample_delete_request'


class ArchiveLkup(models.Model):
    name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'archive_lkup'


class ArchiveMapping(models.Model):
    archive_mapping_id = models.AutoField(primary_key=True)
    user_entered_archive_name = models.CharField(max_length=2000)
    preferred_archive_name = models.CharField(max_length=2000)

    class Meta:
        managed = False
        db_table = 'archive_mapping'


class CollectionMethodLkup(models.Model):
    name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'collection_method_lkup'


class CollectorLkup(models.Model):
    name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'collector_lkup'


class CruiseFieldPrgrmLkup(models.Model):
    name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cruise_field_prgrm_lkup'


class PlatformNameLkup(models.Model):
    name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'platform_name_lkup'


class PlatformTypeLkup(models.Model):
    name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'platform_type_lkup'


class PrimaryLocationNameLkup(models.Model):
    name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'primary_location_name_lkup'


class PrimaryLocationTypeLkup(models.Model):
    name = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'primary_location_type_lkup'


class RegistrarLkup(models.Model):
    registrar_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'registrar_lkup'


class SpatialRefSys(models.Model):
    srid = models.IntegerField(primary_key=True)
    auth_name = models.CharField(max_length=256, blank=True, null=True)
    auth_srid = models.IntegerField(blank=True, null=True)
    srtext = models.CharField(max_length=2048, blank=True, null=True)
    proj4text = models.CharField(max_length=2048, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'spatial_ref_sys'


class Layer(models.Model):
    topology = models.OneToOneField('Topology', models.DO_NOTHING, primary_key=True)  # The composite primary key (topology_id, layer_id) found, that is not supported. The first column is selected.
    layer_id = models.IntegerField()
    schema_name = models.CharField()
    table_name = models.CharField()
    feature_column = models.CharField()
    feature_type = models.IntegerField()
    level = models.IntegerField()
    child_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'layer'
        unique_together = (('topology', 'layer_id'), ('schema_name', 'table_name', 'feature_column'),)


class Topology(models.Model):
    name = models.CharField(unique=True)
    srid = models.IntegerField()
    precision = models.FloatField()
    hasz = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'topology'


# Unsure what these tables are for

class PengOrg(models.Model):
    sesar_name = models.CharField(max_length=250, blank=True, null=True)
    org_name = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'peng_org'


class GfzRegisteredNamespace(models.Model):
    gfz_prefix = models.CharField(max_length=25, blank=True, null=True)
    agen_name = models.CharField(max_length=25, blank=True, null=True)
    register_time = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GFZ_registered_namespace'


class CountryIdMap(models.Model):
    country_id_from_geopass = models.IntegerField(blank=True, null=True)
    country_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'country_id_map'


class EclOrcidTemp(models.Model):
    geopass_account_num = models.IntegerField(blank=True, null=True)
    orcid_id = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ecl_orcid_temp'


class GfzIgsnsNeedFix(models.Model):
    metadata_created_in_gfz = models.DateTimeField(blank=True, null=True)
    igsn = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gfz_igsns_need_fix'

class TempPp(models.Model):
    id = models.IntegerField(primary_key=True)
    fname = models.CharField(max_length=100, blank=True, null=True)
    lname = models.CharField(max_length=100, blank=True, null=True)
    pp = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temp_pp'


class VSqlStatement(models.Model):
    string_agg = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'v_sql_statement'
