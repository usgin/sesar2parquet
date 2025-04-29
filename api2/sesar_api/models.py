from django.db import models
from django.contrib.auth.models import AbstractUser, Group as AuthGroup
from django.conf import settings
from django.utils import timezone
from django.db.models import Index, Q
import os


# Extend Django User Model, add custom fields as neccessary
class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'


class SesarUser(models.Model):
    sesar_user_id = models.AutoField(primary_key=True,
                                     db_comment='sesar_user_id is same as individual_id except where an individual'
                                                'has more than one user id or the SESAR user is a group.'
                                                ' SESAR user might also be a group')
    individual = models.ForeignKey('Individual', models.DO_NOTHING, blank=True, null=True,
                                   db_comment='a sesar user must map to either an individual or a group')
    institution = models.ForeignKey('Institution', models.DO_NOTHING, blank=True, null=True,
                                    db_comment='a sesar user should be affiliated with some institution')
    email = models.CharField(max_length=255, blank=True, null=True,
                             db_comment='email specific to individual or group in context of this user account')
    sso_account_id = models.IntegerField(blank=True, null=True)
    is_admin = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    upload_permission_status = models.IntegerField(blank=True, null=True, default=0)
    upload_permission_date = models.DateField(blank=True, null=True)
    registration_date = models.DateTimeField(default=timezone.now)
    deactivation_date = models.DateTimeField(blank=True, null=True)
    legacy_user_id = models.IntegerField(blank=True, null=True)
    geopass_id = models.CharField(max_length=255, blank=True, null=True)
    orcid = models.CharField(unique=True, max_length=19, blank=True, null=True)
    doi_prefix = models.CharField(max_length=10, default=os.environ.get('SESAR_SHARED_PREFIX', '10.58052/'))
    last_login = models.DateTimeField(blank=True, null=True, default=timezone.now)
    auth_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        if self.individual:
            output = f"{self.individual.fname or ''} {self.individual.lname or ''}".strip()
        
        if self.orcid:
            output += f" ({self.orcid})"
        
        return output

    class Meta:
        db_table = 'sesar_user'


class Team(models.Model):
    owner = models.ForeignKey(SesarUser, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=64)
    display_name = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(max_length=255)
    activate_date = models.DateTimeField(default=timezone.now)
    deactivate_date = models.DateTimeField(blank=True, null=True)
    doi_prefix = models.CharField(max_length=16, default=os.environ.get('SESAR_SHARED_PREFIX', '10.58052/'))
    members = models.ManyToManyField(SesarUser, related_name='teams', through='TeamMember')
    part_of_team = models.ForeignKey("self", models.CASCADE, null=True, blank=True, related_name='subteams')

    class Meta:
        db_table = 'team'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'part_of_team'],
                name='unique_name_team',
                condition=Q(part_of_team__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['name'],
                name='unique_name_when_no_team',
                condition=Q(part_of_team__isnull=True)
            )
        ]

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    team = models.ForeignKey(Team, models.CASCADE, related_name='teams')
    sesar_user = models.ForeignKey(SesarUser, models.DO_NOTHING)
    join_date = models.DateTimeField(default=timezone.now)
    auth_group = models.ForeignKey(AuthGroup, on_delete=models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        db_table = 'team_member'
        unique_together = ('team', 'sesar_user')


class CollectionType(models.Model):
    collection_type_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'collection_type'


class Country(models.Model):
    country_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=255, blank=False, null=False)
    iso3166code = models.CharField(max_length=3, blank=True, null=True)
    is_active = models.IntegerField(blank=False, null=False)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'country'


class GeologicTimeScale(models.Model):
    geologic_time_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    geologic_time_interval_uri = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)
    numeric_older_bound = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True)
    numeric_younger_bound = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True)
    notation = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'geologic_time_scale'
        db_table_comment = 'vocabulary of ICS geologic time ordinal eras, 2024 version'




class InitiativeType(models.Model):
    initiative_type_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'initiative_type'


class Initiative(models.Model):
    initiative_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    funding = models.CharField(max_length=50, blank=True, null=True)
    begin_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    initiative_uri = models.CharField(max_length=255, blank=True, null=True)
    initiative_type = models.ForeignKey(InitiativeType, models.DO_NOTHING, blank=False, null=False)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'initiative'
        db_table_comment = 'Definition of an activity related to sample collection or stewardship. includes cruises, field programs, funded projects, '


class LaunchType(models.Model):
    launch_type_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'launch_type'


