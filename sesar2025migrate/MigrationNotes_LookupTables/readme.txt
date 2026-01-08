This directory contains vocabulary listings, lookup files, and schema diagrams to support migration from the legacy SESAR database to the SESAR 2024 database. 

When there are no existing starter vocabs, draft vocabularies are compiled from unique-values query against the appropriate fields in the legacy SESAR database. See MIgrationDocumentation.docx in this directory for more information. The notes here are from early in the ETL process implementation and are likely of historical interest only.

* Locality type (Sampled feature type)
 Sampled feature is under construction, compiled from existing SESAR data and iSamples sampledFeature and GeoSciml 'eventEnvironment' vocabularies. This populates localityType in SESAR2024.  See github, geosamples/vocabularies/vocabulary directory, SESAR_sampled_feature_extension.ttl.

* Sampling Method draft constructed from existing SESAR data and GeoScience Australia, CGI geoscience terminology group draft vocabularies. Current version is in a Turtle/RDF file to handle multiple inheritance.  In github, geosamples/vocabularies/vocabulary directory.

* initiative type -- 
	Draft compiled by categorizing the samples.cruise_field_prgram  values in the SESAR database. SMR 2024-09-10

* platforms
 * Platform names -- worksheet in MigrationNotes_LookupTables/platform_name_vocab.xlsx Cleaned up list of platform names and types based on unique values query result in MigrationNotes_LookupTables/CruisePRgrmWPlatformAndDates.xlsx, generated with query "SELECT  cruise_field_prgrm, platform_name, min(collection_start_date) as start, max(collection_start_date) as end FROM public.sample 	group by cruise_field_prgrm, platform_name	order by min(collection_start_date)"  from legacy SESAR db. Want to include start date (first platform deployment) and end data (when platform retired).  Most platforms are ships.
	
 * platform type -- worksheet in MigrationNotes_LookupTables/platform_name_vocab.xlsx ; generalized from platforms discovered with unique values query listed in 'platform names', above.
 * platform type -- worksheet in MigrationNotes_LookupTables/platform_name_vocab.xlsx ; generalized from platforms discovered with unique values query listed in 'platform names', above.
 
*navigation type
  construct draft from existing SESAR data

* launch type
  construct draft from existing SESAR data
  

	
  
  
***********************************************************
From Existing vocabularies:
* GeologicTime vocabulary uses the ICS 2024 time scale. 

* Sample type - use iSAmples Material Sample Object Type with EES extensions.

* Countries use ISO3166 2 letter codes following what is in the current SESAR database

* Materials - 
* topClassification: use the iSamples base and EES extensions. 
* materialtype (cassification).  Starting point is iSamples material type, extend for EarthScience with more extensive lithology classes in iSamples extension. These are both turtle RDF SKOS in the iSamples Github. Isamples extension has 87 classes.   For more detail, can use SESAR_material_extension_rock_sediment.ttl, which has 310 classes.  I think this SESAR extension is too big.  Mindat, BGS, GeoSCIML, Geo survey Queensland  or other vocabularies could be used for more granular lithology types, but I think these classisifications would be accounted for just fine with what people put in the verbatim material type free text field.
  * minerals (Classification) -- Use Strunz or Data classes with topClassifiction? Using the IMA approved mineral names to identify mineral species makes the most sense. in the geosamples/vocabularies/vocabulary directory, find 'top250minerals.xlsx', a spreadsheed that contains the 250 minerals with the most reported occurrences from Mindat.   MineralSKOS.ttl is an rdf vocabualry serialized with Turtle that includes all minerals with more than one occurrence in MinDat. 

