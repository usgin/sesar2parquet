# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import AbstractUser, Group as AuthGroup
from django.conf import settings
from django.utils import timezone


class Agent(models.Model):
    AGENT_TYPES = models.TextChoices("Individual", "Organization")
    agent_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False)
    fname = models.CharField(max_length=100, blank=True, null=True)
    lname = models.CharField(max_length=100, blank=True, null=True)
    agent_uri = models.CharField(max_length=254, blank=True, null=True)
    address = models.CharField(max_length=2000, blank=True, null=True)
    organization_affiliation = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    #  need enumeration of vocabulary for agent_type. Should include individual, organization, maybe project, cruise...
    agent_type = models.CharField(max_length=50, blank=False, choices=AGENT_TYPES)
    point_of_contact = models.CharField(max_length=50, blank=True, null=True)
    parent_organization = models.ForeignKey('self', models.DO_NOTHING, related_name='agent_parent_organization_set',
                                            blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'agent'
        db_table_comment = 'Merge Person and Organization into single table to make ' \
                           ' linking to agents easier. Most roles are hard typed in this model. ' \
                           ' Need validation criteria-- \n\t- If agent_type is Person, then organization_affiliation, ' \
                           ' fname, lname is allowed, and parent_organization_id should be null' \
                           ' \n\t- if agent_type os Organization, then organization_affiliation, fname, lname ' \
                           ' should be null and parent_organization_id is allowed. \n- point of contact should be an e-mail address.  If possible, should be a repository role that will outlast the tenure of individuals at the repository.\n- label is the text that will be displayed for the agent in UI.\n- If person name, affiliation, parent organization changes, this should generate a new agent instance; the agent_uri should be constant, allowing aggregation of the various stages of the agent history.'


class CollectionType(models.Model):
    collection_type_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False)
    #    description = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'collection_type'


class Country(models.Model):
    country_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=255, blank=False, null=False)
    iso3166code = models.CharField(max_length=3, blank=True, null=True)
    is_active = models.IntegerField(blank=False, null=False)

    class Meta:
        #       managed = False
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

    class Meta:
        managed = True
        db_table = 'geologic_time_scale'
        db_table_comment = 'vocabulary of ICS geologic time ordinal eras, 2024 version'


# class GeometryColumns(models.Model):
#     f_table_catalog = models.CharField(primary_key=True, max_length=256)
#     # The composite primary key (f_table_catalog, f_table_schema, f_table_name, f_geometry_column) found, that is not supported. The first column is selected.
#     f_table_schema = models.CharField(max_length=256)
#     f_table_name = models.CharField(max_length=256)
#     f_geometry_column = models.CharField(max_length=256)
#     coord_dimension = models.IntegerField()
#     srid = models.IntegerField()
#     type = models.CharField(max_length=30)
#
#     class Meta:
#         #       managed = False
#         db_table = 'geometry_columns'
#         unique_together = (('f_table_catalog', 'f_table_schema', 'f_table_name', 'f_geometry_column'),)


class GeospatialLocation(models.Model):
    location_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False,
                             db_comment='text to display this location position in user interface. ')
    description = models.TextField(blank=True, null=True,
                                   db_comment='information about the position determination and representation.')
    sample = models.ForeignKey('Sample', models.DO_NOTHING, blank=False, null=False, default=-1,
                               db_comment='link to sample that this position applies to. ')
    vertical = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True,
                                   db_comment='based on vertical_srs, might be elevation (positive up) or depth (positive down).')
    vertical_srs = models.ForeignKey('SpatialRefSys', models.DO_NOTHING, db_column='vertical_srs', blank=True,
                                      null=True,
                                      db_comment='defines units of measure for vertical coordinate, positive up or positive down, and the datum-- that is the surface that has a 0 coordinate value.   If the position is within a borehole, the vertical_srs might be the borehole geometry. ')
    coordinate_1 = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True,
                                       db_comment='coordinate order (what is coordinate_1, coordinate_2) and interpretation must be specified in the spatial_reference_system definition. ')
    coordinate_2 = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True,
                                       db_comment='coordinate order (what is coordinate_1, coordinate_2) and interpretation must be specified in the spatial_reference_system definition. ')
    spatial_reference_system = models.ForeignKey('SpatialRefSys', models.DO_NOTHING,
                                              db_column='spatial_reference_system',
                                                  related_name='geospatiallocation_spatial_reference_system_set',
                                                  blank=True, null=True)
    wkt_geometry = models.CharField(db_column='WKT_geometry', max_length=100, blank=True,
                                    null=True)  # Field name made lowercase.
    global_grid_cell_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'geospatial_location'
        db_table_comment = 'The latitude and longitude in the sample table are required to use WGS84 decimal degrees. This table is optional, use to report coordinate locations with spatial reference different from WGS84, e.g. UTM, local grid coordinates, global grid cell identifiers, etc. '