class Locality(models.Model):
    locality_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=120, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    feature_type = models.ForeignKey('SampledFeatureType', models.DO_NOTHING, blank=True, null=True)
    locality_uri = models.CharField(max_length=512, blank=True, null=True) # use mindat location identifiers?
    country = models.ForeignKey(Country, models.DO_NOTHING, blank=True, null=True)
    province = models.CharField(max_length=255, blank=True, null=True)
    county = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    permit = models.CharField(max_length=255, blank=True, null=True)
    collection_policy = models.CharField(max_length=1000, blank=True, null=True)
    contained_in = models.ForeignKey('self', models.DO_NOTHING, db_column='contained_in', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'locality'
        db_table_comment = 'definition of a named place associated with some geologic feature of interest. Binding to concrete geospatial coordinate location is assumed to be through information linked at locality_uri.'


class LocationMethod(models.Model):
    location_method_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'location_method'
        db_table_comment = 'was nav_type'


class MaterialType(models.Model):
    material_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    material_type_uri = models.CharField(max_length=255, blank=True, null=True)
    parent_material_type = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'material_type'
        db_table_comment = 'was classification'


class PlatformType(models.Model):
    platform_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'platform_type'


class PropertyType(models.Model):
    property_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    property_uri = models.CharField(max_length=255, blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'property_type'
        db_table_comment = 'vocabulary of properties that might have values assigned for a material sample'



class AffiliationType(models.Model):
    affiliation_type_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    def __str__(self):
        return (self.label)

    class Meta:
        db_table = 'affiliation_type'


class InstitutionType(models.Model):
    institution_type_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'institution_type'


class Institution(models.Model):
    institution_id = models.AutoField(primary_key=True)
    institution_type = models.ForeignKey(InstitutionType, models.DO_NOTHING)
    label = models.CharField(max_length=200, blank=True, null=True)
    alt_label = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    activate_date = models.DateField(auto_now_add=True)
    deactivate_date = models.DateField(auto_now_add=False, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True,
                             db_comment='email specific to this affiliation; this is the point of contact for the institution')
    address = models.CharField(max_length=500, blank=True, null=True,
                               db_comment='location address specific to this affiliation')

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'institution'


class ParentInstitution(models.Model):
    relation_id = models.AutoField(primary_key=True)
    institution = models.ForeignKey(Institution, models.DO_NOTHING)
    parent = models.ForeignKey(Institution, models.DO_NOTHING, related_name='parent_institution_id')
    label = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    relation_type = models.ForeignKey(AffiliationType, models.DO_NOTHING)
    activate_date = models.DateField(auto_now_add=True)
    deactivate_date = models.DateField(auto_now_add=False, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'parent_institution'


class Platform(models.Model):
    platform_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    platform_type = models.ForeignKey('PlatformType', models.DO_NOTHING, blank=True, null=True)
    host_platform_id = models.IntegerField(blank=True, null=True)
    launch_type = models.ForeignKey(LaunchType, models.DO_NOTHING, blank=True, null=True)
    operator = models.ForeignKey(Institution, models.DO_NOTHING, blank=True, null=True)
    date_commissioned = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'platform'
        db_table_comment = 'Definition of a facility that hosts sampling activities. Typically a ship or ship-based device (e.g. alvin) used to explore marine water bodies in accessible to direct human occupation.  Extent to include extraterrestrial  exploration devices like OSIRIS-REx. '



class Individual(models.Model):
    individual_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=200, blank=True, null=True)
    fname = models.CharField(max_length=100, blank=True, null=True)
    lname = models.CharField(max_length=100, blank=True, null=True)
    alt_label = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    affiliation = models.ManyToManyField(Institution, related_name='affiliations', through='Affiliation')
    # many URIs are null, need way to enforce constraint that if and only if there is a URI, it is unique in this table
    individual_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    @property
    def affiliations_list(self):
        return [a.institution for a in self.affiliation_set.all()]

    class Meta:
        db_table = 'individual'


class Affiliation(models.Model):
    affiliation_id = models.AutoField(primary_key=True)
    individual = models.ForeignKey(Individual, models.DO_NOTHING, related_name='affiliations')
    institution = models.ForeignKey(Institution, models.DO_NOTHING)
    label = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    relation_type = models.ForeignKey(AffiliationType, models.DO_NOTHING)
    activate_date = models.DateField(auto_now_add=True)
    deactivate_date = models.DateField(auto_now_add=False, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True,
                             db_comment='email specific to this affiliation')
    address = models.CharField(max_length=500, blank=True, null=True,
                               db_comment='location address specific to this affiliation')

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'affiliation'


class SesarSpatialRefSys(models.Model):
    spatial_ref_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=254, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    identifier = models.CharField(max_length=254, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sesar_spatial_ref_sys'


class SampleType(models.Model):
    sample_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    sample_type_uri = models.CharField(max_length=255, blank=True, null=True)
    parent_sample_type = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    scheme_name = models.CharField(max_length=50, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'sample_type'


class SampledFeatureType(models.Model):
    feature_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    feature_type_uri = models.CharField(max_length=255, blank=True, null=True)
    parent_feature_type = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'sampled_feature_type'


class SamplingMethod(models.Model):
    collection_method_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    method_uri = models.CharField(max_length=255, blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'sampling_method'


class Sample(models.Model):
    sample_id = models.AutoField(primary_key=True, db_comment='primary key for database. ')
    igsn = models.CharField(max_length=60, blank=False, null=False,
                            db_comment='globally unique identifier string that identifies the material sample. In '
                                       'DataCite/DOI context, this includes the DOI prefix, and the identifier suffix (which in most cases begins with a SESAR code.')
    sesar_code = models.ForeignKey('SesarCode', models.DO_NOTHING, db_column='sesar_code', to_field='sesar_code', related_name='samples', blank=True, null=True)
    name = models.CharField(max_length=255, blank=False, null=False,
                            db_comment='name used to represent the sample in user interface; might be IGSN, '
                                       'or a user-defined label for the sample.')
    parent_sample = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True,
                                      db_comment='This is the sample.sample_id for the parent sample; to get its IGSN '
                                                 'would have to do a sample-sample join on origin_sample_id = '
                                                 'sample_id')
    sample_type = models.ForeignKey(SampleType, models.DO_NOTHING, blank=False, null=False,
                                    db_comment='corresponds to iSamples material sample type, use iSamples vocabulary '
                                               'with earth science extensions.')
    # related agent
    # org_registrant = models.ManyToManyField(Institution, related_name='org_registrant_agent_id',
    #                                         through='RelatedSampleAgent')
    cur_registrant = models.ForeignKey(SesarUser, models.DO_NOTHING, blank=False, null=False,
                                       related_name='sample_cur_registrant_set')
    cur_owner = models.ForeignKey(SesarUser, models.DO_NOTHING, blank=True, null=True,
                                  related_name='sample_cur_owner_set')
    # related agent
    # req_registrant = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='sample_req_registrant_set',
    #                                   blank=True,
    #                                   null=True)
    igsn_is_system_assigned = models.IntegerField(blank=True, null=True)
    publish_date = models.DateTimeField(default=timezone.now)
    archive_date = models.DateTimeField(blank=True, null=True)
    registration_date = models.DateTimeField(default=timezone.now)
    last_update_date = models.DateTimeField(default=timezone.now)
    # current_archive = models.ManyToManyField(Institution, related_name='curr_archive_agent_id', through='RelatedSampleAgent',
    #                                          db_comment='link to agent that currently is the steward of the sample.')
    # original_archive = models.ManyToManyField(Group, related_name='orig_archive_agent_id', through='RelatedSampleAgent',
    #                                           db_comment='link to first agent that was the steward of the sample, '
    #                                                      'if different from the current steward.')
    size = models.CharField(max_length=255, blank=True, null=True,
                            db_comment='text string  specifying size of sample; should be measured value with units '
                                       'of measure. MIght use mass or length dimensions. ')
    general_material_type = models.ForeignKey(MaterialType, models.DO_NOTHING, blank=True, null=True,
                                              db_comment='material type from iSamples material type vocabulary. '
                                                         'Multiple more specific material types are specified through '
                                                         'the sample_material correlation table.  ')
    material_name_verbatim = models.CharField(max_length=255, blank=True, null=True,
                                              db_comment='material name as provided by the original sample collector '
                                                         'or sample registrant.')
    sample_material = models.ManyToManyField(MaterialType, through='SampleMaterial', related_name='related_material_id')
    sample_description = models.TextField(blank=True, null=True,
                                          db_comment='Description of the sample; provide details-- material type, '
                                                     'textures, dimensions, why collected, how collected, information '
                                                     'about the sample context, etc. ')
    purpose = models.CharField(max_length=100, blank=True, null=True,
                               db_comment='brief explanation of why sample was collected.')
    geologic_age_verbatim = models.CharField(max_length=500, blank=True, null=True,
                                             db_comment='geologic age of the sample as reported by the original collector or registrant. ')
    numeric_age_min = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True,
                                          db_comment='Younger numeric temporal coordinate for age of sample; if only have a single age, provide it here and leave age_max null. \n\nunits are specified in numeric_age_unit field.  If a temporal reference system other than standard geologic time frame (yr, ky, my, measured positive back from 1950 CE), describe the reference system in the sample descriptions. ')
    numeric_age_max = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True,
                                          db_comment='Older numeric temporal coordinate for age range of sample; if only have a single age, provide leave age_max null. \n\nunits are specified in numeric_age_unit field.  If a temporal reference system other than standard geologic time frame (yr, ky, my, measured positive back from 1950 CE), describe the reference system in the sample descriptions. ')
    numeric_age_unit = models.CharField(max_length=32, blank=True, null=True,
                                        db_comment='units are specified in numeric_age_unit field.  If a temporal reference system other than standard geologic time frame (yr, ky, my, measured positive back from 1950 CE), describe the reference system in the sample descriptions. ')
    geologic_age_younger = models.ForeignKey(GeologicTimeScale, models.DO_NOTHING, blank=True, null=True,
                                             db_comment='Link to geologic time interval definition for younger age possible for sample. If only have a single interval, provide that here and leave age_olde_id null. ')
    geologic_age_older = models.ForeignKey(GeologicTimeScale, models.DO_NOTHING,
                                           related_name='sample_geologic_age_older_set', blank=True, null=True,
                                           db_comment='Link to geologic time interval definition for older age possible for sample. If only have a single interval, leave this field null. ')
    geologic_unit = models.CharField(max_length=500, blank=True, null=True,
                                     db_comment='name of the geologic unit that contains the sample.')
    age_qualifier = models.CharField(max_length=50, blank=True, null=True,
                                     db_comment='qualifier to indicate if age assignment is exact, if there are know uncertainty bounds on numeric age, if age is questionable, etc.')
    latitude = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True,
                                   db_comment='latitude of point location where sample was collected, reported in decimal degrees using WGS84 Spatial reference system. Location coordinates will be rounded to 6 decimal places.  If the sampling location position is specified with other spatial reference system, link through the location table.')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True,
                                    db_comment='longitude of point location where sample was collected, reported in '
                                               'decimal degrees using WGS84 Spatial reference system.  Location '
                                               'coordinates will be rounded to 6 decimal places.   If the sampling '
                                               'location position is specified with other spatial reference system, '
                                               'link through the location table.')
    latitude_end = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True,
                                       db_comment='If the sampling location is a linear feature (e.g. the track of a'
                                                  ' dredge haul), report the latitude of the end of the feature, using '
                                                  'WGS84 decimal degrees.')
    longitude_end = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True,
                                        db_comment='If the sampling location is a linear feature (e.g. the track of'
                                                   ' a dredge haul), report the longitude of the end of the feature, '
                                                   'using WGS84 decimal degrees.')
    geom_latlong = models.TextField(blank=True, null=True)  #TODO: Change this to a geometry field type
    depth_min = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True,
                                    db_comment='minimum vertical coordinate below a reference datum,'
                                               'measured positive increasing away from the datum point')
    depth_max = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True,
                                    db_comment='maximum vertical coordinate below some reference datum,'
                                               'measured positive increasing away from the datum point')
    depth_uom = models.CharField(max_length=50, blank=True, null=True,
                                 db_comment='units of measure for depth measurements, {meter, foot, '
                                            'centimeter}')
    depth_spatial_ref = models.ForeignKey(SesarSpatialRefSys, models.DO_NOTHING, blank=True, null=True,
                                          db_comment='link to description of depth spatial reference system, including'
                                                     'datum, linear reference geometry (if applicable), units of measure,'
                                                     'and positive increasing direction')
    elevation = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True,
                                    db_comment='vertical datum is not specified in the legacy data, '
                                               'assume is mean sea level. If depths are reported different'
                                               'than the elevation, assume it is the elevation at the borehole'
                                               'origin, otherwise assume it is elevation at the sample location.')
    elevation_uom = models.CharField(max_length=50, blank=True, null=True,
                                     db_comment='units of measure for depth measurements, {meter, foot, '
                                                'centimeter}')
    location_method = models.ForeignKey(LocationMethod, models.DO_NOTHING, blank=True, null=True,
                                        db_comment='link to description of how the location coordinates have been determined')
    location_qualifier = models.CharField(max_length=128, blank=True, null=True,
                                          db_comment='indicate uncertainty, whether locations have be obfuscated intentionally, and '
                                                     'notes about elevation datums')
    sampled_feature_type = models.ForeignKey(SampledFeatureType, models.DO_NOTHING, blank=True, null=True,
                                             db_comment='was primary_location_type. Map to iSamples Sampled feature; this will likely be some geoscience feature. Link to controlled vocabulary.')
    locality = models.ForeignKey(Locality, models.DO_NOTHING, blank=True, null=True,
                                 db_comment='link to place name description of sampling location, as opposed to a '
                                            'coordinate position. The locality table is incompeletly populated because'
                                            'of the challenges correlating the various place names and granularity of place'
                                            'names. '
                                )
    locality_label = models.TextField(blank=True, null=True,
                                       db_comment='labels to identify a place, geographic, cultural, physiographic, geologic.'
                                                  'include city, county, province, country if applicable and available. ')
    locality_detail = models.TextField(blank=True, null=True,
                                       db_comment='linked locality entity has generalized information about the kind '
                                                  'of locality; include details specific to this sampling location '
                                                  'here. for legacy SESAR data this is concatenation of values from all'
                                                  'location and locality fields.')
    collection_method = models.ForeignKey(SamplingMethod, models.DO_NOTHING, blank=True, null=True,
                                          db_comment='link to generic description of the collection method')
    collection_method_detail = models.CharField(max_length=1000, blank=True, null=True,
                                                db_comment='text content includes details about specifics of the '
                                                           'particular collection event for this sample')
    cruise_field_prgrm = models.ForeignKey(Initiative, models.DO_NOTHING, blank=True, null=True,
                                           db_comment='link to description of the cruise, field program, funded '
                                                      'project or other activity that is the context for the '
                                                      'collection of this sample')
    individual_collector = models.ManyToManyField(Individual, related_name='collected_samples',
                                                  through='RelatedSampleAgent',
                                                  through_fields=('sample', 'individual'))
    institution_collector = models.ManyToManyField(Institution, related_name='collected_samples',
                                                  through='RelatedSampleAgent',
                                                  through_fields=('sample', 'institution'))
    platform = models.ForeignKey(Platform, models.DO_NOTHING, blank=True, null=True,
                                 db_comment='Facility that hosted the sampling event. Example of indirect host is '
                                            'remote vehicle from a ship.')
    launch_platform = models.ForeignKey(Platform, models.DO_NOTHING, related_name='samples',
                                        blank=True, null=True,
                                        db_comment='If sampling was hosted indirectly from the facility identified, '
                                                   'by platform_id, this identifies the proximate sampling device or '
                                                   'facility hosted by the platform_id.')
    launch_label = models.CharField(max_length=100, blank=True, null=True,
                                    db_comment='label or identifier for a specify sampling platform deployment from a '
                                               'host platform, e.g launch of Alvin submersible from support ship.')
    collection_start_date = models.DateTimeField(blank=True, null=True,
                                                 db_comment='date and time of sample acquisition; if the acquisition '
                                                            'event is only specfied as a time interval, this is the '
                                                            'start of that interval. ')
    collection_end_date = models.DateTimeField(blank=True, null=True,
                                               db_comment='If sample acquisition event is specified as a date-time '
                                                          'interval, this is the end of that interval. ')
    collection_date_precision = models.CharField(max_length=200, blank=True, null=True,
                                                 db_comment='indicate time interval that collection time is '
                                                            'specified; e.g. minutes, hours, days, weeks, months...')
    metadata_store_status = models.CharField(max_length=25, blank=True, null=True,
                                             db_comment='internal status flag used by SESAR to track metadata '
                                                        'management')
    # orig_owner = models.ManyToManyField(Individual, related_name='orig_owner_agent_id', through='RelatedSampleAgent',
    #                                     db_comment='link to agent who was original owner of sample, if different from '
    #                                                'the current owner.')
    # cur_owner = models.ManyToManyField(Individual, related_name='sample_cur_owner_set', through='RelatedSampleAgent',
    #                                    db_comment='link to current owner of the sample. SESAR uses the owner ID to '
    #                                               'determine permissions for updating sample records.')
    last_changed_by = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='sample_last_changed_by_set',
                                        blank=True,
                                        null=True,
                                        db_comment='link to user who most recently changed the content of this record.')
    team_owner = models.ForeignKey(Team, models.DO_NOTHING, related_name='owned_samples_set', blank=True, null=True)

    def __str__(self):
        return self.igsn

    class Meta:
        db_table = 'sample'
        db_table_comment = ('base table with core sample description fields. The contents of this table are a digital '
                            'representation of a physical, material sample.')


