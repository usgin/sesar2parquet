# Agent table
NOTE 2025-02-07 SMR.  this information is out of date; archive_lkup and peng_org tables are out of date and turned out not useful.  Agents table is not used; Individual, Institution and Group are in separate table. IDs in individual and institution do not overlap. related_sample_agent table is used to resolve responsible party relationships that might be any of individual, instituion or group.

 the agent table includes agents from sesar_user, sesar_user.institution, sesar_user.institution_detail,  sample.collector, and archive_lkup
 - sesar_user.institution needs to be updated with peng_org.org_name, but not all sesar_user.institution have matching peng.org_name.  
 - need new lookup to clean sesar_user.institution, with the peng mappings, and new mapping for stuff peng didn't map.
  
 query for institution lookup table csv export:
 
```
SELECT distinct sesar.institution, sesar.institution_detail, peng.org_name 
	FROM public.sesar_user as sesar left join public.peng_org as peng 
	on peng.sesar_name = sesar.institution order by sesar.institution
```

lookup from archive_lkup to peng.org to see what matches: only get a couple matches

Also have archive_mapping table that normalizes archive names-- use this for agents. 
archive_lkup is not sync'd with what is in the db, so construct query to get archive names from sample.current_archive and sample.original_archive

query:

```
SELECT map.archive_mapping_id, 
		sam.current_archive as archive_org, 
		sam.current_archive_contact as archive_contact, 
		map.preferred_archive_name, 
		peng.org_name as peng_name
	FROM  public.sample as sam 
		  LEFT JOIN public.archive_mapping as map
			on map.user_entered_archive_name = sam.current_archive
		  LEFT JOIN public.peng_org as peng 
			on peng.sesar_name = sam.current_archive
UNION 
SELECT	map.archive_mapping_id, 
		sam2.original_archive as archive_org, 
		sam2.original_archive_contact as archive_contact, 
		map.preferred_archive_name, 
		peng.org_name as peng_name
	FROM  public.sample as sam2 
		 LEFT JOIN public.archive_mapping as map
			on map.user_entered_archive_name = sam2.original_archive
		 LEFT JOIN public.peng_org as peng 
			on peng.sesar_name = sam2.original_archive 
ORDER BY archive_org ASC 
```

need to concatenate these to get organizations in 2024 agents table.  
PK agent_id will start with copying sesar_user.sesar_user_id.  
agent_id from the merged organizations will start with max(sesar_user.sesar_user_id) and increment from there. 

for people, all orcids in ecl_orcid_temp are in sesar_user.orcid, so the ecl_orcid_temp table is not needed.

need to append collectors to agents draft compilation and harmonize with sesar_users. Collector_lkup is out of sync with public.sample.collector; need to use collectors in authority table, collector_lkup does not appear useful.  Query:

```
SELECT distinct  sam.collector as sam_collector, lkup.name as lkup_name,
	s.fname, s.lname
	FROM public.sample as sam left join public.collector_lkup as lkup
	on sam.collector = lkup.name
	left join sesar_user as s  on sam.collector = s.orcid
ORDER BY sam.collector ASC 
```

Note that most of the orcids in the collector.lkup do not match orcid's in sesar_user.

NOTES
- There are persons with multiple sesar_user instances.
- person can have multiple affiliations, affiliations might overlap in time
- Sesar_User has a single affiliations
- Persons can have different names/aliases.
- persons can have multiple e-mail addresses; e-mail might be associated with affiliation, or just might be alternate addresses
- have many persons only associated with e-mail address

agent-agent relations
individuals have affiliation with organiztion, time stamped
organization have 1..*  point of contact, possibly time stamped
organization has parent organization. possibly time stamped
point of contact must have e-mail or address
affiliation must be from individual to organization
parent organization must be between organizations


An agent is a unique person or organization.  (identity of organization is potentially problematic).
in the sesar user table, there are agents with multiple sso-account-ids associated.  there are organizations with sso-ids.  there are agents with Null sso-ids, and agents with both a null and an integer sso-id. 

