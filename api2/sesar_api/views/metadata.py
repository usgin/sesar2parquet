from django.shortcuts import render
from django.utils.timezone import now

from sesar_api.models import *

def getSampleItems(data):
    sample_id = data.sample_id
    print(f"sample_id: {sample_id}")
    sampleitems = {}
    try:
        altnames = SampleAdditionalName.objects.get(sample=sample_id)
        print(f"altnames: {altnames}")
    except:
        altnames = None
    sampleitems['altnames'] = altnames

    parents = RelatedResource.objects.all()
    parents = parents.filter(relation_type=1)
    try:
        parent = parents.filter(sample=sample_id)
        sampleitems['parent'] = parent[0]
        parent_id = parent[0].related_sesar_sample.sample_id
        print(f"parent: {parent_id}")
    except:
        print("parent not found")
        sampleitems['parent'] = None



    #find siblings and child samples
    #siblings have same parent
    try:
        siblings = parents.filter(related_sesar_sample=parent_id)
        siblings = siblings.exclude(sample=sample_id)
        print(f"siblings: {siblings}")
    except:
        print("siblings not found")
        siblings = None
    sampleitems['siblings'] = siblings

    # children have sample_id as parent
    try:
        children = parents.filter(related_sesar_sample=sample_id)
        #print(f"Children: {children}")
        #print(f"a child: {children[0].sample.igsn}")
    except:
        print("children not found")
        children = None
    sampleitems['children'] = children

    try:
        coordinates = GeospatialLocation.objects.get(sample=sample_id)
    except:
        print("no alt coordinates found")
        coordinates = None
    sampleitems['coordinates'] = coordinates

    try:
        materials = SampleMaterial.objects.all()
        materials = materials.filter(sample=sample_id)
        sampleitems['materials'] = materials
    except:
        materials = None



    try:
        resp_parties = RelatedSampleAgent.objects.all()
        resp_parties = resp_parties.filter(sample=sample_id)
        print(f"resp_parties: {resp_parties}")
    except:
        print("no responsible parties found")
        resp_parties = None

    try:
        current_archive = resp_parties.filter(relation_type=3)[0]
    except:
        current_archive = None
    sampleitems['current_archive'] = current_archive

    if resp_parties:
        resp_parties = resp_parties.exclude(relation_type=3)  #resp_parties has all agent_roles except current archive.
    sampleitems['resp_parties'] = resp_parties

    sesar_users = SesarUser.objects.all()
    try:
        theid = data.cur_registrant.sesar_user
        registrant = sesar_users.filter(sesar_user=theid)[0]
    except:
        print("no sesar users found")
        registrant = None
    sampleitems['registrant'] = registrant

    try:
        owner = sesar_users.filter(sesar_user=data.cur_owner.sesar_user)[0]
    except:
        print("no sesar users found")
        owner = None
    sampleitems['owner'] = owner

    try:
        links = SamplePublicationUrl.objects.all()
        links = links.filter(sample=sample_id)
    except:
        print("no links found")
        links = None
    sampleitems['links'] = links

    try:
        docs = SampleDoc.objects.all()
        docs = docs.filter(sample=sample_id)
    except:
        print("no docs found")
        docs = None
    sampleitems['docs'] = docs

# set up collection description for platform,launch etcl

    collectionDesc = ''
    if data.collection_method:
        collectionDesc = collectionDesc + 'method:' + data.collection_method.label
    if data.collection_method_detail:
        collectionDesc = collectionDesc + ', ' + data.collection_method_detail + '. '
    if data.platform:
        collectionDesc = collectionDesc + ' Platform: ' + data.platform.label
    if data.launch_platform:
        collectionDesc = collectionDesc + ' Launch Platform: ' + data.launch_platform.label
    if data.launch_label:
        collectionDesc = collectionDesc + ' Launch: ' + data.launch_label
    sampleitems['collectionDesc'] = collectionDesc
    print(f'collectionDesc: {collectionDesc}')

    verticalpos = ""
    if data.elevation:
        verticalpos = verticalpos + str(data.elevation)
    if data.elevation_uom:
        verticalpos = verticalpos + " UOM: " + data.elevation_uom

    if data.depth_min or data.depth_max:
        if data.depth_min == data.depth_max :
            verticalpos = " Depth: " + str(data.depth_min)
        elif data.depth_min and data.depth_max:
            verticalpos = verticalpos + "Depth range: " + str(data.depth_min) + " to " + str(data.depth_max)
        elif data.depth_min:
            verticalpos = verticalpos + "Depth minimum: " + str(data.depth_min)
        elif data.depth_max:
            verticalpos = verticalpos + "Depth maximum: " + str(data.depth_min)
    if data.depth_uom:
        verticalpos = verticalpos + " UOM: " + data.depth_uom
    if data.depth_spatial_ref:
        verticalpos = verticalpos + " Datum: " + data.depth_spatial_ref

    sampleitems['verticalpos'] = verticalpos
    print(f'verticalpos: {verticalpos}')

    # set up sample description
    samdesc = ""
    if data.sample_description:
        samdesc = samdesc + data.sample_description

    if data.size:
        samdesc = samdesc + ". Sample size: " + data.size
    # if have start and endpoints for lat and long
    if data.latitude and data.latitude_end:
        samdesc = samdesc + ". Latitude from " + str(data.latitude) + " to " + str(data.latitude_end)
    if data.longitude and data.longitude_end:
        samdesc = samdesc + ", Longitude from " + str(data.longitude) + " to " + str(data.longitude_end)
    # if there are UTM coordinates in addition to lat and long
    if coordinates:
        samdesc = samdesc + ". UTM coordinates: Easting " + str(coordinates.coordinate_1) + \
                  " Northing " + str(coordinates.coordinate_2) + \
                    " Spatial reference: " +  coordinates.spatial_reference_system
    if data.geologic_age_verbatim:
        samdesc = samdesc + ". Age: " + data.geologic_age_verbatim
    # add numeric ages
    if data.numeric_age_min and data.numeric_age_max:
        samdesc = samdesc + ". Age between " + str(data.numeric_age_min) + " and " + str(data.numeric_age_max)
    elif data.numeric_age_min:
        samdesc = samdesc + ". Minimum age " + str(data.numeric_age_min)
    elif data.numeric_age_max:
        samdesc = samdesc + ". Maximum age " + str(data.numeric_age_max)
    if (data.numeric_age_min or data.numeric_age_max) and data.numeric_age_unit:
        samdesc = samdesc + " Age units " + data.numeric_age_unit
    if data.age_qualifier:
        samdesc = samdesc + ", Age qualifier: " + data.age_qualifier

    sampleitems['samdesc'] = samdesc
    print(f'verticalpos: {samdesc}')

    return sampleitems

def DisplaySampleByIGSNView(request):
    igsn = request.GET.get('igsn')
    sample = Sample.objects.get(igsn=igsn, publish_date__lt=now())
    sampleitems = getSampleItems(sample)

    return render(request,'../templates/sample.html',{"sample":sample,
                                                       "sampleitems":sampleitems})