class SampleAdditionalName(models.Model):
    sample_additional_name_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False, related_name='other_names')
    name = models.CharField(max_length=255, blank=False, null=False)
    name_authority = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sample_additional_name'
        db_table_comment = 'simple table to link one sample to potentially many different other names by which it is known'


class MaterialRoleType(models.Model):
    material_role_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    material_role_uri = models.CharField(max_length=255, blank=True, null=True)
    scheme_name = models.CharField(max_length=50, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'material_role_type'


class SampleMaterial(models.Model):
    sample_material_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False)
    material_type = models.ForeignKey(MaterialType, models.DO_NOTHING, blank=True, null=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    material_role = models.ForeignKey(MaterialRoleType, models.DO_NOTHING, blank=True, null=True)
    source = models.TextField(blank=True, null=True,
                              db_comment='explanation of how material was assigned, used to flag material associations '
                                         'added by curators, text analytics, AI etc.')

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'sample_material'
        db_table_comment = 'Correlation table to implement many to many relationship between samples and material constituents of the sample.'


class SampleCollection(models.Model):
    collection_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    collection_owner = models.ForeignKey('SesarUser', models.DO_NOTHING,
                                         db_column='collection_owner', blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    collection_type = models.ForeignKey(CollectionType, models.DO_NOTHING, blank=True, null=True,
                                        db_comment="type of collection")
    is_private = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'sample_collection'
        db_table_comment = 'Definition of set of samples by some user to associate a set of samples for some purpose.'


class CollectionMember(models.Model):
    collection = models.ForeignKey(SampleCollection, models.DO_NOTHING, blank=False, null=False, default=-1)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False, default=-1)

    def __str__(self):
        return self.collection

    class Meta:
        db_table = 'collection_member'
        db_table_comment = 'correlation table that associated a sample with a collection. '


class AgentRoleType(models.Model):
    agent_role_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'agent_role_type'


class RelatedSampleAgent(models.Model):
    class AGENT_TYPES(models.TextChoices):
       Individual = 'INDIVIDUAL'
       Team = 'TEAM'
       Institution = 'INSTITUTION'

    sample = models.ForeignKey(Sample, models.DO_NOTHING, related_name='samples')
    related_agent_id = models.IntegerField(models.DO_NOTHING)  # this is FK to one of Individual, Team or Institution
    # depending on value of agent_type
    agent_type = models.CharField(max_length=50, blank=False, choices=AGENT_TYPES)
    relation_type = models.ForeignKey(AgentRoleType, models.DO_NOTHING)
    label = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    activate_date = models.DateField(auto_now_add=True)
    deactivate_date = models.DateField(auto_now_add=False, blank=True, null=True)
    individual = models.ForeignKey(Individual, models.DO_NOTHING, blank=True, null=True)
    team = models.ForeignKey(Team, models.DO_NOTHING, blank=True, null=True)
    institution = models.ForeignKey(Institution, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'related_sample_agent'




class RelationType(models.Model):
    relation_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    # need relation type URI
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return (self.label)

    class Meta:
        db_table = 'relation_type'
        db_table_comment = ('terms to assign semantics for relations between samples. Relations can detail the '
                            'relationship between parent and child samples, use to link to publications, data, '
                            'other online resources, relate to other samples.')


class ResourceType(models.Model):
    resource_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    resource_type_uri = models.CharField(max_length=255, blank=True, null=True)
    broader_type = models.ForeignKey('ResourceType', models.DO_NOTHING,
                                     default='-9999', blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return (self.label)

    class Meta:
        db_table = 'resource_type'
        db_table_comment = ('kinds of things a sample can be related to, e.g. publication, dataset, sample, research '
                            'project')


class RelatedResource(models.Model):
    relation_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False, default=-1)
    relation_type = models.ForeignKey(RelationType, models.DO_NOTHING, blank=False, null=False)
    relation_label = models.CharField(max_length=100, blank=False, null=False)
    related_resource_uri = models.CharField(max_length=255, blank=False, null=False)
    related_sesar_sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=True, null=True,
                                             related_name='relatedsesarsample')
    related_resource_type = models.ForeignKey(ResourceType, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return (self.relation_label)

    class Meta:
        db_table = 'related_resource'
        db_table_comment = "table to provide links to web-accessible related resource via their URIs. Can be used to provide more explicit relation between a subsample and its parent that simply 'parent', e.g. mineral_separate, soluble_fraction..."


class SamplePublicationUrl(models.Model):
    sample_publication_url_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False, related_name='publication_urls',
                               db_comment='link to sample described by this URL content.')
    url = models.CharField(max_length=254, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    url_type = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.url

    class Meta:
        db_table = 'sample_publication_url'


class GeospatialLocation(models.Model):
    location_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False,
                             db_comment='text to display this location position in user interface. ')
    description = models.TextField(blank=True, null=True,
                                   db_comment='information about the position determination and representation.')
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False,
                               db_comment='link to sample that this position applies to. ')
    vertical = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True,
                                   db_comment='based on vertical_srs, might be elevation (positive up) or depth (positive down).')
    vertical_srs = models.ForeignKey(SesarSpatialRefSys, models.DO_NOTHING, db_column='vertical_srs', blank=True,
                                     null=True,
                                     db_comment='defines units of measure for vertical coordinate, positive up or positive down, and the datum-- that is the surface that has a 0 coordinate value.   If the position is within a borehole, the vertical_srs might be the borehole geometry. ')
    coordinate_1 = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True,
                                       db_comment='coordinate order (what is coordinate_1, coordinate_2) and interpretation must be specified in the spatial_reference_system definition. ')
    coordinate_2 = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True,
                                       db_comment='coordinate order (what is coordinate_1, coordinate_2) and interpretation must be specified in the spatial_reference_system definition. ')
    spatial_reference_system = models.CharField(db_column='spatial_reference_system', max_length=100, blank=True,
                                                null=True)
    wkt_geometry = models.CharField(db_column='WKT_geometry', max_length=100, blank=True,
                                    null=True)  # Field name made lowercase.
    global_grid_cell_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'geospatial_location'
        db_table_comment = 'The latitude and longitude in the sample table are required to use WGS84 decimal degrees. This table is optional, use to report coordinate locations with spatial reference different from WGS84, e.g. UTM, local grid coordinates, global grid cell identifiers, etc. '


