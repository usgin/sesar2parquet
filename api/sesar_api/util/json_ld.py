from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
import datetime
from decimal import Decimal, ROUND_HALF_UP
from sesar_api.models import Sample


def format_geo_data(latitude, longitude, latitude_end=None, longitude_end=None, elevation=None, elevation_unit=None):
    """
    Generates spatial coverage (spc) data in the JSON-LD format.
    """
    spc = {"@type": "Place"}
    geos = []

    # Formatter function for numbers with six decimal places
    def format_number(value):
        return f"{Decimal(value).quantize(Decimal('.000001'), rounding=ROUND_HALF_UP)}"

    if latitude_end is not None and longitude_end is not None:
        # Line geometry
        geo_data = {"@type": "GeoShape"}
        lat1, lon1 = format_number(latitude), format_number(longitude)
        lat2, lon2 = format_number(latitude_end), format_number(longitude_end)
        geo_data["Line"] = f"{lat1} {lon1},{lat2} {lon2}"
        if elevation is not None:
            geo_data["elevation"] = f"{format_number(elevation)} {elevation_unit or ''}".strip()
        geos.append(geo_data)
    elif latitude is not None and longitude is not None:
        # Point geometry
        geo_data = {"@type": "GeoCoordinates"}
        geo_data["latitude"] = format_number(latitude)
        geo_data["longitude"] = format_number(longitude)
        if elevation is not None:
            geo_data["elevation"] = f"{format_number(elevation)} {elevation_unit or ''}".strip()
        geos.append(geo_data)

    if geos:
        spc["geo"] = geos
        return spc
    return None


def format_collection_dates(collection_start_date, collection_end_date, collection_date_precision):
    """
    Format collection start and end dates based on precision.
    """
    # Define the default date format
    pattern = "%Y-%m-%d"  # Default to 'day' format

    # Determine the date pattern based on precision
    if collection_date_precision:
        collection_date_precision = collection_date_precision.lower()
        if collection_date_precision == "time":
            pattern = "%Y-%m-%d %H:%M:%S"
        elif collection_date_precision == "year":
            pattern = "%Y"
        elif collection_date_precision == "month":
            pattern = "%Y-%m"
        elif collection_date_precision == "day":
            pattern = "%Y-%m-%d"

    # Format the dates if they exist
    formatted_start_date = (
        collection_start_date.strftime(pattern) if collection_start_date else None
    )
    formatted_end_date = (
        collection_end_date.strftime(pattern) if collection_end_date else None
    )

    return formatted_start_date, formatted_end_date


