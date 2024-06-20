#  Work to execute ETL from SESARlegacy to SESAR2024

## 2024 material_type
table can include material types from various vocabularies.  the general_material_type foreign key  links to the material type vocabulary used as the top-level facet.  I'd like to see these be the iSamples (with extensions) vocabularies.  sample_material correlation table is used to link to material types from other vocabularies, or more specific material types.   NEED a 'general material type' vocabulary. 
map existing classification to material_type with scheme_name  'original SESAR classification'.  Will have to come back later and map to 'general_material_type'

##country
there is a correlation table country_id_map that maps geopass country_id to sesar country_id.  Do we still need this?  why not update geopass country ids?

##cruise_field_prgrm_lkup
Didn't Bob Arko clean up the cruise list?

## download_history
don't have corresponding table in new design.  Copy table to new dB

## ecl_orcid_temp
Maps geopass_account_num to ORCID. Use to get identifiers into agent field.

##gfz_igsns_need_fix
don't know what to do with this...

## group_sample
correlated samples with groups that include the sample.   one to one mapping, but make sure have same sample and group id's.

## groups
one to one mapping, keep group id's the same. check group_type FK to collection_type vocabulary.

## nav_type
goes to location_method, have to make sure FK integrity is preserved.

## peng_org
normalized organization names; these should be the values in the Agent table for agent type = organization.

## platform_name_lkup
convert to vocab table platform; name becomes label.  Have to figure out host platforms if applicable

## platform_type-lkup 
convert to vocab table platform_type; name becomes label

## primary_location_name
lkup, locality, primary_location_type_lkup, location_description, locality_description --  Have to map distinct combinations of location-related fields to SESAR2024 locality. 2024 locality includes geographic, political, geologic features, e.g. place names, formation names, tectonic environments....  Establishes context for sample collection.  These are mixed between location_name and locality in SESAR2017 Should this be split into geographic/political locations and a separate table for geologic/tectonic sampled features?  Need to make sample--> locality many to many.  Geologic or tectonic units go in Geologic unit_verbatim field.   Tectonic env should be location type. 

## registrar_lkup
not clear what this is for, is sequence of integers, not sequential.

## Sample
### location
22642 samples have UTM northing; add separate table for other coordinate location? 
	
### geologic age
age_min, age_max have numbers; convert all to Ma for numeric age fields.  Geological age has some geologic TOEs, also text for numeric age, which might not be reflected in age_min, age_max fields.   if has TOE, put in 2024 geologic age, have to work on whether to do min and max.  make table of unique age_min, age_max, age_unit, and geological_age to make mapping to 2024 numeric_age and geologic_age fields.   In simplest case just load age_max, age_min to numeric age fields, and geological_age to geological age_verbatim field .  The age max field has some calendar dates in it.   Not clear how to treat these as geologic ages. Some of these are eruption dates for volcanic samples. 
	
### classification
top level can use iSamples material type.  Populate sample material table from classification table mapping to iSamples.  get mindat URIs for minerals  
	
### agents
have to construct Agent table from collector, cur_owner_id,  cur_registrant_id,  current_archive, current_archive_contact, last_changed_by, last_registrant_id, orig_owner_id,  original_archive,  original_archive_contact, req_registrant_id.   *Note that collector is many to many, need correlation table*
	
### Initiative
construct initiative table from cruise_field_prgm.  a launch is part of an initiative; The launch_label and collection_start_date and collection_end_date serve to identify individual launches.
	
### geological unit
make current field a 'verbatim'; this will get content from geological_unit and from locality, location fields in SESAR 2017.  Later can add URI or FK to a geologic lexicon table.  Geologic unit is about rock body.  Locality is about location,
	
### platform
generate platform lookup tabel from samples launch_platform_name, platform_name, platform_descr, platform_type. have to capture  link  between a platform (e.g. Alvin) and a host platform (the ship hauling Alvin)
	
### vertical location
vertical min,max and reference id generate from elevation, elevation_end, elevation_unit, depth_max, depth_min, depth_scale, vertical_datum. will need to generate spatial reference system entries.
	
### geospatial_Location table
generate from northing, easting, zone
	
### sample_description
is concatenation of sample_comment, description, classification comment, collector detail, and possible other random text scattered about.
	
### Sample_type
corresponds to iSamples Material_sample_object_type. 
	
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

## sesar_users
most will go into Agents table, sesar specifica stuff to 
	
#	Work flow


## Tables that copy directly
fields in source table map directly to fields in target tables. All source table content accounted for.

## lkup tables that need to be made into vocabularies
will have to gin up resoure_type and relation_type. 

## agents
decouple sesar_users from full list of all individuals/ogranizations related to samples. preserver ids if poossible. Collectors are many to many w.r.t. sample. Have to merge sesar_user.{fname, lname}, sesar_user.institution, collector_lkup, archive_lkup,

## Tables that require mapping from distinct values on combination of fields
	1. material types
	2. locality, location
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