class SampleDoc(models.Model):
    # note order of fields in db modified in migration 0035 to match what is in
    # legacy database so table copy function works
    sample_doc_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=True, null=True, related_name='sample_docs', db_comment='link to sample described by this URL content.')
    primary_image = models.IntegerField(blank=False, null=False, default=0)
    file_name = models.CharField(max_length=2048, blank=False, null=False)
    path_to_file = models.CharField(max_length=400, blank=False, null=False)
    uploaded_by = models.ForeignKey(SesarUser, models.DO_NOTHING,
                                    db_column='uploaded_by', blank=True, null=True)
    uploaded_date = models.DateTimeField(blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    file_type = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.file_name

    class Meta:
        db_table = 'sample_doc'


class RelatedLocalDoc(models.Model):
    local_doc_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False, default=-1)
    primary_image = models.IntegerField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    path_to_file = models.CharField(max_length=400, blank=True, null=True)
    uploaded_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='uploaded_by', blank=False, null=False)
    uploaded_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.file_name

    class Meta:
        db_table = 'related_local_doc'
        db_table_comment = 'Table to provide links from sample to document hosted in the file system local to the SESAR server'


class OtherProperty(models.Model):
    property_value_id = models.IntegerField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False,
                             db_comment='text to display property value in user interface')
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False, default=-1,
                               db_comment='foreign key to sample table to link property attribution to sample')
    property_type = models.ForeignKey('PropertyType', models.DO_NOTHING, blank=False, null=False,
                                      db_comment='foreign key to property type vocabulary')
    property_value_text = models.CharField(max_length=256, blank=False, null=False,
                                           db_comment='property value, serialized as text. the value_data_type is used ' \
                                                      ' to convert to number or treat as URI if appropriated')
    value_data_type = models.CharField(max_length=50, blank=False, null=False,
                                       db_comment='data type for property value, if need to cast text as numeric or a URI.')
    provenance = models.CharField(max_length=250, blank=True, null=True,
                                  db_comment='explanation of how (when, who...) the value was determined')

    def __str__(self):
        return self.label

    class Meta:
        db_table = 'other_property'
        db_table_comment = 'Optional correlation table to link sample with descriptive properties not explicitly included in this schema. Was sample_customized_metadata'