class CollectionMember(models.Model):
    collection_member_id = models.AutoField(primary_key=True)
    collection = models.ForeignKey('SampleCollection', models.DO_NOTHING, blank=False, null=False,default=-1)
    sample = models.ForeignKey('Sample', models.DO_NOTHING, blank=False, null=False,default=-1)

    class Meta:
        #       managed = False
        db_table = 'collection_member'
        db_table_comment = 'correlation table that associated a sample with a collection. '


class SampleCollection(models.Model):
    collection_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=100, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    collection_owner = models.ForeignKey('SesarUser', models.DO_NOTHING, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    collection_type = models.ForeignKey(CollectionType, models.DO_NOTHING, blank=True, null=True,
                                   db_comment="type of collection")
    is_private = models.BooleanField(blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'sample_collection'
        db_table_comment = 'Definition of set of samples by some user to associate a set of samples for some purpose.'


class Initiative(models.Model):
    initiative_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    funding = models.CharField(max_length=50, blank=True, null=True)
    begin_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    initiative_uri = models.CharField(max_length=255, blank=True, null=True)
    initiative_type = models.ForeignKey('InitiativeType', models.DO_NOTHING, blank=False, null=False)

    class Meta:
        #       managed = False
        db_table = 'initiative'
        db_table_comment = 'Definition of an activity related to sample collection or stewardship. includes cruises, field programs, funded projects, '


class InitiativeType(models.Model):
    initiative_type_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'initiative_type'


class LaunchType(models.Model):
    launch_type_id = models.AutoField(primary_key=True)
    label = models.CharField(unique=True, max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'launch_type'


class Locality(models.Model):
    locality_id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    feature_type = models.ForeignKey('SampledFeatureType', models.DO_NOTHING, blank=True, null=True)
    locality_uri = models.CharField(max_length=255, blank=True, null=True,
                                    db_comment='use mindat location identifiers?')
    country = models.ForeignKey(Country, models.DO_NOTHING, blank=True, null=True)
    province = models.CharField(max_length=255, blank=True, null=True)
    county = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    permit = models.CharField(max_length=255, blank=True, null=True)
    collection_policy = models.CharField(max_length=255, blank=True, null=True)
    contained_in = models.ForeignKey('self', models.DO_NOTHING, db_column='contained_in', blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'locality'
        db_table_comment = 'definition of a named place associated with some geologic feature of interest. Binding to concrete geospatial coordinate location is assumed to be through information linked at locality_uri.'


class LocationMethod(models.Model):
    location_method_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'location_method'
        db_table_comment = 'was nav_type'


class MaterialType(models.Model):
    material_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    material_type_uri = models.CharField(max_length=255, blank=True, null=True)
    parent_material_type = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'material_type'
        db_table_comment = 'was classification'


class OtherProperty(models.Model):
    property_value_id = models.IntegerField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False,
                             db_comment='text to display property value in user interface')
    sample = models.ForeignKey('Sample', models.DO_NOTHING, blank=False, null=False,default=-1,
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

    class Meta:
        #       managed = False
        db_table = 'other_property'
        db_table_comment = 'Optional correlation table to link sample with descriptive properties not explicitly included in this schema. Was sample_customized_metadata'


class Platform(models.Model):
    platform_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    platform_type = models.ForeignKey('PlatformType', models.DO_NOTHING, blank=True, null=True)
    host_platform_id = models.IntegerField(blank=True, null=True)
    launch_type = models.ForeignKey(LaunchType, models.DO_NOTHING, blank=True, null=True)
    operator_id = models.ForeignKey(Agent, models.DO_NOTHING,blank=True, null=True)
    date_commissioned = models.DateField(blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'platform'
        db_table_comment = 'Definition of a facility that hosts sampling activities. Typically a ship or ship-based device (e.g. alvin) used to explore marine water bodies in accessible to direct human occupation.  Extent to include extraterrestrial  exploration devices like OSIRIS-REx. '


class PlatformType(models.Model):
    platform_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'platform_type'


class PropertyType(models.Model):
    property_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    property_uri = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'property_type'
        db_table_comment = 'vocabulary of properties that might have values assigned for a material sample'


class RelatedLocalDoc(models.Model):
    local_doc_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey('Sample', models.DO_NOTHING, blank=False, null=False,default=-1)
    primary_image = models.IntegerField(blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=100, blank=True, null=True)
    path_to_file = models.CharField(max_length=400, blank=True, null=True)
    uploaded_by = models.ForeignKey('SesarUser', models.DO_NOTHING, db_column='uploaded_by', blank=False, null=False)
    uploaded_date = models.DateField(blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'related_local_doc'
        db_table_comment = 'Table to provide links from sample to document hosted in the file system local to the SESAR server'


class RelatedResource(models.Model):
    relation_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey('Sample', models.DO_NOTHING, blank=False, null=False, default=-1)
    relation_type = models.ForeignKey('RelationType', models.DO_NOTHING, blank=False, null=False)
    relation_label = models.CharField(max_length=50, blank=False, null=False)
    related_resource_uri = models.CharField(max_length=50, blank=False, null=False)
    related_resource_type = models.ForeignKey('ResourceType', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'related_resource'
        db_table_comment = "table to provide links to web-accessible related resource via their URIs. Can be used to provide more explicit relation between a subsample and its parent that simply 'parent', e.g. mineral_separate, soluble_fraction..."


class RelationType(models.Model):
    relation_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)
    # need relation type URI
    scheme_uri = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'relation_type'
        db_table_comment = 'terms to assign semantics for relations between samples. Relations can detail the relationship between parent and child samples, use to link to publications, data, other online resources, relate to other samples.'


class ResourceType(models.Model):
    resource_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    resource_type_uri = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'resource_type'
        db_table_comment = 'kinds of things a sample can be related to, e.g. publication, dataset, sample, research project'


class Sample(models.Model):
    sample_id = models.AutoField(primary_key=True, db_comment='primary key for database. ')
    igsn = models.CharField(max_length=30, blank=False, null=False,
                            db_comment='globally unique identifier string that identifies the material sample. In DataCite/DOI context, this includes the DOI handle, the IGSN prefix and the token assigned when the sample was registered, the toke MUST be unique in the context of the DOI handle and IGSN prefix.')
    igsn_prefix = models.CharField(max_length=5, blank=False, null=False,
                                   db_comment='This includes the DOI handle prefix and the IGSN registration authority prefix.  ')
    name = models.CharField(max_length=255, blank=False, null=False,
                            db_comment='name used to represent the sample in user interface; might be IGSN, or a user-defined label for the sample.')
    parent_sample = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True,
                                      db_comment='This is the sample.sample_id for the parent sample; to get its IGSN would have to do a sample-sample join on origin_sample_id = sample_id')
    sample_type = models.ForeignKey('SampleType', models.DO_NOTHING, blank=False, null=False,
                                    db_comment='corresponds to iSamples material sample type, use iSamples vocabulary with earth science extensions.')
#    org_registrant = models.ForeignKey(Agent, models.DO_NOTHING, blank=False, null=False)
    cur_registrant = models.ForeignKey(Agent, models.DO_NOTHING, blank=False, null=False, related_name='sample_cur_registrant_set')
    req_registrant = models.ForeignKey(Agent, models.DO_NOTHING, related_name='sample_req_registrant_set', blank=True,
                                       null=True)
    igsn_is_system_assigned = models.IntegerField(blank=True, null=True)
    is_private = models.IntegerField(blank=False, null=False)
    publish_date = models.DateTimeField(blank=True, null=True)
    archive_date = models.DateTimeField(blank=True, null=True)
    registration_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)
    current_archive = models.ForeignKey(Agent, models.DO_NOTHING, related_name='sample_current_archive_set', blank=True,
                                        null=True,
                                        db_comment='link to agent that currently is the steward of the sample.')
    # original_archive = models.ForeignKey(Agent, models.DO_NOTHING, related_name='sample_original_archive_set',
    #                                      blank=True, null=True,
    #                                      db_comment='link to first agent that was the steward of the sample, if different from the current steward.')
    size = models.CharField(max_length=255, blank=True, null=True,
                            db_comment='text string  specifying size of sample; should be measured value with units of measure. MIght use mass or length dimensions. ')
    general_material_type = models.ForeignKey(MaterialType, models.DO_NOTHING, blank=True, null=True,
                                              db_comment='material type from iSamples material type vocabulary. Multiple more specific material types are specified through the sample_material correlation table.  ')
    material_name_verbatim = models.CharField(max_length=255, blank=True, null=True,
                                              db_comment='material name as provided by the original sample collector or sample registrant.')
    sample_description = models.TextField(blank=True, null=True,
                                          db_comment='Description of the sample; provide details-- material type, textures, dimensions, why collected, how collected, information about the sample context, etc. ')
    purpose = models.CharField(max_length=100, blank=True, null=True,
                               db_comment='brief explanation of why sample was collected.')
    geologic_age_verbatim = models.CharField(max_length=500, blank=True, null=True,
                                             db_comment='geologic age of the sample as reported by the original collector or registrant. ')
    numeric_age_min = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True,
                                          db_comment='Younger numeric temporal coordinate for age of sample; if only have a single age, provide it here and leave age_max null. \n\nunits are specified in numeric_age_unit field.  If a temporal reference system other than standard geologic time frame (yr, ky, my, measured positive back from 1950 CE), describe the reference system in the sample descriptions. ')
    numeric_age_max = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True,
                                          db_comment='Older numeric temporal coordinate for age range of sample; if only have a single age, provide leave age_max null. \n\nunits are specified in numeric_age_unit field.  If a temporal reference system other than standard geologic time frame (yr, ky, my, measured positive back from 1950 CE), describe the reference system in the sample descriptions. ')
    numeric_age_unit = models.CharField(max_length=12, blank=True, null=True,
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
                                    db_comment='longitude of point location where sample was collected, reported in decimal degrees using WGS84 Spatial reference system.  Location coordinates will be rounded to 6 decimal places.   If the sampling location position is specified with other spatial reference system, link through the location table.')
    latitude_end = models.DecimalField(max_digits=8, decimal_places=6, blank=True, null=True,
                                       db_comment='If the sampling location is a linear feature (e.g. the track of a a dredge haul), report the latitude of the end of the feature, using WGS84 decimal degrees.  ')
    longitude_end = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True,
                                        db_comment='If the sampling location is a linear feature (e.g. the track of a a dredge haul), report the longitude of the end of the feature, using WGS84 decimal degrees. ')
    vertical_min = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True,
                                       db_comment='vertical coordinate of sampling location position. Units of measure and the reference system are reported in the linked vertical_reference definition.')
    vertical_max = models.DecimalField(max_digits=9, decimal_places=4, blank=True, null=True,
                                       db_comment='if sampling location is a linear feature, e.g. a core from a borehole, report the max  coordinate of the sampling location position. Units of measure and the reference system are reported in the linked vertical_reference definition.  Generally, for cores, max coordinate will be the deepest beneath to datum. ')
    vertical_reference = models.ForeignKey('SpatialRefSys', models.DO_NOTHING, blank=True, null=True,
                                            db_comment="link to definition of vertical reference system; the definition must specify the units of measure, the datum ('0' surface) and the positive direction for coordinate values (up or down)")
    location_method_id = models.ForeignKey(LocationMethod, models.DO_NOTHING, blank=True, null=True,
                                             db_comment='link to description of how the location coordinates have been determined')
    location_qualifier = models.CharField(max_length=50, blank=True, null=True,
                                          db_comment='indicate uncertainty, whether locations have be obfuscated intentionally')
    sampled_feature_type = models.ForeignKey('SampledFeatureType', models.DO_NOTHING, blank=True, null=True,
                                             db_comment='was primary_location_type. Map to iSamples Sampled feature; this will likely be some geoscience feature. Link to controlled vocabulary.')
    locality = models.ForeignKey(Locality, models.DO_NOTHING, blank=True, null=True,
                                 db_comment='link to place name description of sampling location, as opposed to a coordinate position. ')
    locality_detail = models.TextField(blank=True, null=True,
                                       db_comment='linked locality entity has generalized information about the kind of locality; include details specific to this sampling location here. ')
    collection_method = models.ForeignKey('SamplingMethod', models.DO_NOTHING, blank=True, null=True,
                                          db_comment='link to generic description of the collection method')
    collection_method_detail = models.CharField(max_length=1000, blank=True, null=True,
                                                db_comment='text content includes details about specifics of the particular collection event for this sample')
    cruise_field_prgrm = models.ForeignKey(Initiative, models.DO_NOTHING, blank=True, null=True,
                                           db_comment='link to description of the cruise, field program, funded project or other activity that is the context for the collection of this sample')
    # collector = models.ForeignKey(Agent, models.DO_NOTHING, related_name='sample_collector_set', blank=True, null=True,
    #                               db_comment='agent acknowledged for collection of the sample. ')
    platform = models.ForeignKey(Platform, models.DO_NOTHING, blank=True, null=True,
                                 db_comment='Identifier for the facility that hosted the sampling event either directly or indirectly. Example of indirect host is launch of remote vehicle from a ship.')
    launch_platform = models.ForeignKey(Platform, models.DO_NOTHING, related_name='sample_launch_platform_set',
                                        blank=True, null=True,
                                        db_comment='If sampling was hosted indirectly from the facility identified, by platform_id, this identifies the proximate sampling device or facility hosted by the platform_id.')
    launch_label = models.CharField(max_length=100, blank=True, null=True,
                                    db_comment='label or identifier for a specify sampling platform deployment from a host platform, e.g launch of Alvin submersible from support ship.')
    collection_start_date = models.DateTimeField(blank=True, null=True,
                                                 db_comment='date and time of sample acquisition; if the acquisition event is only specfied as a time interval, this is the start of that interval. ')
    collection_end_date = models.DateTimeField(blank=True, null=True,
                                               db_comment='If sample acquisition event is specified as a date-time interval, this is the end of that interval. ')
    collection_date_precision = models.CharField(max_length=200, blank=True, null=True,
                                                 db_comment='indicate time interval that collection time is specified; e.g. minutes, hours, days, weeks, months...')
    metadata_store_status = models.CharField(max_length=25, blank=False, null=False,
                                             db_comment='internal status flag used by SESAR to track metadata management')
    # orig_owner = models.ForeignKey(Agent, models.DO_NOTHING, related_name='sample_orig_owner_set', blank=True,
    #                                null=True,
    #                                db_comment='link to agent who was original owner of sample, if different from the current owner.')
    cur_owner = models.ForeignKey(Agent, models.DO_NOTHING, related_name='sample_cur_owner_set', blank=True, null=True,
                                  db_comment='link to current owner of the sample. SESAR uses the owner ID to determine permissions for updating sample records.')
    last_changed_by = models.ForeignKey(Agent, models.DO_NOTHING, related_name='sample_last_changed_by_set', blank=True,
                                        null=True,
                                        db_comment='link to agent who most recently changed the content of this record.')
    # last_registrant = models.ForeignKey(Agent, models.DO_NOTHING, related_name='sample_last_registrant_set', blank=True,
    #                                     null=True, db_comment='link to agent that most recently registered the sample.')

    class Meta:
        #       managed = False
        db_table = 'sample'
        db_table_comment = 'base table with core sample description fields. The contents of this table are a digital representation of a physical, material sample. '


