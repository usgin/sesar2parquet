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
        self._login_lookup = self._parse_env_string(os.getenv('DATACITE_LOGIN'))
        self._password_lookup = self._parse_env_string(os.getenv('DATACITE_PASSWORD'))
        self._login, self._pswd = self._get_credentials(sample.igsn)

    def _parse_env_string(self, env_string):
        """Helper method to parse login and password environment variables"""
        lookup = {}
        for entry in env_string.split("|"):
            key, value = entry.split(",")
            lookup[key] = value
        return lookup

    def _get_credentials(self, igsn):
        """Retrieve login and password for the given IGSN prefix"""
        prefix = igsn.split("/")[0] + "/"
        return self._login_lookup.get(prefix), self._password_lookup.get(prefix)

    # check if igsn is registered with Datacite
    def igsn_exists(self):
        url = f"{self.base_url}dois/{self.sample.igsn}"
        response = requests.get(url, auth=(self._login, self._pswd))
        return response

    # register a new igsn with Datacite
    def register_igsn(self):
        post_data = self._assemble_json(False, self.sample)
        url = f"{self.base_url}dois/"
        response = requests.post(url, auth=(self._login, self._pswd), headers={"Content-Type": "application/vnd.api+json;charset=UTF-8"}, data=post_data)
        return response

    # update existing igsn metadata
    def update_igsn(self):
        post_data = self._assemble_json(False, self.sample)
        url = f"{self.base_url}dois/{self.sample.igsn}"
        response = requests.put(url, auth=(self._login, self._pswd), headers={"Content-Type": "application/vnd.api+json;charset=UTF-8"}, data=post_data)
        return response

    # set visibility to hidden
    def deactivate_igsn(self):
        post_data = self._deactivate_json(self.sample.igsn)
        url = f"{self.base_url}dois/{self.sample.igsn}"
        response = requests.put(url, auth=(self._login, self._pswd), headers={"Content-Type": "application/vnd.api+json;charset=UTF-8"}, data=post_data)
        return response

    def _assemble_json(self, is_reregistration, sample: Sample):
        igsn_split = sample.igsn.split('/')
        igsn_suffix = igsn_split[-1]
        doi_prefix = igsn_split[0]

        if sample.orig_owner.orcid:
            orcid_array = {
            "schemeUri": "https://orcid.org",
            "nameIdentifier": sample.orig_owner.orcid,
            "nameIdentifierScheme": "ORCID"
            } 
        else:
            orcid_array = {}

        if sample.collector and sample.collector.lower() != 'curator':
            creator_array = [
                {"name": sample.collector}
            ]
        else :
            if sample.orig_owner:
                creator_array = [
                    {
                        "nameIdentifiers": [orcid_array],
                        "name": f"{sample.orig_owner.lname}, {sample.orig_owner.fname}",
                        "givenName": sample.orig_owner.fname,
                        "familyName": sample.orig_owner.lname,
                    }
                ]
            elif sample.group_owner:
                creator_array = [
                    {"name": sample.group_owner.display_name}
                ]

        last_updated = sample.last_update_date.strftime('%Y-%m-%d')
        dates_array = [{"date": last_updated, "dateType": "Updated"}]

        identifier = sample.igsn
        related_identifiers = []
        if is_reregistration:
            related_identifiers = [{
                "relatedIdentifier": f"10273/{igsn_suffix}",
                "relatedIdentifierType": "IGSN",
                "relationType": "IsIdenticalTo"
            }]
            identifier = f"10273/{igsn_suffix}"

        event_type = "publish" if not self.test_mode else ""

        data = {
            "data": {
                "type": "dois",
                "id": sample.igsn,
                "attributes": {
                    "event": event_type,
                    "doi": sample.igsn,
                    "identifiers": [
                        {"identifier": identifier, "identifierType": "IGSN"}
                    ],
                    "relatedIdentifiers": related_identifiers,
                    "types": {
                        "resourceType": sample.sample_type.name,
                        "resourceTypeGeneral": "PhysicalObject"
                    },
                    "creators": creator_array,
                    "titles": [{"lang": "en", "title": sample.name}],
                    "publisher": "SESAR",
                    "publicationYear": sample.publish_date.year,
                    "url": f"https://app.geosamples.org/sample/igsn/{sample.igsn}",
                    "dates": dates_array
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