class SesarCode(models.Model):
    sesar_user = models.ForeignKey(SesarUser, models.DO_NOTHING, blank=True, null=True, related_name='sesar_codes')
    team = models.ForeignKey(Team, models.DO_NOTHING, blank=True, null=True, related_name='sesar_codes')
    sesar_code = models.CharField(unique=True, max_length=5)
    is_available = models.IntegerField(blank=True, null=True, default=1)
    igsn_count = models.BigIntegerField(blank=True, null=True, default=0)
    is_grandfather_code = models.BooleanField(blank=True, null=True, default=False)
    id = models.BigAutoField(primary_key=True)
    doi_prefix = models.CharField(max_length=16, default=os.environ.get('SESAR_SHARED_PREFIX', '10.58052/'))

    class Meta:
        db_table = 'sesar_code'


class Permission(models.Model):
    id = models.AutoField(primary_key=True)
    geopass_id = models.CharField(max_length=250, blank=True, null=True)
    sesar_code = models.ForeignKey(SesarCode, models.CASCADE, to_field='sesar_code', db_column='sesar_code', related_name='permissions', max_length=5, blank=True, null=True)
    sample = models.ForeignKey(Sample, models.CASCADE, related_name='permissions', blank=True, null=True)
    activate_date = models.DateTimeField(blank=True, null=True, default=timezone.now)
    deactivate_date = models.DateTimeField(blank=True, null=True)
    orcid_id = models.CharField(max_length=19, blank=True, null=True)
    sesar_user = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='permissions', blank=True, null=True)
    team = models.ForeignKey(Team, models.CASCADE, related_name='permissions', blank=True, null=True)
    auth_group = models.ForeignKey(AuthGroup, on_delete=models.DO_NOTHING, blank=True, null=True)
    granted_by_team = models.ForeignKey(Team, models.CASCADE, related_name='granted_permissions', blank=True, null=True)

    class Meta:
        db_table = 'permission'
        unique_together = (('geopass_id', 'sesar_code'),)


