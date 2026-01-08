#  Work to execute ETL from SESARlegacy to SESAR2024
Notes. Stephen Richard smrTucson@gmail.com
modified date 2024-10-30

## 2024 material_type
table can include material types from various vocabularies.  the general_material_type foreign key  links to the material type vocabulary used as the top-level facet.  I'd like to see these be the iSamples (with extensions) vocabularies.  sample_material correlation table is used to link to material types from other vocabularies, or more specific material types.   NEED a 'general material type' vocabulary. 
map existing classification to material_type with scheme_name  'original SESAR classification'.  Will have to come back later and map to 'general_material_type'

## archive_lkup
names of repository origanizations, load into agent table with type=organization (or archive).  Turns out the _lkup tables are out of sync with the existing database and I've started ignoring them, running unique value queries on the appropriate fields to determine what's in the database.

## country
there is a correlation table country_id_map that maps geopass country_id to sesar country_id.  Do we still need this?  why not update geopass country ids?
2024-10. Have created country vocabulary table with country_id (integer), label, ISO3166 code (two character), and 'is_active' boolean flag.

## cruise_field_prgrm_lkup
Didn't Bob Arko clean up the cruise list?.  2024-10. Not currently using this

## download_history
don't have corresponding table in new design.  Copy table to new dB. No action in migration code.

## ecl_orcid_temp
Maps geopass_account_num to ORCID. Use to get identifiers into agent field.

## gfz_igsns_need_fix
don't know what to do with this...

## group_sample
correlated samples with groups that include the sample.   one to one mapping, but make sure have same sample and group id's.

## groups
2024-10. This becomes collection in 2024 database schema.  one to one mapping, keep group id's the same. check group_type FK to collection_type vocabulary.  

## nav_type
goes to location_method, have to make sure FK integrity is preserved.  2024-10 mapping function done

## peng_org
normalized organization names; these should be the values in the Agent table for agent type = organization.  Compare with archive_lkup table.

## platform_name_lkup
convert to vocab table platform; name becomes label.  Have to figure out host platforms if applicable

## platform_type-lkup 
convert to vocab table platform_type; name becomes label. not used, based on unique values in sample table.

## primary_location_name
lkup, locality, primary_location_type_lkup, location_description, locality_description --  Have to map distinct combinations of location-related fields to SESAR2024 locality. Legacy locality includes geographic, political, geologic features, e.g. place names, formation names, tectonic environments....  Establishes context for sample collection.  These are mixed between location_name and locality in SESAR2017 Should this be split into geographic/political locations and a separate table for geologic/tectonic sampled features?  Need to make sample--> locality many to many.     Tectonic env should be location type. 
If locality_type is geologic unit, put name in SESAR2024.geologic_unit field

## registrar_lkup
 not clear what this is for, is sequence of integers, not sequential.


## Sample
### location
22642 samples have UTM northing; put in geospatial_location field.
	
### geologic age
age_min, age_max have numbers; convert all to Ma for numeric age fields.  Geological age has some geologic TOEs, also text for numeric age, which might not be reflected in age_min, age_max fields.   if has TOE, put in 2024 geologic age, have to work on whether to do min and max.  make table of unique age_min, age_max, age_unit, and geological_age to make mapping to 2024 numeric_age and geologic_age fields.   In simplest case just load age_max, age_min to numeric age fields, and geological_age to geological age_verbatim field .  The age max field has some calendar dates in it.   Not clear how to treat these as geologic ages. Some of these are eruption dates for volcanic samples. 
	
### classification  (material type)
top level can use iSamples material type.  Populate sample material table from isamplesMaterialtype, EarthEnv material type extension and opencontext extension (not the rock/mineral parts).  sample_material correlation table carries verbatim field name.  get mindat URIs for minerals .  Need to add a role on in sample_material correlation for samples with multiple material constitutents, e.g. for protolith links for metamorphic rocks or analytical preparations. 
	
### agents
	see separate document 'agentsMapping.md'.
	have to construct Agent table from collector, cur_owner_id,  cur_registrant_id,  current_archive, current_archive_contact, last_changed_by, last_registrant_id, orig_owner_id,  original_archive,  original_archive_contact, req_registrant_id, 
	
### Initiative
	construct initiative table from cruise_field_prgm.  a launch is part of an initiative; The launch_label and collection_start_date and collection_end_date serve to identify individual launches.
	
