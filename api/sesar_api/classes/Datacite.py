import json
import datetime
import requests
import os
from django.conf import settings
from django.db.models.functions import ExtractYear
from sesar_api.models import Sample

class IGSNToDatacite:
    """
    Handles interactions with the Datacite API.
    """
    def __init__(self, sample: Sample):
        self.base_url = os.getenv('DATACITE_BASEURL', "https://api.datacite.org/")
        self.sample = sample
        self.test_mode = os.getenv('DATACITE_TEST', False)
        self._credentials = self._parse_credentials(os.getenv('DATACITE_CREDENTIALS', '{}'))
        self._login, self._pswd = self._get_credentials(sample.igsn)

    def _parse_credentials(self, json_string):
        return json.loads(json_string)

    def _get_credentials(self, igsn):
        prefix = igsn.split("/")[0] + "/"
        creds = self._credentials.get(prefix, {})
        return creds.get("username"), creds.get("password")

    # get existing igsn registered with Datacite
    def get_igsn(self):
        url = f"{self.base_url}dois/{self.sample.igsn}"
        response = requests.get(url, auth=(self._login, self._pswd))
        return response

    # register a new igsn with Datacite
    def register_igsn(self):
        post_data = self._assemble_json(self.sample)
        url = f"{self.base_url}dois/"
        response = requests.post(url, auth=(self._login, self._pswd), headers={"Content-Type": "application/vnd.api+json;charset=UTF-8"}, data=post_data)
        return response

    # update existing igsn metadata
    def update_igsn(self):
        existing_datacite_record = json.loads(self.get_igsn().text)
        existing_datacite_record = existing_datacite_record.get('data', None)

        post_data = self._assemble_json(self.sample, existing_datacite_record)
        url = f"{self.base_url}dois/{self.sample.igsn}"
        response = requests.put(url, auth=(self._login, self._pswd), headers={"Content-Type": "application/vnd.api+json;charset=UTF-8"}, data=post_data)
        return response

    # set visibility to hidden
    def deactivate_igsn(self):
        post_data = self._deactivate_json(self.sample.igsn)
        url = f"{self.base_url}dois/{self.sample.igsn}"
        response = requests.put(url, auth=(self._login, self._pswd), headers={"Content-Type": "application/vnd.api+json;charset=UTF-8"}, data=post_data)
        return response

    def _assemble_json(self, sample: Sample, existing_datacite_record = None):
        igsn_split = sample.igsn.split('/')
        igsn_suffix = igsn_split[-1]
        doi_prefix = igsn_split[0]

        creator_array = []

        registrant_orcid = None
        if sample.cur_registrant.orcid:
            registrant_orcid = {
                "schemeUri": "https://orcid.org",
                "nameIdentifier": "https://orcid.org/" + sample.cur_registrant.orcid,
                "nameIdentifierScheme": "ORCID"
            }
        registrant_creator_object = {
            "nameType": "Personal",
            "nameIdentifiers": [registrant_orcid] if registrant_orcid else [],
            "name": f"{sample.cur_registrant.lname}, {sample.cur_registrant.fname}",
            "givenName": sample.cur_registrant.fname,
            "familyName": sample.cur_registrant.lname,
        }
        creator_array.append(registrant_creator_object)

        # Previous creator mapping
        # if sample.orig_owner.orcid:
        #     orcid_array = {
        #     "schemeUri": "https://orcid.org",
        #     "nameIdentifier": sample.orig_owner.orcid,
        #     "nameIdentifierScheme": "ORCID"
        #     } 
        # else:
        #     orcid_array = {}

        # if sample.collector and sample.collector.lower() != 'curator':
        #     creator_array = [
        #         {"name": sample.collector}
        #     ]
        # else :
        #     if sample.orig_owner:
        #         creator_array = [
        #             {
        #                 "nameIdentifiers": [orcid_array],
        #                 "name": f"{sample.orig_owner.lname}, {sample.orig_owner.fname}",
        #                 "givenName": sample.orig_owner.fname,
        #                 "familyName": sample.orig_owner.lname,
        #             }
        #         ]
        #     elif sample.group_owner:
        #         creator_array = [
        #             {"name": sample.group_owner.display_name}
        #         ]

        last_updated = sample.last_update_date.strftime('%Y-%m-%d')
        dates_array = [{"date": last_updated, "dateType": "Updated"}]

        if sample.collection_start_date:
            dates_array.append({
                "date": sample.collection_start_date.strftime('%Y-%m-%d'), 
                "dateType": "Collected"
            })

        related_identifiers = []
        alternate_identifiers = []

        if existing_datacite_record and existing_datacite_record['attributes']['relatedIdentifiers']:
            for identifier in existing_datacite_record['attributes']['relatedIdentifiers']:
                if identifier['relationType'] == 'IsIdenticalTo':
                    related_identifiers.append(identifier)

        if sample.origin_sample:
            related_identifiers.append({
                "relatedIdentifier": sample.origin_sample.igsn,
                "relatedIdentifierType": "IGSN",
                "relationType": "isPartOf"
            })

        if sample.publication_urls.exists():
            for url in sample.publication_urls.all():
                if url.url_type == 'regular URL':
                    identifier_type = 'URL'
                elif url.url_type == 'DOI':
                    identifier_type = 'DOI'

                related_identifiers.append({
                    "relatedIdentifier": url.url,
                    "relatedIdentifierType": identifier_type,
                    "relationType": "isReferencedBy"
                })

        if sample.other_names.exists():
            for name in sample.other_names.all():
                alternate_identifiers.append({
                    "alternateIdentifierType": "Local",
                    "alternateIdentifier": name.name
                })

        if existing_datacite_record and existing_datacite_record['attributes']['alternateIdentifiers']:
            for identifier in existing_datacite_record['attributes']['alternateIdentifiers']:
                if identifier['alternateIdentifierType'] == 'IGSN':
                    alternate_identifiers.append(identifier)

        geo_locations = []
        country = None
        if sample.country:
            country = sample.country.name
        geo_fields = [
            getattr(sample, 'locality', ''),
            country,
            getattr(sample, 'city', ''),
            getattr(sample, 'state', ''),
            getattr(sample, 'province', ''),
            getattr(sample, 'county', ''),
        ]
        geo_place = ' '.join(filter(None, geo_fields))
        geo_point = None
        if sample.longitude and sample.latitude:
            geo_point = {
                "pointLongitude": sample.longitude,
                "pointLatitude": sample.latitude
            }
        geo_location = {}
        if geo_point:
            geo_location['geoLocationPoint'] = geo_point
        if geo_place.strip() != '':
            geo_location['geoLocationPlace'] = geo_place

        geo_locations.append(geo_location)

        subjects = []
        subjects.append({
            "subject": sample.sample_type.name
        })

        if sample.geological_age:
            subjects.append({
                "subject": sample.geological_age
            })


        event_type = "publish" if not self.test_mode else ""

        if sample.classification and sample.top_level_classification:
            material = sample.classification.name+'>'+sample.top_level_classification.name
        elif sample.classification:
            material = sample.classification.name
        elif sample.top_level_classification:
            material = sample.top_level_classification.name
        else:
            material = None

        title = sample.name + ' ' + sample.sample_type.name
        if material:
            title += ' ' + material
            subjects.append({
                "subject": material
            })
        if sample.field_name:
            title += ' ' + sample.field_name

        contributor_array = []
        if sample.current_archive:
            contributor_array.append({
                "name": sample.current_archive,
                "nameType": "Organizational",
                "contributorType": "HostingInstitution"
            })

        data = {
            "data": {
                "type": "dois",
                "id": sample.igsn,
                "attributes": {
                    "event": event_type,
                    "doi": sample.igsn,
                    "relatedIdentifiers": related_identifiers,
                    "alternateIdentifiers": alternate_identifiers,
                    "types": {
                        "resourceType": sample.sample_type.name,
                        "resourceTypeGeneral": "PhysicalObject"
                    },
                    "creators": creator_array,
                    "contributors": contributor_array,
                    "titles": [
                        {
                            "title": title
                        }
                    ],
                    "publisher": "SESAR",
                    "publicationYear": sample.publish_date.year,
                    "url": f"https://app.geosamples.org/sample/igsn/{sample.igsn}",
                    "dates": dates_array,
                    "subjects": subjects,
                    "geoLocations": geo_locations
                }
            }
        }
        return json.dumps(data)

    def _deactivate_json(self, igsn):
        data = {
            "data": {
                "type": "dois",
                "id": igsn,
                "attributes": {
                    "event": "hide",
                    "doi": igsn
                }
            }
        }
        return json.dumps(data)