class SampleAdditionalIdentifier(models.Model):
    sample_external_identifier_id = models.IntegerField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False)
    identifier_scheme = models.CharField(max_length=50)
    identifier_value = models.CharField(max_length=256, blank=False, null=False)

    class Meta:
        #       managed = False
        db_table = 'sample_additional_identifier'
        db_table_comment = 'Simple link to implement one to many relation from sample id to other identifiers assigned to the sample'


class SampleAdditionalName(models.Model):
    additional_name_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False)
    name = models.CharField(max_length=255, blank=False, null=False)

    class Meta:
        #       managed = False
        db_table = 'sample_additional_name'
        db_table_comment = 'simple table to link one sample to potentially many different other names by which it is known'


class SampleMaterial(models.Model):
    sample_material_id = models.CharField(primary_key=True, max_length=50)
    sample = models.ForeignKey(Sample, models.DO_NOTHING, blank=False, null=False)
    material_type = models.ForeignKey(MaterialType, models.DO_NOTHING, blank=True, null=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'sample_material'
        db_table_comment = 'Correlation table to implement many to many relationship between samples and material constituents of the sample.'


class SampleType(models.Model):
    sample_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    sample_type_uri = models.CharField(max_length=255, blank=True, null=True)
    parent_sample_type = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    scheme_name = models.CharField(max_length=50, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'sample_type'


class SampledFeatureType(models.Model):
    feature_type_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    feature_type_uri = models.CharField(max_length=255, blank=True, null=True)
    parent_feature_type = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'sampled_feature_type'


class SamplingMethod(models.Model):
    collection_method_id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    method_uri = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=250, blank=True, null=True)
    scheme_uri = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'sampling_method'


class SesarUser(models.Model):
    sesar_user = models.OneToOneField(Agent, models.DO_NOTHING, primary_key=True)
    sso_account_id = models.IntegerField(blank=False, null=False)
    is_admin = models.BooleanField(blank=False, null=False)
    note = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    upload_permission_status = models.IntegerField(blank=True, null=True)
    upload_permission_date = models.DateField(blank=True, null=True)
    registration_date = models.DateTimeField(blank=True, null=True)
    deactivation_date = models.DateTimeField(blank=True, null=True)
    legacy_user_id = models.IntegerField(blank=True, null=True)
    geopass_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'sesar_user'


class SpatialRefSys(models.Model):
    srid = models.IntegerField(primary_key=True)
    auth_name = models.CharField(max_length=256, blank=True, null=True)
    auth_srid = models.IntegerField(blank=True, null=True)
    srtext = models.CharField(max_length=2048, blank=True, null=True)
    proj4text = models.CharField(max_length=2048, blank=True, null=True)

    class Meta:
        #       managed = False
        db_table = 'spatial_ref_sys'


class Group(models.Model):
    owner = models.ForeignKey(SesarUser, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    activate_date = models.DateTimeField(default=timezone.now)
    deactivate_date = models.DateTimeField(blank=True, null=True)
    doi_prefix = models.CharField(max_length=16, default='10.58052/')
    members = models.ManyToManyField(SesarUser, related_name='groups', through='GroupMember')
    part_of_group = models.ForeignKey("self", models.CASCADE, null=True, blank=True, related_name='teams')

    class Meta:
        db_table = 'group'
        db_table_comment = 'definition imported from SCao migration in legacy db updates'


class GroupMember(models.Model):
    group = models.ForeignKey(Group, models.CASCADE)
    sesar_user = models.ForeignKey(SesarUser, models.DO_NOTHING)
    is_admin = models.BooleanField(default=False)
    join_date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'group_member'
        db_table_comment = 'Related sesar user to a group. Definition imported from SCao migration in legacy db updates'