### geological unit
make current field a 'verbatim'; this will get content from geological_unit and from locality, location fields in SESAR 2017.  Later can add URI or FK to a geologic lexicon table.  Geologic unit is about rock body.  Locality is about location,
	
### platform
generate platform lookup tabel from samples launch_platform_name, platform_name, platform_descr, platform_type. have to capture  link  between a platform (e.g. Alvin) and a host platform (the ship hauling Alvin)
	
### vertical location
vertical min,max and reference id generate from elevation, elevation_end, elevation_unit, depth_max, depth_min, depth_scale, vertical_datum. will need to generate spatial reference system entries.
on inspecting the data, the values in these fields do not make sense in many cases. Elevations >25000 meters, vertical data or units not reported. When is postive up or down?  many depths are below sea floor, and in many cases elevation looks like possible depth to sea floor for a borehole collar that a series of samples are from -- thus the reference datum for depth. Cleaning this up to be consistent and error minimized is too big a job to handle in the time available.  
For IMLGS that has 'start depth' and 'end depth', presumably for underwater traverses--e.g. dredge haul, use additionalProperty.	

### geospatial_Location table
generate from northing, easting, zone

### sample_description
is concatenation of sample_comment, description, classification comment, collector detail, and possible other random text scattered about.
	
### Sample_type
corresponds to iSamples Material_sample_object_type.  Have mapping from existing SESAR sample type to iSamples vocab and vocab extension.   ...GithubC/iSamples/content-classification/SESAR/trainingDataApproach/trainingData/SESAR_training_dataset_archive.xlsx  SpecimentType tab. Build sample type vocab table from iSamples vocabularies. 
	
### metadata_store_status
values are currently mostly about relation to Datacite.  Is there a need for an isPrivate flag?
	
## sample_delete_request
will this be used in new implementation.

## sample_doc
maps to related local_doc.  new table doesn't have file_size that is in legacy table. *ADD?*.	

## sample_publication_url
content loads into related_resource in SESAR 2024, resource type should indicate 'publication'
	
## sample registration_stats
not sure we need to migrate; managment and monitoring

## Sample_type
make vocab table, hopefully use iSamples and extensions
  
## sample_upload_history
not sure what to do with this.

## sesar_user
most will go into Agents table, sesar specific stuff to 2024 sesar_user table.  notes apply to current sesar_user, put these in new sesar user table.   *?ADD note field in 2024 agent table?*

## sesar_user_code
IGSN prefixs; a user might be associated with multiple prefixes (user codes). copy table, make sure ids are the same

## sesar_user_code_role
maps users to role id (integer 1-4). Sesar_role table defines roles.  Also has geopass_id, user_code, and orcid_id, all of which duplicate content in either sesar_user or sesar_user_code.  Leave this for admin reimplmentation.

## spatial_ref_sys
spatial refrence system. copy table.  *add description field and label?*
	
#	Work flow

## Tables that copy directly
fields in source table map directly to fields in target tables. All source table content accounted for.

### agents
decouple sesar_users from full list of all individuals/ogranizations related to samples. preserver ids if poossible. Collectors are many to many w.r.t. sample. Have to merge sesar_user.{fname, lname}, sesar_user.institution, collector_lkup, archive_lkup,
### individual
there are 91 individuals and one institution that have multiple SESAR user accounts. Can't preserve sesar_user id's uniquely in individual table for those agents. the individual will need a new ID, and the SESAR_USER table has to have a FK to the Individual table. The orgs with sesar accounts will be come groups in the new schema.

### institution
institutions are any collection of agents that have an identifier. Some institutions might also be SESAR groups.


## Tables that require mapping from distinct values on combination of fields
	1. material types
	2. locality
	3. initiative
	4. platform

## Sample table:
	break into steps
	1.  generate base table by copying fields that don't change: {sample_id, parent_sample_id, dates, lat, long)  
	2. add agents. All the person related IDs will likely have to be tanslated through a mapping table to remove duplicates. 
	3. insert fields that require a transform mapping between legacy db and SESAR 2024
	4. get the vertical coordinate location from depth and elevation fields, generate 
	
## question tables
	tables that have unclear purpose and might not need to be migrated.

### lkup tables that need to be made into vocabularies
will have to gin up resoure_type and relation_type. NOTE_- the lkup tables are out of sync with current db content, don't use; construct distinct value queries from legacy sample table.