class TransferHistory(models.Model):
    id = models.AutoField(primary_key=True)
    transfer_by = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='transfers_created')
    transfer_time = models.DateTimeField(default=timezone.now)
    orig_user = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='transfers_sent', blank=True, null=True)
    orig_team = models.ForeignKey(Team, models.DO_NOTHING, related_name='transfers_sent', blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    new_user = models.ForeignKey(SesarUser, models.DO_NOTHING, related_name='transfers_received', blank=True, null=True)
    new_team = models.ForeignKey(Team, models.DO_NOTHING, related_name='transfers_received', blank=True, null=True)
    status = models.CharField(max_length=32, default='pending')

    class Meta:
        db_table = 'transfer_history'


class BatchHistory(models.Model):
    batch_history_id = models.AutoField(primary_key=True)
    batch_type = models.CharField(max_length=10)
    sesar_code = models.CharField(max_length=10)
    sample_count = models.IntegerField(blank=True, null=True)
    upload_time = models.DateTimeField()
    upload_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='upload_by')
    processed_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='processed_by', related_name='batchhistory_processed_by_set', blank=True, null=True)
    processed_time = models.DateTimeField(blank=True, null=True)
    filename = models.CharField(max_length=64, blank=True, null=True)
    deleted_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'batch_history'


