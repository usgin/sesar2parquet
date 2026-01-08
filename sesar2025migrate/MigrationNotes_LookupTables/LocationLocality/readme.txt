Sample location concepts mix information about where (geographically) a sample was collected, with the context of the sample collection.  The sample is collected at a location that provides physical access to a feature of interest. 


Locality_Type (2024 schema) corresponds to SampledFeature_Type in iSamples model.  
Each locality has a feature type (locality.locality_type). It can also have a 'parent' feature to assert that it is part of some larger feature (the 'locality.contained_in field. Locality also has country_id (FK to country vocabulary), a province, county, and city. Only some of these are populated; need to figure out what kind of 'typeing' is going to actually be useful.  Many locations are just named places-towns, mountains, water bodies, but lack information about what kind of feature was actually sampled, so the locality doesn't actually correspond to the sampled_feature concept.

Workflow-
Fields in the SESAR database with information about location:
primary_location_type, primary_location_name, location_description, locality, locality_description, province, county, city, country_id

AllLocationDistinct.xlsx starts with a unique values query 
 “SELECT distinct locality,primary_location_name,primary_location_type,location_description,
locality_description,province, county, city, country_id from sample”
--put in country names by looking up on country_id. 
-- Add column  location_detail; concatenate location_description and locality_description. Use this for lookup to get locality if {locality,primary_location_name,primary_location_type,province, county, city, country_id} are all NULL
-- add columns for SESAR2024.locality_id, locality.feature_type_id, locality_type (label), locality.locality_name
-- add columns for lookup keys to map from legacy sesar to new localities. Construct keys in 2 steps: 
	---lookupkey--=SUBSTITUTE(TRIM(locality&primary_location_name&primary_location_type),"~", ""). Have to get the '~' characters out because they break the Excel vlookup function.
	---LookupKey2: concatenate province, county, city, country.  If province, county, city is null, the concate has 'NULL', if country is null, leave blank. 
	---fullKey  concat lookupkey and LookupKey2.
	
-- Spend a ridiculous amount of time cleaning up locality_name to reduce duplication. Generate names with information from the legacy sesar columns. Correct obvious spelling mistakes. Generally if there are locations from different parts of some relatively (a subjective call, no guarantee of consistency...) compact feature (a particular mine, mountain, fault, valley....) that becomes one locality.  There is still alot of duplication-- different label strings for a single place. If there is some kind of sampling feature site name or identifier, keep that in the locality_name.
-- generate a feature type vocabulary based on the locations described in the legacy data. 
-- classify many, but not all, of the localities to a feature type.  There's a bunch of work still to do here if it seems useful. 

Generate a locality vocabulary based on distinct values from the location-related fields in legacy SESAR (primary_location_type, primary_location_name, location_description, locality, locality_description, country_id, province, county, city).  The distinct values are in AllLocation_Distinct-lookup sheet in AllLocationDistinct-refine.xlsx spreadsheet.
The initial locality vocab was taken into OpenRefine to cluster the location labels-- there is a lot of duplicatoin with various place name constructions. I didn't process all the clusters (>2000) of them-- that will require more work; theres lots of situation where it's not clear if two strings label the same place. 

Sampled Feature type vocabulary (in sampled_feature_type table) should be used to populate SESAR2024.locality.locality_type.  Currently a SESAR2024.locality can have only one sampled_feature_type.  We should consider if this constraint needs to be relaxed.  The sampled feature type vocabulary is currently quite heterogeneous, with physiographic features, tectonic settings, geologic structures, Earth Environments.  It is build top down starting with the CGI geologic environments, then bottom up with IMLGS settings, and locality_types, names, descriptions from SESAR0821.  The goal of this vocabulary is to provide users 'facets' to zero in on the samples of interest.  Problem of course is that there are all kinds of ways a user might want to zero in. The rdf version of the vocabulary is a multi hierarchy (Directed acyclic graph); to be useful for search query resolution, the search client will need to be able to handle transitive closures in this graph. If someone searches for 'submarine volcano', possible hits might include seamount, guyot, volcano. 

for the sample table, need lookup key to get locality_id from the 'xxx' field in the spreadsheet 
the key is a concatenation of all the location fields from legacy data:

primary_location_type, primary_location_name, location_description, locality, locality_description, country_id, province, county, city
spaces are removed, and special characters that bollux up the lookup functions are removed, using 'Substitute' function:
using these formulas in Excel:
part one: =SUBSTITUTE(TRIM(locality&primary_location_name&primary_location_type),"~", "")
note the apparent space is a special character, not a regular space….
Part two: =SUBSTITUTE(TRIM(province&county&city&country_id),"~", "")
Part three: =SUBSTITUTE(IF(locality_description="NULL","",locality_description) &
    IF(ISERROR(FIND("Matched",location_description)),IF(location_description="NULL","",location_description),""),"~", "")
part three is a little tricky-- don't include the long 'Matched by...' explanations from smithsonian-- the result is in the locality_description; also don't include NULL values.
FINALLY:  concatenate and remove spaces and other unwanted characters (#,",?,*): 	
=LEFT(substitute(Substitute(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(A2&B2&C2," ", ""),"#",""),"""",""),"?",""),"*",""), 254)

the fullKey is constructed in the AllLocation_Distinct-lookup sheet in AllLocationDistinct-refine.xlsx spreadsheet.
After initial testing, export the fullKey and locality_id to a separate csv file for better performance on the ETL processing

the constructed key matches the 'fullKey' field in the spreadsheet to get the locality_id for the sample table
If there is no locality, skip
the locality_detail in sesar2024 is a string concatenated from all the source location fields, with NULLs removed and blanks skipped. This preservis all original information.


workflow for loading data...
create a dataframe with the lookup values before diving into the sample ETL
for each sample, construct the lookupkey; if its null skip
use the key to grab the locality_id from the lookup table

execution for load sample with 100000 records takes 43.36 seconds

**********************************************************************

Preliminary working files kept just in case, but probably will archive.

--LocalityTypeLookup.xlsx:
select distinct primary_location_type from sample 
		where primary_location_type is not null
		order by primary_location_type

--LocalityDescriptionLookup.xlsx	
select distinct locality, locality_description

--primaryLocationTypeDistinct20240821.xlsx
select distinct primary_location_type
*** initial development of sampledFEaturetype vocabulary extension by categorizing location types from SESAR data. Try to distinguish 'types' that are place names ('name'--instances), geographic location descripions ('location'), materials, and types (kinds of locations); several other classes of 'type' terms identified in the 'class' column here. 

--LocationTypeNameLocalityLookup.xlsx
select distinct primary_location_type, primary_location_name, locality
*** this ended up being the most useful.  Add fields for the SESAR2024 database locality_type,locality_name, locality_description. Load locality_descriptions from SESAR0821 with join on 'SESAR0821.sample.locality'.  Then map content from primary_location_type, primary_location_name, locality to the new fields for SESAR2024.
  Looking at the content in SESAR0821, its clear there has been confusion about what goes in the location_type, location_name and locality fields. We need to make it clear that 'location name' is the name of a place (a geographic location instance); location_type is a kind of place that was sampled, and locality_description provides additional science context or geographic detail about location specifics. Locality_description can be completely free text. Locality_type should be a controlled vocabulary. Locality name should autocomplete with existing or suggest similar existing place names to reduce duplication, but allow new names to be entered. Curator will need to inspect what is in these fields for submissions and determine if the content makes sense and is useful; Policy decision is to what extent curators clean things up or return to registrant to get better information.  

 