def generate_description(sample):
    # check if sample is deactivated
    if sample.archive_date and sample.archive_date <= timezone.now():
        description = {
            "description": "The sample is deleted",
            "igsnPrefix": sample.igsn_prefix.user_code
        }
        return description
    # check if sample is private (not published)
    elif sample.publish_date > datetime.datetime.now():
        description = {
            "description": "Sample medata is private",
            "igsnPrefix": sample.igsn_prefix.user_code
        }
        return description

    # build material string
    if sample.top_level_classification:
        if sample.classification:
            material = sample.classification.name+'>'+sample.top_level_classification.name
        else:
            material = sample.top_level_classification.name
    else:
        material = None

    # format collection dates based on precision
    formatted_collection_start, formatted_collection_end = format_collection_dates(
        sample.collection_start_date, sample.collection_end_date, sample.collection_date_precision
    )

    children_samples = list(Sample.objects.filter(origin_sample=sample).values_list('igsn', flat=True))
    if sample.origin_sample:
        sibling_samples = list(Sample.objects.filter(origin_sample=sample.origin_sample).values_list('igsn', flat=True))
    else:
        sibling_samples = []

    other_names = list(sample.other_names.values_list('name', flat=True))

    publication_urls = []
    for url in sample.publication_urls.all():
        publication_urls.append({
            "description": url.description,
            "url": url.url,
            "urlType": url.url_type,
        })

    documents = []
    for document in sample.sample_docs.all():
        documents.append({
            "fileName": document.file_name,
            "urlToFile": "https://app.geosamples.org/uploads/"+document.path_to_file,
            "primaryImage": document.primary_image
        })

    contributors = []
    if sample.cur_owner:
        contributors.append({
            "contributor": [
            {
                "@type": "Person",
                "name": sample.cur_owner.fname + " " + sample.cur_owner.lname,
                "givenName": sample.cur_owner.fname,
                "familyName": sample.cur_owner.lname
            }
            ],
            "@type": "Role",
            "roleName": "Sample Owner"
        })
    contributors.append({
        "contributor": [
        {
            "@type": "Person",
            "name": sample.cur_registrant.fname + " " + sample.cur_registrant.lname,
            "givenName": sample.cur_registrant.fname,
            "familyName": sample.cur_registrant.lname
        }
        ],
        "@type": "Role",
        "roleName": "Sample Registrant"
    })
    if sample.current_archive_contact:
        contributors.append({
            "contributor": [
            {
                "@type": "Person",
                "name": sample.current_archive_contact,
            }
            ],
            "@type": "Role",
            "roleName": "Sample Archive Contact"
        })

    supplemental_data = {
        "classificationComment": sample.classification_comment,
        "ageMin": sample.age_min,
        "ageMax": sample.age_max,
        "ageUnit": sample.age_unit,
        "city": sample.city,
        "country": sample.country.name if sample.country else None,
        "county": sample.county,
        "province": sample.province,
        "cruiseFieldPrgrm": sample.cruise_field_prgrm,
        "currentArchive": sample.current_archive,
        "currentArchiveContact": sample.current_archive_contact,
        "originalArchive": sample.original_archive,
        "originalArchiveContact": sample.original_archive_contact,
        "depthMin": sample.depth_min,
        "depthMax": sample.depth_max,
        "depthScale": sample.depth_scale,
        "easting": sample.easting,
        "northing": sample.northing,
        "verticalDatum": sample.vertical_datum,
        "zone": sample.zone,
        "elevation": sample.elevation,
        "elevationEnd": sample.elevation_end,
        "elevationUnit": sample.elevation_unit,
        "externalParentName": sample.external_parent_name,
        "externalParentSampleType": sample.external_parent_sample_type.name if sample.external_parent_sample_type else None,
        "externalSampleId": sample.external_sample_id,
        "fieldName": sample.field_name,
        "geologicalAge": sample.geological_age,
        "geologicalUnit": sample.geological_unit,
        "launchId": sample.launch_id,
        "launchPlatformName": sample.launch_platform_name,
        "launchType": sample.launch_type.name if sample.launch_type else None,
        "locality": sample.locality,
        "localityDescription": sample.locality_description,
        "navigationType": sample.nav_type.name if sample.nav_type else None,
        "platformDescr": sample.platform_descr,
        "platformName": sample.platform_name,
        "platformType": sample.platform_type,
        "launchPlatformName": sample.launch_platform_name,
        "primaryLocationName": sample.primary_location_name,
        "primaryLocationType": sample.primary_location_type,
        "sampleComment": sample.sample_comment,
        "sampleUnit": sample.sample_unit,
        "size": sample.size,
        "sizeUnit": sample.size_unit,
        "purpose": sample.purpose,
        "childIGSN": children_samples,
        "siblingIGSN": sibling_samples,
        "otherName": other_names,
        "publicationUrl": publication_urls,
        "document": documents
    }
    supplemental_data = {k: v for k, v in supplemental_data.items() if v is not None}

    description = {
        "sampleName": sample.name,
        "igsnPrefix": sample.igsn_prefix.user_code,
        "sampleType": sample.sample_type.name if sample.sample_type else None,
        "contributors": contributors,
        "material":  material,
        "collectionStartDate": formatted_collection_start,
        "collectionEndDate": formatted_collection_end,
        "collectionDatePrecision": sample.collection_date_precision,
        "collectionMethod": sample.collection_method,
        "collectionMethodDescr": sample.collection_method_descr,
        "collector": sample.collector,
        "collectorDetail": sample.collector_detail,
        "description": sample.description,
        "parentIdentifier": sample.origin_sample.igsn if sample.origin_sample else None,
        "supplementMetadata": supplemental_data,
        "spatialCoverage": format_geo_data(sample.latitude, sample.longitude, sample.latitude_end, sample.longitude_end, sample.elevation, sample.elevation_unit),
        "publisher": {
            "contactPoint": {
                "@type": "ContactPoint",
                "name": "Information Desk",
                "contactType": "Customer Service",
                "email": "info@geosamples.org",
                "url": "https://www.geosamples.org/contact/"
            },
            "@type": "Organization",
            "name": "EarthChem",
            "@id": "https://www.geosamples.org",
            "url": "https://www.geosamples.org"
        },
        "log": [
            {
                "type": "registered",
                "timestamp": sample.registration_date
            },
            {
                "type": "published",
                "timestamp": sample.publish_date
            },
            {
                "type": "lastUpdated",
                "timestamp": sample.last_update_date
            }
    ],
    }
    description = {k: v for k, v in description.items() if v is not None}
    return description


def generate_sample_jsonld(sample):
    """
    Generate JSON-LD for a given Sample instance.
    
    :param sample: A Sample instance.
    :return: JSON-LD representation as a dictionary.
    """
    jsonld = {
        "@context": "https://raw.githubusercontent.com/IGSN/igsn-json/master/schema.igsn.org/json/registration/v0.1/context.jsonld",
        "@id": f"https://data.geosamples.org/sample/igsn/{sample.igsn}",
        "igsn": sample.igsn,
        "registrant": {
            "name": "IEDA",
            "identifiers": {
                "kind": "uri",
                "id": "https://www.geosamples.org"
            }
        },
        "description": generate_description(sample)
    }
    return jsonld