class DownloadHistory(models.Model):
    download_history_id = models.AutoField(primary_key=True)
    filters = models.JSONField()
    download_time = models.DateTimeField()
    download_by = models.ForeignKey(SesarUser, models.DO_NOTHING, db_column='download_by', blank=True, null=True)

    class Meta:
        db_table = 'download_history'


class SearchHistory(models.Model):
    id = models.AutoField(primary_key=True)
    filters = models.JSONField()
    search_time = models.DateTimeField()
    search_by = models.ForeignKey(SesarUser, models.DO_NOTHING, db_column='search_by', blank=True, null=True)

    class Meta:
        db_table = 'search_history'


class SampleUploadHistory(models.Model):
    sample_upload_history_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=True, null=True)
    upload_from = models.CharField(max_length=256, blank=True, null=True)
    upload_time = models.DateTimeField(blank=True, null=True)
    upload_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='upload_by', blank=True, null=True)

    class Meta:
        db_table = 'sample_upload_history'


class AnnualStats(models.Model):
    year = models.IntegerField(primary_key=True)
    batches_processed = models.IntegerField(blank=True, null=True)
    new_users = models.IntegerField(blank=True, null=True)
    active_users = models.IntegerField(blank=True, null=True)
    download_count = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'annual_stats'


class SampleRegistrationStats(models.Model):
    time = models.DateField(unique=True)
    samples_registered = models.IntegerField(blank=True, null=True)
    samples_updated = models.IntegerField(blank=True, null=True)

    class Meta:
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
        db_table = 'sample_delete_request'