I'm trying to generate the Agents table for the migration, with the  idea that An agent is a unique person or organization.  (recognizing that identity of organization is potentially problematic).   I'm identifying people using name strings (with some small potential duplication for people with same first & last name).  In the current sesar user table, there are several variations:
- multiple sso-account-ids associated.  
- organizations with sso-ids.  
- users with Null sso-ids, 
- users with both a null and an integer sso-id. 

From this, it seems that
- a sesar_user can be an organization (e.g. Indiana Geological and Water Survey, Integrated Ocean Drilling Program (TAMU), Curator) or a person
- a sesar_user can have multiple associated sso-account_ids
- the sesar_user_id does not identify an agent; commonly it is person with a particular affiliation, but not always (e.g. see 'Cameron, Cheryl') sometimes same affiliation with different e-mails (e.g. 'Choe, Saebyul'),  sometimes same e-mail/affiliation but one of them has sso-id = NULL. 

I was hoping to be able to use the sesar_user_id as the agent_id for the migration, but because of these issues, I think there will have to be a new agent_id generated that will preserver the sesar_user_id for sesar users with unique names, and new agent_ids to identify people who have multiple sesar_user_ids. 


- agents will have  a optional e-mail or address,  
- sesar_user has institution_id and point of contact (poc), both of which are FK to agents table.
- there will be a correlation table to allow many to many relationship between agents to allow for multiple affiliations, and multiple points of contact. these will be time stamped because they can change over time. 

the correlation table will be needed if there are multiple links, but not necessary in the simple case of a single point of contact or affiliation. 


agents table	
   insert records from unique individuals table.  IDs are generated first from sesar_users who do not have multiple sso_account_ids.  Then add other sesar users starting with ids between 1801 and 1890.  ORganization ID's start at 15000
   Add users from  agents.xlsx uniqueIndividuals tab.  It might take another pass to add poc information.  
   For affiliations, will ndde to lookup AgentID ion the OrgLKUP table. 
   poc information is in seser_user, collectors, org_poc_lkup, and archiveContact. mappings will need to use the names to match and pull e-mail, orcid, address where there are avaialble .
   
sesar_user.
	sso_account_id, is_admin, password, upload_permission_status and _date, legacy_user_id, geopass_id all stay the same. 
	add agent_id via mpaping in Agent.xslx, maching the sesar_user ID in sesar_user.sam.sesar_user_id to sesar_user.AgentID.  Some agents have multiple sesar_user_ids.
	for the map the sesar_user.institution to an agent_id by matching the name string to orgLKUP.Org_verbatime or indivLKUP.label_verbatim.   If an institution is found it will be an Agent, and if there is an email, that goes in the new sesar_user_institution_poc_id, otherwise use the emial (or asddress) from the agent associated with the Sesar_user.


sample.collector:
	multiple collectors might be associated with sample, use correlation table related_sample_agent, with role = collector
	workflow:
		1. does the string in sample.collector match multiple_collector_lkup.sam_collector, if so then get the list of names from that row in the multiple_collector_lkup table and look for each name in indivLKUP.label_verbatim; insert a related_sample_agent link for each one in the list; the notes on the link should include the name from the list in the multiple_collector_lkup.sam_collector row. from sample.sample_id to indivLKUP.AgentID
		2. if not, then match the name in sample.collector to sesar_user and create the related_sample_agent link from sample.sample_id to indivLKUP.AgentID
		
		if the collector name doesn't match anything in indivLKUP, check if there's a match in orgLKUP and use that
		if there is no match for either, put the name in the related_sample_agent.notes, and use the id for unknown '12734'
		

Samples table:
	Three sesar_users are linked directly to sample table-- req_registratnt, cur_registrant, and last_changed_by. 
	The sesar_user ID will be the same so no change is necessary.
 
 
	cur_owner_id, orig_owner_id, org_registrant, cur_archive, original_archive, collector, last_registrant_id are all linked to agent via related_sample_agent correlation table. registrant is expected to be a sesar_user, but other roles are not necessarily sesar_users,and could be individual or organization. follow same procedure as for collectors.
 
