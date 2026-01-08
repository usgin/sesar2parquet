from datetime import datetime
import logging
import numbers
import re
import time
import sys
import psycopg2
import pandas

#  Main execution sequence starts after line 2579.  Find 'def main'

# Global logger
LOGGER = logging.getLogger('sesarMigration')


# utility functions
def get_legacyConnection() -> psycopg2.extensions.connection:
    try:
        return psycopg2.connect(
            database="sesardb20241209",
            user="postgres",
            password="smrpostgis",
            host="127.0.0.1",
            port=5432,
        )
    except Exception as e:
        LOGGER.info(f'legacy db connection problem {repr(e)}')
        return None


def get_2024Connection() -> psycopg2.extensions.connection:
    try:
        return psycopg2.connect(
            database="sesar202512",
            user="postgres",
            password="smrpostgis",
            host="127.0.0.1",
            port=5432,
        )
    except Exception as e:
        LOGGER.info(f'2025db connection problem {repr(e)}')
        return None


def cleanKey(inkey: str) -> str:
    #  regular expression to replace all non-alphanumeric characters (\W) with an period ('.')
    return re.sub(r'\W+', '', inkey).lower()[:254]


# def checkDate(adate):
#     testDate = pandas.to_datetime(adate, errors='coerce')
#
#     return datetime


def executeQuery(conn, querystring):
    # CREATE A CURSOR USING THE CONNECTION OBJECT
    curr = conn.cursor()
    # EXECUTE THE SQL QUERY
    curr.execute(querystring)
    # FETCH ALL THE ROWS FROM THE CURSOR
    data = curr.fetchall()
    curr.close()
    return data


def getFields(conn, tableName):
    #  get field names for table
    fieldsquery = "SELECT column_name,ordinal_position " \
                  "FROM information_schema.columns " + \
                  "WHERE table_schema = 'public' AND table_name = '" + \
                  tableName + "' ORDER BY ordinal_position"
    LOGGER.debug(f'getFields query: {fieldsquery}')
    fields = executeQuery(conn, fieldsquery)

    fieldlist = []
    for row in fields:
        fieldlist.append(row[0])
    return fieldlist


def getPrimaryKey(conn, tableName):
    pkquery = "SELECT  kcu.column_name FROM information_schema.table_constraints tc " + \
              "JOIN information_schema.key_column_usage kcu  ON tc.constraint_name = kcu.constraint_name " + \
              "AND tc.table_schema = kcu.table_schema WHERE tc.constraint_type = 'PRIMARY KEY' " + \
              "AND tc.table_name = '" + tableName + "'"
    try:
        result = executeQuery(conn, pkquery)
        pk = result[0]
    except Exception as e:
        LOGGER.info(f'PRIMARY KEY query fail, table {tableName}')
        return None
    return pk


def pk_lkup(conn):
    """function to create dictionary with {tablename:primaryKeyFieldName} entries
            input is a database connection object, returns a dictionary"""
    cursor = conn.cursor()
    lkup = {}
    try:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public';   """)
        # Fetch all table names
        tables = cursor.fetchall()
        # Convert list of tuples to list of strings
        table_list = [table[0] for table in tables]
    except Exception as error:
        LOGGER.info(f"tablelist Error: {error}")
        if cursor:
            cursor.close()
        return {}

    for tablename in table_list:
        apk = getPrimaryKey(conn, tablename)
        if apk is not None:
            lkup[tablename] = getPrimaryKey(conn, tablename)[0]
        else:
            LOGGER.info(f"Primary key for {tablename} not found")
    if cursor:
        cursor.close()
    return lkup


def truncateTable(conn, tableName, cascade=False):
    # this is tricky because of foreign key constraints
    # Truncate table sample RESTART IDENTITY  CASCADE
    if cascade:
        pkquery = "TRUNCATE table " + tableName + " RESTART IDENTITY  CASCADE"
    else:
        pkquery = "TRUNCATE table " + tableName + " RESTART IDENTITY "
    curr = conn.cursor()
    try:
        curr.execute(pkquery)
    #        conn.commit()
    except Exception as e:
        LOGGER.info(f'truncate fail: {repr(pkquery)}, exception: {repr(e)}')
        curr.close()
        return 0
    print(tableName + " truncated")
    curr.close()
    return 1


def cleanDb(conn, tables, cascade=False):
    """ takes a list of tables, and runs SQL truncate on each
        if 'cascade' is true, truncate cascades to delete all tables with
        FK relations to the table being truncated.  This can cause
        unexpected results--take care.
    """
    for atable in tables:
        try:
            result = truncateTable(conn, atable, cascade)
            print('truncate: ', atable)
        except Exception as e:
            LOGGER.info('cleanDb, exception: %s', repr(e))
            return 0
    return 1


def insertRow(cursor, newTableName, newRow, pkl={}):
    """ Insert content of newRow dictionary  into newTableName using
    database connection specified by cursor. if pkl contains the
    Primary Key lookup dictionary (which is supposed to be a global, but
    doesn't work that way for some reason), if the insert fails because the pk is already there
    will do an update instead of insert.
    newRow is a dictionary of {fieldname:value} paires to insert into the table
    """

    thevalues = list(newRow.values())
    flkeys = list(newRow.keys())
    insertvalues = '('
    fields = '  ('
    fc = 0
    for fc in range(0, len(thevalues)):
        val = thevalues[fc]
        if val == 'blank' or val is None:
            continue
        if isinstance(val, str):
            # if '\'' in val:
            #    LOGGER.info(f'string with quotes:{val}, the values {thevalues}')
            # strings have to be quoted in the sql query
            val = val.replace('\'', '\'\'')  # escape internal quotes
            val = '\'' + val + '\''
        elif isinstance(val, datetime):
            # format date as string
            val = '\'' + f'{val:%Y-%m-%d %H:%M:%S %z}' + '\''
        else:
            val = str(val)

        fields = fields + flkeys[fc] + ', '
        insertvalues = insertvalues + val + ', '

    fieldsval = fields[:-2] + ') VALUES {} '

    #    print(insertvalues[:-2] + ')')
    sql2 = 'insert into ' + newTableName + fieldsval.format(
        insertvalues[:-2] + ')')

    if len(pkl) > 0:
        pk = pkl[newTableName]
        updatepart = ' on conflict (' + pk + ') Do update set ' + (fields[:-2] + ') = {}').format(
            insertvalues[:-2] + ')')
        sql2 = sql2 + updatepart

    #    print('the query: ', sql2)
    try:
        cursor.execute(sql2)
    except Exception as e:
        LOGGER.info(f'InsertRow, Cursor execute fail. sql: {sql2}')
        LOGGER.info('insertRow exception: %s', repr(e))
        return 0
    return 1


# def construct_query(table_name, field_name, column_name, text_value):
#     """Constructs an SQL query string with a text value criteria."""
#
#     # Sanitize the text value to prevent SQL injection
#     text_value = text_value.replace("'", "''")
#
#     query = f"SELECT {field_name} FROM {table_name} WHERE {column_name} = '{text_value}'"
#     return query


def insert_POC(thisPOC, relType, timestamp, sample_id):
    """ generates a newRow dictionary to populate the related_sample_agent table
    create function because requires logic to determine how to handle individual
    vs. institution.
    """
    newRow = {}
    if thisPOC['individual_id']:
        newRow['related_agent_id'] = thisPOC['individual_id']
        newRow['agent_type'] = 'Individual'
    elif thisPOC['institution_id']:
        newRow['related_agent_id'] = thisPOC['institution_id']
        newRow['agent_type'] = 'Institution'

    if thisPOC['individual_id']:
        newRow['individual_id'] = thisPOC['individual_id']
    if thisPOC['institution_id']:
        newRow['institution_id'] = thisPOC['institution_id']

    aLabel = (thisPOC['archive'] + '. ' + thisPOC['poc']).replace('\'', '\'\'')
    newRow['label'] = aLabel[:50]
    newRow['description'] = 'verbatim name: ' + aLabel
    newRow['activate_date'] = timestamp
    newRow['sample_id'] = sample_id
    newRow['relation_type_id'] = relType

    return newRow


def insert_related_agent_by_name(name, sample_id, reltype, timestamp):
    """
    generate newRow dictionary for related_sample_agent table;
    handles individual vs. institution, based on field from
    agent lookup table.
    """
    agentKey = cleanKey(name)
    try:
        agentToInsert = AGENT_ID_LKUP[agentKey]
    except:
        return ''

    newRow = {}
    newRow['related_agent_id'] = agentToInsert['agent_id']

    if agentToInsert['source'] == 'individual':
        newRow['agent_type'] = 'Individual'
        newRow['individual_id'] = agentToInsert['agent_id']
    else:
        newRow['agent_type'] = 'Institution'
        newRow['institution_id'] = agentToInsert['agent_id']

    newRow['label'] = agentToInsert['prefName'].replace('\'', '\'\'')[:200]
    newRow['description'] = 'verbatim name: ' + agentToInsert['label_verbatim'].replace('\'', '\'\'')
    newRow['activate_date'] = timestamp
    newRow['sample_id'] = sample_id
    newRow['relation_type_id'] = reltype
    return newRow


def is_number(value):
    try:
        result = type(value) in (int, float)
    except:
        result = False
    return result


##############################################################################
# GLOBALS

# init the lookup table objects as global variables
PK_LKUP = {}  # dictionary maps tables to PK for table
COUNTRY_LKUP = {}
COLLECTION_METHOD_LKUP = {}
SAMPLE_TYPE_LKUP = {}
LOCALITY_LKUP = {}
FEATURETYPE_LKUP = {}
INITIATIVE_LKUP = {}
PLATFORM_LKUP = {}
DATUM_LKUP = {}  # map verbatim strings defining elevation or depth datums to sesar_spatial_ref_sys ids
MATERIAL_LKUP = {}  # maps legacy classification_id to id in new material_type table.
GEOLOGIC_AGE_LKUP = {}
MULTI_COLLECTOR_LKUP = {} # maps the list of agents from legacy db (typically from collector) to list of individuals
                            # or institutions that will map in the agent lookup
AGENT_ID_LKUP = {}  # find by verbatim label
AGENT_NAME_LKUP = {}  # find by name
ARCHIVE_POC_LKUP = {}

SOURCE_BASE_FOLDER = 'MigrationNotes_LookupTables'
AFFILIATION_TYPE = SOURCE_BASE_FOLDER + '/Agent/affiliation_type.csv'
AGENTID_LOOKUP = SOURCE_BASE_FOLDER + '/agent/agentID_lookup.csv'
AGENT_ROLE_TYPE = SOURCE_BASE_FOLDER + '/Agent/agent_role_type.csv'
AGENTS_MAPPING = SOURCE_BASE_FOLDER + '/Agent/agentsMapping.xlsx'
ARCHIVE_POC_LOOKUP = SOURCE_BASE_FOLDER + '/Agent/ArchivePOC-Lookup.csv'
ALLOCATION_DISTINCT = SOURCE_BASE_FOLDER + '/LocationLocality/AllLocationDistinct-refine.xlsx'
CLASSIFICATION_MATERIAL_LOOKUP = SOURCE_BASE_FOLDER + '/Material/ClassificationMaterialLookup.csv'
COUNTRY_VOCABULARY = SOURCE_BASE_FOLDER + '/country_vocabulary.xlsx'
DEPTH_SCALE_UNIQUE = SOURCE_BASE_FOLDER + '/DepthElevation/Depth_Scale_unique.xlsx'
GEOLOGIC_AGE_LOOKUP = SOURCE_BASE_FOLDER + '/GeologicAge/geologic_age_lookup.xlsx'
GEOLOGIC_TIME_SCALE2020 = SOURCE_BASE_FOLDER + '/GeologicAge/GeologicTimeScale2020.xlsx'
INDIVIDUALS_VOCAB = SOURCE_BASE_FOLDER + '/Agent/individualsVocab.csv'
INITIATIVE_LOOKUP = SOURCE_BASE_FOLDER + '/PlatformInitiative/InitiativeLookup.csv'
INITIATIVE_TYPE_VOCAB = SOURCE_BASE_FOLDER + '/PlatformInitiative/InitiativeTypeVocab.xlsx'
INITIATIVE_VOCAB = SOURCE_BASE_FOLDER + '/PlatformInitiative/initiativeVocabulary.csv'
INSTITUTION_VOCAB = SOURCE_BASE_FOLDER + '/Agent/institutionVocab.csv'
LAUNCH_TYPE_VOCAB = SOURCE_BASE_FOLDER + '/PlatformInitiative/launch_type_vocab.xlsx'
LOCALITY_FEATURE_TYPE_COUNTRY = SOURCE_BASE_FOLDER + '/LocationLocality/locality-featuretype-countrylkup.csv'
LOCALITY_LOOKUP = SOURCE_BASE_FOLDER + '/LocationLocality/LocalityLookup.csv'
LOCATION_METHOD = SOURCE_BASE_FOLDER + '/location_method.xlsx'
MULTIPLE_COLLECTOR_LOOKUP = SOURCE_BASE_FOLDER + '/Agent/MultipleCollectorLookup.csv'
PLATFORM_LOOKUP = SOURCE_BASE_FOLDER + '/PlatformInitiative/PlatformLookup.xlsx'
PLATFORM_NAME_VOCAB = SOURCE_BASE_FOLDER + '/PlatformInitiative/platform_name_vocab.xlsx'
PLATFORM_TYPE_VOCAB = SOURCE_BASE_FOLDER + '/PlatformInitiative/platformType_vocab.xlsx'
RELATION_TYPE = SOURCE_BASE_FOLDER + '/relation_type.csv'
RESOURCE_TYPES = SOURCE_BASE_FOLDER + '/resourceTypes.xlsx'
SAMPLE_MATERIAL_ROLE = SOURCE_BASE_FOLDER + '/Material/SampleMaterialRole.xlsx'
SAMPLE_TYPE_VOCAB = SOURCE_BASE_FOLDER + '/SampleType/sample_type_vocab.csv'
SAMPLED_FEATURE_TYPE_VOCAB = SOURCE_BASE_FOLDER + '/LocationLocality/sampledFeatureTypeVocabulary.xlsx'
SAMPLING_METHOD_LOOKUP = SOURCE_BASE_FOLDER + '/SamplingMethods/Sampling_method_lookup.xlsx'
SAMPLING_METHOD_VOCAB = SOURCE_BASE_FOLDER + '/SamplingMethods/Sampling_method_vocab.xlsx'
SESAR_MATERIAL_TYPE_VOCAB = SOURCE_BASE_FOLDER + '/Material/SESAR_material_type_vocabulary.xlsx'
SESAR_SAMPLE_TYPE_MAPPING = SOURCE_BASE_FOLDER + '/SampleType/SESAR_SampleTypeMapping.xlsx'


# *******************************************************************
# ******************************************************************
# functions to load vocabularies and create lookup dataframes for use in the
#  data transformation routines.


def load_initiative_type(newDb):
    newTableName = "initiative_type"
    # get from excel workbook
    df = pandas.read_excel(INITIATIVE_TYPE_VOCAB,
                           na_filter=False)
    LOGGER.debug('initiative type columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['initiative_type_id'] = row['ID']
        newRow['label'] = row['Label']
        if len(row['notes']) > 0:
            newRow['description'] = row['notes']
        if len(row['source']) > 0:
            newRow['source'] = row['source']
        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug(f'load_initiative_type, rowNum: {rowNum}')

    newDb.commit()
    return 1


def load_affiliation_type(newDb):
    newTableName = "affiliation_type"
    # read vocabulary into dataframe
    df = pandas.read_csv(AFFILIATION_TYPE,
                         na_filter=False)
    LOGGER.debug('affiliation type columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['affiliation_type_id'] = row['affiliation_type_id']
        newRow['label'] = row['label']
        if len(row['description']) > 0:
            newRow['description'] = row['description']
        if len(row['source']) > 0:
            newRow['source'] = row['source']
        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    return 1


def load_agent_role_type(newDb):
    newTableName = "agent_role_type"
    # read vocabulary into dataframe
    df = pandas.read_csv(AGENT_ROLE_TYPE,
                         na_filter=False)
    LOGGER.debug('agent role type columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['agent_role_id'] = row['agent_role_id']
        newRow['label'] = row['label']
        if len(row['description']) > 0:
            newRow['description'] = row['description']
        if len(row['source']) > 0:
            newRow['source'] = row['source']
        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    return 1


def load_platform_type(newDb):
    newTableName = 'platform_type'
    # read vocabulary into dataframe
    df = pandas.read_excel(PLATFORM_TYPE_VOCAB,
                           sheet_name="platformtype",
                           na_filter=False)
    LOGGER.debug('platform type columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['platform_type_id'] = row['id']
        newRow['label'] = row['label']
        if len(row['notes']) > 0:
            newRow['description'] = row['notes']
        if len(row['source']) > 0:
            newRow['source'] = row['source']
        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    return 1


def load_launch_type(newDb):
    newTableName = 'launch_type'
    # read vocabulary into dataframe
    df = pandas.read_excel(LAUNCH_TYPE_VOCAB,
                           sheet_name="launch_type",
                           na_filter=False)
    logging.debug('launch type columns %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['launch_type_id'] = row['id']
        newRow['label'] = row['label']
        if len(row['notes']) > 0:
            newRow['description'] = row['notes']
        if len(row['source']) > 0:
            newRow['source'] = row['source']
        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_institution_type(newDb):
    newTableName = 'institution_type'
    # read vocabulary into dataframe
    df = pandas.read_excel(AGENTS_MAPPING, sheet_name="org_type",
                           na_filter=False)
    LOGGER.debug('institution columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['institution_type_id'] = row['institution_type_id']
        newRow['label'] = row['label']
        newRow['description'] = row['description']
        newRow['source'] = row['source']
        result = insertRow(cursor, newTableName, newRow)
        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)
    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_relation_type(newDb):
    newTableName = 'relation_type'
    # read vocabulary into dataframe
    df = pandas.read_csv(RELATION_TYPE,
                         na_filter=False)
    LOGGER.debug('relation type columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['relation_type_id'] = row['relation_type_id']
        newRow['label'] = row['label'].replace('\'', '\'\'')
        if len(row['description']) > 0:
            newRow['description'] = row['description'].replace('\'', '\'\'')
        newRow['source'] = row['source'].replace('\'', '\'\'')
        result = insertRow(cursor, newTableName, newRow)
        # rowNum = rowNum + 1
        # LOGGER.debug('rowNum: ', rowNum)
    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_resource_type(newDb):
    newTableName = 'resource_type'
    # read vocabulary into dataframe
    df = pandas.read_excel(RESOURCE_TYPES, sheet_name="resourceTypes",
                           na_filter=False)
    LOGGER.debug('resource type columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['resource_type_id'] = row['resource_type_id']
        newRow['label'] = row['label'].replace('\'', '\'\'')
        if len(row['description']) > 0:
            newRow['description'] = row['description'].replace('\'', '\'\'')
        newRow['source'] = row['source'].replace('\'', '\'\'')
        if row['broader_type_id']:
            newRow['broader_type_id'] = row['broader_type_id']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_location_method(newDb):
    # This is populated with vocabulary derived from uniq values in legacy nav_type
    newTableName = 'location_method'
    # read vocabulary into dataframe
    df = pandas.read_excel(LOCATION_METHOD, sheet_name="nav_type",
                           na_filter=False)
    logging.debug('location method %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['location_method_id'] = row['location_method_id']
        newRow['label'] = row['label']
        if len(row['description']) > 0:
            newRow['description'] = row['description']
        if len(row['source']) > 0:
            newRow['source'] = row['source']
        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_country(newDb):
    newTableName = 'country'
    # read vocabulary into dataframe
    df = pandas.read_excel(COUNTRY_VOCABULARY, sheet_name="countrySESARdump",
                           na_filter=False)
    LOGGER.debug('country columns %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['country_id'] = row['country_id']
        newRow['label'] = row['label']
        newRow['iso3166code'] = row['iso3166code']
        newRow['is_active'] = row['is_active']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug(f'load country rowNum: {rowNum}')
    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_sampling_method(newDb):
    newTableName = 'sampling_method'
    # read vocabulary into dataframe
    df = pandas.read_excel(SAMPLING_METHOD_VOCAB,
                           sheet_name="SamplingMethod",
                           na_filter=False)
    LOGGER.debug('sampling method columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['collection_method_id'] = row['collection_method_id']
        newRow['method_uri'] = row['method_uri']
        newRow['label'] = row['label']
        newRow['description'] = row['description']
        newRow['scheme_uri'] = 'https://w3id.org/sesar/samplingmethods/0.1/samplingmethods'
        newRow['source'] = row['source']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def get_locality_key(sample_rec):
    #
    # need to implement these EXCEl functions:
    # part one: = locality & primary_location_name & primary_location_type
    # Parttwo: = province & county & city & country_id
    # Part three: = IF(locality_description="NULL", "", locality_description) &
    #                     IF(ISERROR(FIND("Matched", location_description)),
    #                        IF(location_description="NULL", "", location_description), "")
    # part three is a little tricky - - don't include the long 'Matched by...'
    # explanations from smithsonian-- the result is in the locality_description; also don't
    # include NULL values.
    # FINALLY: concatenate and remove spaces and other unwanted characters with cleanKey function
    if sample_rec['locality'] == 'Salinian Block':
        found = 1
    p_one = sample_rec['locality'] + sample_rec['primary_location_name'] + sample_rec['primary_location_type']
    p_two = sample_rec['province'] + sample_rec['county'] + sample_rec['city'] + str(sample_rec['country_id'])
    frag1 = ''
    frag2 = ''
    if sample_rec['locality_description'] != 'NULL':
        frag1 = sample_rec['locality_description']
    if sample_rec['location_description'].find("Matched") == -1:
        if sample_rec['location_description'] != 'NULL':
            frag2 = sample_rec['location_description']
    p_three = frag1 + frag2
    p_three = p_three.replace('blank', '')
    localitykey = p_one + p_two + p_three
    #    localitykey = localitykey.replace("~", "").replace("#", "").replace("?", "").replace("*", "")
    #    localitykey = localitykey.replace("\"", "")

    teststring = localitykey.replace("blank", "")
    if teststring == '':
        localitykey = ''
    else:
        localitykey = localitykey.replace("blank", "NULL").replace(" ", "")
        # note the apparent space is a special character, not a regular space….
        # localitykey = localitykey[:254] cleanKey truncates the string
    localitykey = cleanKey(localitykey)
    return localitykey


def load_individual(newDb):
    newTableName = 'individual'
    df = pandas.read_csv(INDIVIDUALS_VOCAB,
                         na_filter=False)
    # fields label,individual_id,description,lname,fname,email,ORCID
    LOGGER.debug('individualsVocab columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        try:
            if row['individual_id']:
                newRow['individual_id'] = row['individual_id']
            else:
                print('load individual; got an empty primary key, break ', row['label'])
                continue
            newRow['label'] = row['label'].strip().replace('\'', '\'\'')
            newRow['fname'] = row['fname'].strip().replace('\'', '\'\'')
            newRow['lname'] = row['lname'].strip().replace('\'', '\'\'')
            if row['ORCID']:
                newRow['individual_uri'] = row['ORCID'].strip()
            if row['email']:
                newRow['email'] = row['email'].strip()
            if row['description']:
                newRow['description'] = row['description'].strip()
        except:
            print('problem with individual: ', row)
            newRow = {}
        # Insert this data into new db
        if len(newRow) != 0:
            try:
                result = insertRow(cursor, newTableName, newRow)
                rowNum = rowNum + 1
                LOGGER.debug('rowNum: %s Individual_id %s', rowNum, row['individual_id'])
            except:
                print('Individual insertRow fail, newRow:', newRow)
    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_sesar_user(newDb):
    # First load sesar_users to preserve the sesar_user_ids
    #  tbd -- load individuals from smr spreadsheet
    tableName = 'sesar_user'
    newTableName = 'sesar_user'
    parentLinkTableName = 'parent_institution'
    timestamp = datetime.now().isoformat('T', 'seconds')
    # set up lookup dictionary to get individual_id or group_id, and the institution_id for
    #   the user affiliation.  These will be keyed to the sesar_user_id in a list
    lkup = pandas.read_excel(AGENTS_MAPPING,
                             sheet_name="sesar_user20241209",
                             na_filter=False)
    LOGGER.debug('SESAR user lookup columns: %s', ', '.join(lkup.columns))

    rowNum = 0
    cursor = newDb.cursor()
    for index, row in lkup.iterrows():
        newRow = {}
        newRow['sesar_user'] = row['sesar_user_id']
        if row['sso_account_id'] != 'NULL':
            newRow['sso_account_id'] = row['sso_account_id']
        newRow['is_admin'] = row['is_admin']
        if row['note'] != 'NULL':
            newRow['note'] = row['note'].strip().replace('\'', '\'\'')
        newRow['password'] = row['password']
        newRow['upload_permission_status'] = row['upload_permission_status']
        if row['upload_permission_date'] != 'NULL':
            newRow['upload_permission_date'] = row['upload_permission_date']
        if row['registration_date'] != 'NULL':
            newRow['registration_date'] = row['registration_date']
        if row['deactivation_date'] != 'NULL':
            newRow['deactivation_date'] = row['deactivation_date']
        if row['legacy_user_id'] != 'NULL':
            newRow['legacy_user_id'] = row['legacy_user_id']
        if row['geopass_id'] != 'NULL':
            newRow['geopass_id'] = row['geopass_id']
        newRow['doi_prefix'] = row['doi_prefix']
        if row['last_login'] != 'NULL':
            newRow['last_login'] = row['last_login']
        if row['orcid'] != 'NULL':
            newRow['orcid'] = row['orcid']
        if row['agentType'] == 'individual':
            newRow['individual_id'] = row['agent_id']
            if row['institution_id']:
                newRow['institution_id'] = row['institution_id']
        if row['agentType'] == 'institution':
            newRow['institution_id'] = row['agent_id']
        if row['agentType'] == 'institution part':
            newRow['institution_id'] = row['agent_id']
        if row['email'] != 'NULL':
            newRow['email'] = row['email']

        # Insert this data into new db
        try:
            result = insertRow(cursor, newTableName, newRow)
            newDb.commit()
        except Exception as e:
            print(f'problem with sesar user insert {newRow}')
            LOGGER.info('load_sesar_user exception: %s', repr(e))

        # check if user is an institution with a parent institution,
        if row['agentType'] == 'institution part':
            # if so, create a parent_institution record
            newDb.commit()
            newRow = {}
            try:
                newRow['label'] = row['sesar_user_id']
                newRow['description'] = row['sesar_user_id']
                newRow['activate_date'] = timestamp
                newRow['institution_id'] = row['agent_id']
                newRow['parent_id'] = row['institution_id']
                newRow['relation_type_id'] = 1
                result = insertRow(cursor, parentLinkTableName, newRow)
                # LOGGER.info(f'parent institution row: {newRow}')
                # newDb.commit()
            except Exception as e:
                LOGGER.info(f'problem with parent link: {newRow}')
                LOGGER.info('load_sesar_user parent exception: %s', repr(e))

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_spatial_ref_sys(newDb):
    newTableName = 'sesar_spatial_ref_sys'
    df = pandas.read_excel(DEPTH_SCALE_UNIQUE,
                           sheet_name="sesar_spatial_ref_vocab",
                           na_filter=False)
    LOGGER.debug('sesar spatial reference system vocab columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['spatial_ref_id'] = row['spatial_ref_id']
        newRow['name'] = row['name'].strip().replace('\'', '\'\'')
        newRow['description'] = row['description'].strip().replace('\'', '\'\'')
        newRow['identifier'] = row['identifier']
        result = insertRow(cursor, newTableName, newRow)

        # rowNum = rowNum + 1
        # LOGGER.debug('rowNum: ', rowNum)
    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_sample_type(newDb):
    newTableName = 'sample_type'
    df = pandas.read_csv(SAMPLE_TYPE_VOCAB,
                         na_filter=False)
    LOGGER.debug('sample type columns:%s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['sample_type_id'] = row['sample_type_id']
        newRow['label'] = row['label'].strip().replace('\'', '\'\'')
        newRow['description'] = row['description'].strip().replace('\'', '\'\'')
        newRow['sample_type_uri'] = row['sample_type_uri']
        newRow['scheme_uri'] = 'https://w3id.org/sesar/objecttype/objecttypevocabulary'
        newRow['scheme_name'] = 'SESAR material sample object type extension'
        if (row['parent_sample_type_id'] != ''):  # top concept in vocab won't have a parent
            newRow['parent_sample_type_id'] = row['parent_sample_type_id']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_sampled_feature_type(newDb):
    newTableName = 'sampled_feature_type'
    df = pandas.read_excel(SAMPLED_FEATURE_TYPE_VOCAB,
                           sheet_name="sampledFeatureTable",
                           na_filter=False)
    LOGGER.debug('sampled feature type columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['feature_type_id'] = row['feature_type_id']
        newRow['label'] = row['label'].strip().replace('\'', '\'\'')
        newRow['description'] = row['description'].strip().replace('\'', '\'\'')
        newRow['feature_type_uri'] = row['uri']
        if row['source'] != '':
            newRow['source'] = row['source'].strip().replace('\'', '\'\'')
        newRow['scheme_uri'] = 'sessf:sfvocabulary'
        if (row['parent_feature_type_id'] != ''):  # top concept in vocab won't have a parent
            newRow['parent_feature_type_id'] = row['parent_feature_type_id']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_locality(newDb):
    newTableName = 'locality'
    df = pandas.read_excel(ALLOCATION_DISTINCT,
                           sheet_name='LocationVocab',
                           na_filter=False)
    LOGGER.debug('locality columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['locality_id'] = row['locality_id']
        newRow['name'] = row['label'].strip().replace('\'', '\'\'')[:119]
        newRow['description'] = 'missing'
        if row['feature_type_id'] != '':
            newRow['feature_type_id'] = row['feature_type_id']
        if row['province'] != '':
            newRow['province'] = row['province'].strip().replace('\'', '\'\'')
        if row['county'] != '':
            newRow['county'] = row['county'].strip().replace('\'', '\'\'')
        if row['city'] != '':
            newRow['city'] = row['city'].strip().replace('\'', '\'\'')
        if row['country_id'] != '':
            newRow['country_id'] = row['country_id']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_institution(newDb):
    newTableName = 'institution'
    df = pandas.read_csv(INSTITUTION_VOCAB,
                         na_filter=False)
    # names=[label,institution_id,institution_type_id,Type,email,description]
    LOGGER.debug('institution columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        try:
            newRow['institution_id'] = row['institution_id']
            newRow['label'] = row['label'].strip().replace('\'', '\'\'')
            newRow['description'] = row['description'].strip().replace('\'', '\'\'')
            newRow['institution_type_id'] = row['institution_type_id']
            newRow['email'] = row['email'].strip()
            newRow['activate_date'] = '2024-12-21'
            result = insertRow(cursor, newTableName, newRow)
        except Exception as e:
            LOGGER.info('load_institution exception: %s', repr(e))
            LOGGER.info('problem with institution:', row)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_material_role(newDb):
    newTableName = 'material_role_type'
    df = pandas.read_excel(SAMPLE_MATERIAL_ROLE,
                           sheet_name="MaterialRole",
                           na_filter=False)

    LOGGER.debug('material role columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['material_role_id'] = row['material_role_id']
        newRow['label'] = row['relation'].strip().replace('\'', '\'\'')
        if row['notes'] != '':
            newRow['description'] = row['notes'].strip().replace('\'', '\'\'')
        if row['source'] != '':
            newRow['scheme_name'] = row['source'].strip().replace('\'', '\'\'')
        result = insertRow(cursor, newTableName, newRow)
        rowNum = rowNum + 1
        LOGGER.debug('load material role, rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_material_type(newDb):
    newTableName = 'material_type'
    df = pandas.read_excel(SESAR_MATERIAL_TYPE_VOCAB,
                           sheet_name="Material_vocabulary",
                           na_filter=False)

    LOGGER.debug('material type columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['material_type_id'] = row['material_id']
        newRow['label'] = row['label'].strip().replace('\'', '\'\'')
        if row['description'] != '':
            newRow['description'] = row['description'].strip().replace('\'', '\'\'')
        if row['material_type_uri'] != '':
            newRow['material_type_uri'] = row['material_type_uri']
        if row['source'] != '':
            newRow['source'] = row['source'].strip().replace('\'', '\'\'')
        if row['scheme_uri'] != '':
            newRow['scheme_uri'] = row['scheme_uri']
        if row['parent_material_type_id'] != '':
            newRow['parent_material_type_id'] = row['parent_material_type_id']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_platform(newDb):
    newTableName = 'platform'
    # get from excel workbook
    df = pandas.read_excel(PLATFORM_NAME_VOCAB,
                           sheet_name="PlatformVocabulary",
                           na_filter=False)
    LOGGER.debug('platform columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['platform_id'] = row['platform_id']
        newRow['label'] = row['label'].strip().replace('\'', '\'\'')
        if len(row['description']) > 0:
            newRow['description'] = row['description'].strip().replace('\'', '\'\'')
        newRow['launch_type_id'] = row['launch_type_id']
        newRow['platform_type_id'] = row['platform_type_id']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_initiative(newDb):
    newTableName = 'initiative'
    df = pandas.read_csv(INITIATIVE_VOCAB,
                         na_filter=False)
    LOGGER.debug('initiative columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['initiative_id'] = row['initiative_id']
        newRow['label'] = row['label'].strip().replace('\'', '\'\'')
        if row['notes'] != '':
            newRow['description'] = row['notes'].strip().replace('\'', '\'\'')
        if row['start'] != '' and row['start'] != 'NULL':
            newRow['begin_date'] = row['start']
        if row['end'] != '' and row['end'] != 'NULL':
            newRow['end_date'] = row['end']
        if row['type_id'] != '' and row['type_id'] != 'NULL':
            newRow['initiative_type_id'] = row['type_id']

        result = insertRow(cursor, newTableName, newRow)

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)

    newDb.commit()
    if cursor:
        cursor.close()
    return 1


def load_sesar_spatial_ref(newDb):
    newTableName = 'sesar_spatial_ref'
    # get from excel workbook
    df = pandas.read_excel(DEPTH_SCALE_UNIQUE,
                           sheet_name="sesar_spatial_ref_vocab",
                           na_filter=False)
    LOGGER.debug('Depth datum columns: %s', ' '.join(df.columns))
    rowNum = 0
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        newRow = {}
        newRow['spatial_ref_id'] = row['spatial_ref_id']
        newRow['name'] = row['name'].strip().replace('\'', '\'\'')
        if len(row['description']) > 0:
            newRow['description'] = row['description'].strip().replace('\'', '\'\'')
        if len(row['identifier']) > 0:
            newRow['identifier'] = row['identifier']
        result = insertRow(cursor, newTableName, newRow)
        # rowNum = rowNum + 1
        # LOGGER.debug('rowNum: ', rowNum)
    newDb.commit()
    if cursor:
        cursor.close()
    return 1


# load the geologic_time_scale table
def load_geologic_time_scale(newDb):
    newTableName = "geologic_time_scale"
    # get from excel workbook
    df = pandas.read_excel(GEOLOGIC_TIME_SCALE2020)
    LOGGER.debug('Geo time scale columns: %s', ' '.join(df.columns))
    cursor = newDb.cursor()
    for index, row in df.iterrows():
        # LOGGER.debug('timescale row: %s',row[0])
        newRow = {}
        try:
            newRow['label'] = row['label']
            tevent = ""
            spoint = ""
            scomment = ""
            if not (pandas.isna(row.event)):
                tevent = "Event: " + str(row['event'])
            if not (pandas.isna(row.bLevel)):
                spoint = "Stratigraphic point: " + str(row['bLevel'])
            if not (pandas.isna(row.stratotypeComment)):
                scomment = "Stratotype commment: " + str(row['stratotypeComment'])
            thetext = tevent + '; ' + spoint + '; ' + scomment
            thetext = thetext.replace("'", "''")
            thetext = thetext.replace('"', '""')
            newRow['description'] = thetext
            newRow['geologic_time_interval_uri'] = row['URI']
            if pandas.isna(row.source):
                rsource = 'missing'
            else:
                rsource = row['source']
            newRow['source'] = rsource
            newRow['scheme_uri'] = 'http://resource.geosciml.org/vocabulary/timescale/gts2020'
            newRow['numeric_older_bound'] = row['beginMa']
            newRow['numeric_younger_bound'] = row['endMa']
            newRow['notation'] = row['notation']
            LOGGER.debug('Geo time scale newRow: ', newRow)
            result = insertRow(cursor, newTableName, newRow)
        except Exception as e:
            LOGGER.info('load_geologic_time_scale exception: %s', repr(e))
            LOGGER.info("load_geologic_time_scale insert row problem. row: %s", ', '.join(row))

    try:
        newDb.commit()
    except Exception as e:
        LOGGER.info(f'load_geologic_time_scale commit problem. exception: {repr(e)}')
        if cursor:
            cursor.close()
        return 0
    if cursor:
        cursor.close()
    return 1


def load_lookups():
    print('build lookup dataframes')
    print('country lookup')
    lkup = pandas.read_excel(COUNTRY_VOCABULARY, sheet_name="countrySESARdump",
                             na_filter=False)
    LOGGER.debug('Load country lookup columns: %s', ', '.join(lkup.columns))
    # get the country vocabulary.
    for index, row in lkup.iterrows():
        COUNTRY_LKUP[row['country_id']] = row['label']  # get rid of special characters
    lkup = {}

    print('sampling method lookup from legacy collection method')
    lkup = pandas.read_excel(SAMPLING_METHOD_LOOKUP,
                             sheet_name='samplemethodlookup',
                             na_filter=False
                             )
    LOGGER.debug('Load sample, sampling method lookup columns: %s', ', '.join(lkup.columns))
    # get the sampling_method vocabulary.
    for index, row in lkup.iterrows():
        COLLECTION_METHOD_LKUP[cleanKey(row['collection_method'])] = row['method_id']  # get rid of special characters
    lkup = {}

    # sample type
    # map legacy integer_ids to ids in new vocabulary; mostly these don't change
    print('sample type lookup')
    lkup = pandas.read_excel(SESAR_SAMPLE_TYPE_MAPPING,
                             sheet_name='SESAR_SampleTypeMapping',
                             na_filter=False
                             )
    LOGGER.debug('Load sample, sample type lookup columns: %s', ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        SAMPLE_TYPE_LKUP[row['legacy_sample_type_id']] = row
    lkup = {}

    # locality_id lookup based on the key ('fullkey')concatenated from source fields in the legacy data
    #    lkup = pandas.read_excel('../../MigrationNotes_LookupTables/LocationLocality/AllLocationDistinct-refine.xlsx',
    #                           sheet_name='AllLocationDistinct-lookup',
    #                           na_filter=False)
    print('locality lookup')
    lkup = pandas.read_csv(LOCALITY_LOOKUP,
                           na_filter=False,
                           usecols=['fullKey', 'locality_id'], dtype={'fullKey': 'string', 'locality_id': 'int'})
    LOGGER.debug('Load sample, locality_id lookup columns: %s', ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        theKey = cleanKey(row['fullKey'])
        LOCALITY_LKUP[theKey] = row['locality_id']
    lkup = {}

    print('locality feature type lookup')
    lkup = pandas.read_csv(LOCALITY_FEATURE_TYPE_COUNTRY,
                           na_filter=False)
    LOGGER.debug('locality feature type lookup columns: %s', ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        theKey = row['locality_id']
        FEATURETYPE_LKUP[theKey] = row['feature_type_id']
    lkup = {}

    # initiative_id based on cruise_field_prgrm in legacy data
    print('initiative lookup')
    lkup = pandas.read_csv(INITIATIVE_LOOKUP,
                           na_filter=False,
                           usecols=[0, 2])
    LOGGER.debug('Load sample, initiative_id lookup columns: %s', ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        theKey = cleanKey(row['cruise_field_prgrm_verbatim'])
        INITIATIVE_LKUP[theKey] = row['initiative_id']
    lkup = {}

    # platform_id based on cruise_field_prgrm in legacy data
    print('platform lookup')
    lkup = pandas.read_excel(PLATFORM_LOOKUP,
                             sheet_name='PlatformLookup',
                             na_filter=False
                             )
    LOGGER.debug('Load sample, platform_id lookup columns: %s', ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        theKey = cleanKey(str(row['verbatim_platform_name']))
        try:
            PLATFORM_LKUP[theKey] = row['platform_id']
        except Exception as e:
            LOGGER.info('lookup for platform name exception: %s', repr(e))
            LOGGER.info('bad lookup for platform name: ' + theKey)
            PLATFORM_LKUP[theKey] = -9999
    lkup = {}

    # datum lookup to normalize depth_scale (depth_uom)
    print('depth datum lookup')
    lkup = pandas.read_excel(DEPTH_SCALE_UNIQUE,
                             sheet_name='vertical_ref_lookup',
                             na_filter=False
                             )
    LOGGER.debug('Load depth datum IDs: %s', ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        theKey = cleanKey(str(row['vertical_spatial_ref']))
        try:
            DATUM_LKUP[theKey] = row
        except Exception as e:
            LOGGER.info('lookup for depth datum exception: %s', repr(e))
            LOGGER.info('bad lookup for depth datum, key: ' + theKey)
            DATUM_LKUP[theKey] = []
    lkup = {}

    # material type based on top_classification_id or classification_id
    print('material classification lookup')
    lkup = pandas.read_csv(CLASSIFICATION_MATERIAL_LOOKUP,
                           na_filter=False)
    LOGGER.debug('classification-material lookup columns: %s', ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        theKey = row['classification_id']
        try:
            MATERIAL_LKUP[theKey] = row
        except:
            LOGGER.info('bad lookup for material_id: ', theKey)
            row['material_id'] = -9999
            row['label'] = 'check'
            MATERIAL_LKUP[theKey] = row
    lkup = {}

    # geologic age lookup, based on geological_age, age_min, age_max, age_unit in legacy data
    print('geologic age lookup')
    lkup = pandas.read_excel(GEOLOGIC_AGE_LOOKUP,
                             sheet_name='geologic_age_lkup',
                             na_filter=False
                             )
    LOGGER.debug('Load geologic age lookup columns: %s', ', '.join(lkup.columns))

    for index, row in lkup.iterrows():
        if is_number(row['age_min']):
            amin = "{:08.6f}".format(row['age_min'])  # have to format consistently to make a lookup key
        else:
            amin = 'null'
        if is_number(row['age_max']):
            amax = "{:08.6f}".format(row['age_max'])
        else:
            amax = 'null'
        theKey = str(row['geological_age']) + amin + amax + str(row['age_unit'])
        theKey = cleanKey(theKey)
        try:
            GEOLOGIC_AGE_LKUP[theKey] = row[-12:-4]  # take 11 fields from the end.
        except Exception as e:
            LOGGER.info('lookup for geologic age name exception: %s', repr(e))
            LOGGER.info(f'bad lookup for geologic age row: {theKey}')
    lkup = {}

    # collector
    # generate collector lookup. The legacy sample.collector field is the key,
    #   value in dictionary is an array of names
    #   collector might be individual or is list of individuals (multi_collector)
    lkup = pandas.read_csv(MULTIPLE_COLLECTOR_LOOKUP,
                           na_filter=False)
    LOGGER.debug('load_correlation_tables, multiple collector lookup columns: %s',
                 ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        try:
            theKey = cleanKey(row['sam_collector'])
        except Exception as e:
            LOGGER.info('multiple collector lookup, exception: %s', repr(e))
            LOGGER.info('key problem, multiple collector lookup: ', row['sam_collector'])
            continue
        # slice off the elements after the sam_collector column
        # there are up to 9 names in the collector list
        MULTI_COLLECTOR_LKUP[theKey] = row[-10:]
    lkup = {}

    # agent name-id lookup
    lkup = pandas.read_csv(AGENTID_LOOKUP,
                           na_filter=False)
    LOGGER.debug('load_correlation_tables, agent ID lookup columns: %s', ', '.join(lkup.columns))
    # columns should be label_verbatim, prefName, individual_id, source,
    # agent_id_lkup  find by verbatim label
    # agent_name_lkup find by agent_id
    for index, row in lkup.iterrows():
        theKey = cleanKey(row['label_verbatim'])
        AGENT_ID_LKUP[theKey] = row
        theKey = cleanKey(str(row['agent_id']))
        AGENT_NAME_LKUP[theKey] = row
    lkup = {}

    # archive and point of contact lookup
    lkup = pandas.read_csv(ARCHIVE_POC_LOOKUP,
                           na_filter=False)
    LOGGER.debug('load_correlation_tables, Archive POC lookup columns: %s', ', '.join(lkup.columns))
    for index, row in lkup.iterrows():
        theKey = cleanKey(row['archive'] + row['poc'])
        # concatenate archive and poc fields
        if (row['institution_id'] or row['individual_id'] or row['individual'] == 'multi'):
            ARCHIVE_POC_LKUP[theKey] = row
        else:
            ARCHIVE_POC_LKUP[theKey] = {}
    lkup = {}

    print('done with lookup loading')
    return 1


# *************************************************************
#  ***********************************************************
# The main data loading functions, for sample, geospatial location, and
#  correlation tables relating sample to other information

def load_sample(newDb, data, fl):
    # data is a collection of rows from the legacy sample table
    # fl is a list of fields in each sample data row
    start_time = time.time()  # time the function execution
    newTableName = 'sample'
    # set up lookup dictionaries
    # sampling method  samplemethodlookup

    theDict = {}
    rows = []
    rowNum = 0
    cursor = newDb.cursor()
    for row in data:
        theobj = {}
        for nc in range(len(row)):
            if row[nc] is None:
                theobj[fl[nc]] = 'blank'
                # replace null values with 'blank'
            else:
                theobj[fl[nc]] = row[nc]

        # theobj contains key-value pairs for one data row in the oldDb

        newRow = {}
        newRow['age_qualifier'] = 'blank'  # theobj['']
        newRow['archive_date'] = theobj['archive_date']
        if theobj['collection_date_precision'] != 'blank':
            newRow['collection_date_precision'] = theobj['collection_date_precision']

        if theobj['collection_end_date'] != 'blank':
            thecheck = pandas.to_datetime(str(theobj['collection_end_date'])[:22], errors='coerce')
            if pandas.isnull(thecheck):
                logging.info(f"bad collection_end_date {theobj['collection_end_date']}")
            else:
                newRow['collection_end_date'] = thecheck

        newRow['collection_method_detail'] = theobj['collection_method_descr'].replace('\'', '\'\'')

        if theobj['collection_method'] != 'blank':
            # theid = lookup_sampling_method_id(theobj['collection_method'].strip(), collection_method_lkup  )
            try:
                theid = COLLECTION_METHOD_LKUP[cleanKey(theobj['collection_method'].strip())]
                newRow['collection_method_id'] = theid
                LOGGER.debug(f'the id of the sampling method is {str(theid)}')
            except Exception as e:
                LOGGER.info('sampling method exception: %s', repr(e))
                newRow['collection_method_detail'] = newRow['collection_method_detail'] + "error on: " + theobj[
                    'collection_method']
                LOGGER.info(f'id of the sampling method error: {theobj["collection_method"]}')

        if theobj['collection_start_date'] != 'blank':
            thecheck = pandas.to_datetime(str(theobj['collection_start_date'])[:22], errors='coerce')
            if pandas.isnull(thecheck):
                logging.info(f"bad collection_start_date {theobj['collection_start_date']}")
            else:
                newRow['collection_start_date'] = thecheck

        # initiative (cruise_field_prgrm) type
        if theobj['cruise_field_prgrm'] != 'blank':
            try:
                aresult = INITIATIVE_LKUP[cleanKey(theobj['cruise_field_prgrm'])]
                if aresult != -9999:
                    newRow['cruise_field_prgrm_id'] = aresult
            except Exception as e:
                LOGGER.info(f"initiative lookup fail: {theobj['cruise_field_prgrm']}")
                # newRow['cruise_field_prgrm_id'] = -9999

        # cur_owner_id must be a sesar user, so jus copy to new table
        newRow['cur_owner_id'] = theobj['cur_owner_id']

        newRow['cur_registrant_id'] = theobj['cur_registrant_id']  # fk to sesar user

        if theobj['top_level_classification_id'] != 'blank':
            try:
                # row['material_id']
                aresult = MATERIAL_LKUP[str(theobj['top_level_classification_id'])]['material_id']
                if type(aresult) == int:
                    newRow['general_material_type_id'] = aresult
                else:
                    newRow['general_material_type_id'] = -9999
            except Exception as e:
                newRow['general_material_type_id'] = -9999

        theGeoAgeVerbatim = str(theobj['geological_age']) + '; bounds: ' + str(theobj['age_min']) + ' - ' + str(
            theobj['age_max']) + ' ' + str(theobj['age_unit'])
        theGeoAgeVerbatim = theGeoAgeVerbatim.replace('\'', '\'\'')
        if len(theGeoAgeVerbatim) > 0 and theGeoAgeVerbatim != 'blank; bounds: blank - blank blank':
            newRow['geologic_age_verbatim'] = theGeoAgeVerbatim
        theAgeRow = {}
        theGeoAgeKey = ''
        try:
            if is_number(theobj['age_min']):
                amin = "{:08.6f}".format(theobj['age_min'])
            else:
                amin = 'null'
            if is_number(theobj['age_max']):
                amax = "{:08.6f}".format(theobj['age_max'])
            else:
                amax = 'null'
            theGeoAgeKey = str(theobj['geological_age']) + amin + amax + str(theobj['age_unit'])
            theGeoAgeKey = theGeoAgeKey.replace('blank', 'null')
            theGeoAgeKey = cleanKey(theGeoAgeKey)
            theAgeRow = GEOLOGIC_AGE_LKUP[theGeoAgeKey]
        except Exception as e:
            LOGGER.info(f'problem with geologic age lookup {repr(e)}, igsn: {theobj["igsn"]}')
        if len(theAgeRow) > 0:  # skip if there was a problem
            try:
                if theAgeRow['geologic_age_older_id']:
                    newRow['geologic_age_older_id'] = theAgeRow['geologic_age_older_id']
                if theAgeRow['geologic_age_younger_id']:
                    newRow['geologic_age_younger_id'] = theAgeRow['geologic_age_younger_id']
                if theAgeRow['age_qualifier']:
                    newRow['age_qualifier'] = theAgeRow['age_qualifier']
                if theAgeRow['numeric_age_max']:
                    newRow['numeric_age_max'] = theAgeRow['numeric_age_max']
                if theAgeRow['numeric_age_min']:
                    newRow['numeric_age_min'] = theAgeRow['numeric_age_min']
                if theAgeRow['numeric_age_unit']:
                    newRow['numeric_age_unit'] = theAgeRow['numeric_age_unit']
            except Exception as e:
                LOGGER.info(f'problem with loading geo age rows {repr(e)}')
                LOGGER.info(f'problem with geo age. Key: {theGeoAgeKey}, rows {theAgeRow}')

        newRow['geologic_unit'] = theobj['geological_unit'].replace('\'', '\'\'')
        if theobj['geom_latlong'] != 'blank':
            newRow['geom_latlong'] = theobj['geom_latlong']
        newRow['igsn'] = theobj['igsn']
        newRow['igsn_prefix'] = theobj['igsn_prefix']
        newRow['igsn_is_system_assigned'] = theobj['igsn_is_system_assigned']
        newRow['last_changed_by_id'] = theobj['last_changed_by']
        newRow['last_update_date'] = theobj['last_update_date']
        newRow['latitude'] = theobj['latitude']
        newRow['latitude_end'] = theobj['latitude_end']
        newRow['launch_label'] = theobj['launch_id']

        if theobj['launch_platform_name'] != 'blank':
            try:
                newRow['launch_platform_id'] = PLATFORM_LKUP[cleanKey(str(theobj['launch_platform_name']))]
            except Exception as e:
                newRow['launch_platform_id'] = -9999

        # calculate the fullLookupkey
        locKey = get_locality_key(theobj)  # construct key from fields in legacy sample data
        if locKey != '':
            locdetail = ''
            if theobj['primary_location_name'] != 'blank':
                locdetail = locdetail + theobj['primary_location_name'] + ". "
            if theobj['primary_location_type'] != 'blank':
                locdetail = locdetail + theobj['primary_location_type'] + ". "
            if theobj['location_description'] != 'blank':
                locdetail = locdetail + theobj['location_description'] + ". "
            if theobj['locality'] != 'blank':
                locdetail = locdetail + theobj['locality'] + ". "
            if theobj['locality_description'] != 'blank':
                locdetail = locdetail + theobj['locality_description'] + ". "
            if theobj['province'] != 'blank':
                locdetail = locdetail + theobj['province'] + ". "
            if theobj['county'] != 'blank':
                locdetail = locdetail + theobj['county'] + ". "
            if theobj['city'] != 'blank':
                locdetail = locdetail + theobj['city'] + ". "

            try:
                if theobj['country_id'] != 'blank':
                    locdetail = locdetail + ", " + COUNTRY_LKUP[theobj['country_id']]
            except:
                LOGGER.info(f"locdetail countryID lookup problem, country_id {theobj['country_id']}")
            locdetail = locdetail.replace('blank', '')
            locdetail = locdetail.replace('. . ', '. ').replace('\'', '\'\'')
            locdetail = locdetail.replace('. . ', '. ')
            newRow['locality_detail'] = locdetail
            loc_id = ''
            try:
                if LOCALITY_LKUP[locKey] == -9999:
                    LOGGER.debug(f'locality_id lookup -9999, locKey:{locKey}')
                else:
                    loc_id = LOCALITY_LKUP[locKey]
                    newRow['locality_id'] = loc_id
            except Exception as e:
                newRow['locality_detail'] = "locality_id not defined. " + locdetail
                LOGGER.info(f'locality_id lookup exception. locKey: {locKey}')

            try:
                if loc_id:
                    if len(FEATURETYPE_LKUP[loc_id]) > 0:
                        newRow['sampled_feature_type_id'] = FEATURETYPE_LKUP[loc_id]
            except Exception as e:
                LOGGER.info(f'feature type lookup exception {loc_id}')

        else:
            newRow['locality_detail'] = ''
            # LOGGER.info(f'locKey is blank, sample_id: {theobj['sample_id']}')

        newRow['location_method_id'] = theobj['nav_type_id']  # theobj['']
        newRow['location_qualifier'] = ''  # theobj['']
        newRow['longitude'] = theobj['longitude']
        newRow['longitude_end'] = theobj['longitude_end']

        # for verbatim material, concatenate field_name and classifications
        verb_mat = ''
        if theobj['top_level_classification_id'] != 'blank':
            verb_mat = verb_mat + MATERIAL_LKUP[str(theobj['top_level_classification_id'])][
                'classification_label'].replace('\'', '\'\'')
        if len(verb_mat) > 0:
            verb_mat = verb_mat + '; '
        if theobj['classification_id'] != 'blank':
            verb_mat = (verb_mat + MATERIAL_LKUP[str(theobj['classification_id'])]['classification_label'].
                        replace('\'','\'\''))
        if len(verb_mat) > 0:
            verb_mat = verb_mat + '; '
        if theobj['field_name'] != 'blank':
            verb_mat = verb_mat + theobj['field_name'].replace('\'', '\'\'')
        if len(verb_mat) > 0:
            newRow['material_name_verbatim'] = verb_mat

        if theobj['metadata_store_status'] != 'blank':
            newRow['metadata_store_status'] = theobj['metadata_store_status']
        else:
            newRow['metadata_store_status'] = 'missing'
        newRow['name'] = theobj['name'].replace('\'', '\'\'')
        newRow['numeric_age_max'] = theobj['age_max']
        newRow['numeric_age_min'] = theobj['age_min']
        newRow['numeric_age_unit'] = theobj['age_unit']
        #if theobj['origin_sample_id'] != 'blank':
        #    newRow['parent_sample_id'] = theobj['origin_sample_id']
        # platform
        if theobj['platform_name'] != 'blank':
            try:
                newRow['platform_id'] = PLATFORM_LKUP[cleanKey(str(theobj['platform_name']))]
            except Exception as e:
                newRow['platform_id'] = -9999

        newRow['publish_date'] = theobj['publish_date']
        if theobj['purpose'] != 'blank':
            newRow['purpose'] = theobj['purpose'].replace('\'', '\'\'')
        newRow['registration_date'] = theobj['registration_date']
        tempstr = ''
        if theobj['description'] != 'blank':
            tempstr = tempstr + theobj['description'] + '; '
        if theobj['classification_comment'] != 'blank':
            tempstr = tempstr + theobj['classification_comment'] + '; '
        if theobj['sample_comment'] != 'blank':
            tempstr = tempstr + theobj['sample_comment'] + '; '
        if theobj['collector_detail'] != 'blank':
            tempstr = tempstr + theobj['collector_detail']
        tempstr = tempstr.replace('blank; ', '').replace('\'', '\'\'')
        tempstr = tempstr.replace('; blank', '')
        if len(tempstr) > 0:
            newRow['sample_description'] = tempstr
        newRow['sample_id'] = theobj['sample_id']  # Database primary key
        # sample type
        try:
            newRow['sample_type_id'] = SAMPLE_TYPE_LKUP[theobj['sample_type_id']]['sesar2024_id']
        except Exception as e:
            newRow['sample_type_id'] = -9999

        if theobj['size'] != 'blank':
            newRow['size'] = theobj['size']
        if theobj['size_unit'] != 'blank':
            if theobj['size'] != 'blank':
                newRow['size'] = newRow['size'] + ' ' + theobj['size_unit']
            else:
                newRow['size'] = theobj['size_unit']

        # **************************************************
        #  logic to handle the variations in encoding depth and elevation
        dmax = theobj['depth_max']
        dmin = theobj['depth_min']
        dscale = cleanKey(theobj['depth_scale'])
        elev = theobj['elevation']
        elev_end = theobj['elevation_end']
        vert_datum = cleanKey(theobj['vertical_datum'])

        check_string = ''
        if isinstance(dmin, numbers.Number):
            if dmin > 99999:  # skip a couple bogus records
                dmin = 'blank'
            else:
                check_string = check_string + str(dmin)
        if isinstance(dmax, numbers.Number):
            check_string = check_string + str(dmax)
        if isinstance(elev, numbers.Number):
            check_string = check_string + str(elev)
        if isinstance(elev_end, numbers.Number):
            check_string = check_string + str(elev_end)

        thenotes = ''
        if len(check_string) > 0:  # check if there's any depth or elevation data
            if (dmin != 'blank' or dmax != 'blank') and \
                    elev == 'blank' and elev_end == 'blank':  # have depth(s), no elevation data
                if dmin != 'blank' and dmax != 'blank':
                    newRow['depth_min'] = min(abs(dmax), abs(dmin))
                    newRow['depth_max'] = max(abs(dmax), abs(dmin))
                elif dmin != 'blank':
                    newRow['depth_min'] = abs(dmin)
                elif dmax != 'blank':
                    newRow['depth_max'] = abs(dmax)
                if dscale != 'blank':
                    thenotes = thenotes + f' Reference datum for depth: {DATUM_LKUP[dscale].iloc[3]}'
                    # thenotes = thenotes + f' Reference datum for depth: {datum_lkup[dscale][3]}'
                    newRow['depth_spatial_ref_id'] = DATUM_LKUP[dscale].iloc[1]
                    newRow['depth_uom'] = DATUM_LKUP[dscale].iloc[2]
                else:
                    thenotes = thenotes + '. Reference datum for depths not specified.'
            if dmin == 'blank' and dmax == 'blank' and elev_end == 'blank' \
                    and elev != 'blank':  # only have elevation.
                newRow['elevation'] = elev  # only have elevation, no depth(s)
                if vert_datum != 'blank':
                    thenotes = f' Vertical datum is {vert_datum}'
                    newRow['depth_spatial_ref_id'] = DATUM_LKUP[vert_datum].iloc[1]
                    newRow['depth_uom'] = DATUM_LKUP[vert_datum].iloc[2]
                    # change to datum_lkup[vert_datum].iloc[1]

            if dmin == 'blank' and dmax == 'blank' and elev == 'blank' \
                    and elev_end != 'blank':  # only have elevation_end, no depth(s)
                newRow['elevation'] = elev_end
                thenotes = ' Elevation_end reported as elevation.'
                if vert_datum != 'blank':
                    thenotes = thenotes + f' Vertical datum is {vert_datum}'
                    newRow['depth_spatial_ref_id'] = DATUM_LKUP[vert_datum].iloc[1]
                    newRow['depth_uom'] = DATUM_LKUP[vert_datum].iloc[2]
                    # change to datum_lkup[vert_datum].iloc[1]
            if (dmin != 'blank' or dmin != 'blank') and elev != 'blank' and elev_end != 'blank':
                # have depth(s), elevation and elevation_end
                thenotes = thenotes + f' Elevation of sampled interval from {elev} to {elev_end}'
                newRow['elevation'] = elev
                if vert_datum != 'blank':
                    thenotes = thenotes + f' Elevation vertical datum: {vert_datum}'
                    newRow['depth_spatial_ref_id'] = DATUM_LKUP[vert_datum].iloc[1]
                    newRow['depth_uom'] = DATUM_LKUP[vert_datum].iloc[2]
                    # change to datum_lkup[vert_datum].iloc[1]
                else:
                    thenotes = thenotes + f' Vertical datum not reported'
                if dmin != 'blank' and dmin != 'blank':
                    newRow['depth_min'] = min(abs(dmax), abs(dmin))
                    newRow['depth_max'] = max(abs(dmax), abs(dmin))
                elif dmin != 'blank':
                    newRow['depth_min'] = abs(dmin)
                elif dmax != 'blank':
                    newRow['depth_max'] = abs(dmax)
                if dscale != 'blank':
                    thenotes = thenotes + f' Reference datum for depth: {DATUM_LKUP[dscale].iloc[3]}'
                    newRow['depth_spatial_ref_id'] = DATUM_LKUP[dscale].iloc[1]
                    newRow['depth_uom'] = DATUM_LKUP[dscale].iloc[2]
                    # change to datum_lkup[dscale].iloc[1]
                else:
                    thenotes = thenotes + '. Reference datum for depths not specified.'

            if dmin == 'blank' and dmin == 'blank' and elev != 'blank' and elev_end != 'blank':
                if vert_datum != 'blank':
                    newRow['elevation'] = elev
                    thenotes = thenotes + f' sampling elevation between {elev} and {elev_end} {vert_datum}'
                    newRow['depth_spatial_ref_id'] = DATUM_LKUP[vert_datum].iloc[1]
                    newRow['depth_uom'] = DATUM_LKUP[vert_datum].iloc[2]
                    # change to datum_lkup[dscale].iloc[1]
                else:  # vert_datum == 'blank'
                    if theobj['sample_type_id'] == 12:  # dredge haul
                        newRow['depth_min'] = min(abs(elev), abs(elev_end))
                        newRow['depth_max'] = max(abs(elev), abs(elev_end))
                        thenotes = thenotes + f' Dredge haul depth reported as elevation, make depths positive, end of haul at ={abs(elev_end)}'
                    else:  # other sample types
                        newRow['elevation'] = elev
                if elev == elev_end:
                    thenotes = thenotes + f' Sampling elevation is {elev}, datum not reported.'
                elif elev_end < elev:
                    thenotes = thenotes + f' Sampling elevation between {elev} and {elev_end}, datum not reported.'
                else:  # elev_end > elev
                    if elev_end < 0:
                        thenotes = thenotes + f' Reported sampling elevation between {elev} and {elev_end},' + \
                                   f' bottom of interval is probably {elev}, datum not reported.'
                    else:
                        thenotes = thenotes + f' Reported sampling elevation between {elev} and {elev_end}, ' + \
                                   f'bottom of interval is probably -{elev_end}, datum not reported.'
            try:
                if len(thenotes) > 0:
                    newRow['location_qualifier'] = (newRow['location_qualifier'] + thenotes).replace('\'', '\'\'')[:128]
            except:
                LOGGER.info(f'key error, locality detail ')

        # Insert this data into new db
        try:
            result = insertRow(cursor, newTableName, newRow)
            # result = 1  # for debugging
        except Exception as e:
            LOGGER.info('sample insert error, exception: %s', repr(e))
            LOGGER.info(f'Sample insert error. igsn: {newRow["igsn"]} ')
            continue
        try:
            newDb.commit()
        except Exception as e:
            LOGGER.info(f"load sample, db commit fail. igsn:{newRow['igsn']}, {repr(e)}")
            continue

        if theobj['easting'] != 'blank':
            result = insert_one_utm_loc(newDb, theobj)

        result = insert_one2many_links(newDb, theobj)

        rowNum = rowNum + 1
        if rowNum % 10000 == 0:
            LOGGER.debug(f'load sample rowNum: {rowNum}')

    newDb.commit()
    end_time = time.time()
    execution_time = end_time - start_time
    LOGGER.info(f"load sample batch execution time: {execution_time} seconds")

    cursor.close()

    return 1  # load sample


def insert_one_utm_loc(newDb, theobj):
    newTableName = 'geospatial_location'
    # filter for records with UTM coordinates
    LOGGER.debug(f'insert_geospatial_location, sampleid {theobj["sample_id"]}')
    cursor = newDb.cursor()
    # theobj contains key-value pairs for one data row in the oldDb
    # fields:
    # $ location_id, label, description, vertical, coordinate_1, coordinate_2,
    # "WKT_geometry", global_grid_cell_id,
    # sample_id, spatial_reference_system, vertical_srs)
    newRow = {}
    try:
        newRow['sample_id'] = theobj['sample_id']
        newRow['label'] = f"UTM coordinates, sample {theobj['sample_id']}"
        newRow['description'] = "coordinate order is easting, northing"
        newRow['coordinate_1'] = theobj['easting']
        newRow['coordinate_2'] = theobj['northing']
        newRow['spatial_reference_system'] = "UTM zone " + theobj['zone']
        result = insertRow(cursor, newTableName, newRow)
        newDb.commit()  # commit on each pass to catch foreign key errors
    except Exception as e:
        LOGGER.info('insert_geospatial_location exception: %s', repr(e))
        LOGGER.info(f"insert_geospatial_location problem. {theobj['sample_id']}")

    cursor.close()

    return 1


def insert_geospatial_location(newDb, data, fl):
    # loops through all items in data and finds utms to insert
    # superseded by insert_one_utm_loc
    newTableName = 'geospatial_location'
    # filter for records with UTM coordinates
    LOGGER.debug("insert_geospatial_location, %s number of records: %s",
                 newTableName, len(data))
    rowNum = 0
    cursor = newDb.cursor()
    for row in data:
        newRow = {}
        theobj = {}
        if row[75] is None:  # check for a utm coordinate
            continue
        for nc in range(len(row)):
            if row[nc] is None:
                theobj[fl[nc]] = 'blank'
                # replace null values with 'blank'
            else:
                theobj[fl[nc]] = row[nc]
        # theobj contains key-value pairs for one data row in the oldDb
        # fields:
        # $ location_id, label, description, vertical, coordinate_1, coordinate_2,
        # "WKT_geometry", global_grid_cell_id,
        # sample_id, spatial_reference_system, vertical_srs)
        try:
            newRow['sample_id'] = theobj['sample_id']
            newRow['label'] = f"UTM coordinates, sample {theobj['sample_id']}"
            newRow['description'] = "coordinate order is easting, northing"
            newRow['coordinate_1'] = theobj['easting']
            newRow['coordinate_2'] = theobj['northing']
            newRow['spatial_reference_system'] = "UTM zone " + theobj['zone']
            result = insertRow(cursor, newTableName, newRow)
            newDb.commit()  # commit on each pass to catch foreign key errors
        except Exception as e:
            LOGGER.info('insert_geospatial_location exception: %s', repr(e))
            LOGGER.info(f"insert_geospatial_location problem. {theobj['sample_id']}")

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)
    # newDb.commit()
    return 1


def insert_one2many_links(newDb, theobj):
    # theobj contains contents for one sample record from legacy db
    # extract from load_correlation_tables
    SampleMaterialTableName = 'sample_material'
    # process multiple agents for collector,
    RelatedAgentTable = 'related_sample_agent'
    #   sample additional name
    SampleAdditionalNameTable = 'sample_additional_name'
    #   sample additional identifier

    timestamp = datetime.now().isoformat('T', 'seconds')

    cursor = newDb.cursor()

    # process classification_id
    if theobj['classification_id'] != 'blank':
        newRow = {}
        newRow['label'] = MATERIAL_LKUP[str(theobj['classification_id'])]['label'].replace('\'', '\'\'')
        if MATERIAL_LKUP[str(theobj['classification_id'])]['description'] != 'blank':
            newRow['description'] = MATERIAL_LKUP[str(theobj['classification_id'])]['description'].replace('\'',
                                                                                                           '\'\'')
        newRow['material_type_id'] = MATERIAL_LKUP[str(theobj['classification_id'])]['material_id']
        newRow['sample_id'] = theobj['sample_id']
        newRow['source'] = 'Legacy data mapped to new vocabulary'
        if MATERIAL_LKUP[str(theobj['classification_id'])]['material_role_id'] != '':
            newRow['material_role_id'] = MATERIAL_LKUP[str(theobj['classification_id'])]['material_role_id']
        # generate insert queries
        result = insertRow(cursor, SampleMaterialTableName, newRow)

    # collector is list of individuals
    if theobj['collector'] != 'blank':
        # process multiple agents for collector,lookup collector list
        # iterate names in collector list for each row,
        # get individual_id for each and add related_agent record
        oneCollector = ''
        multiCollector = ''

        collectorKey = cleanKey(theobj['collector'])
        try:
            oneCollector = AGENT_ID_LKUP[collectorKey]
        except:
            try:
                multiCollector = MULTI_COLLECTOR_LKUP[collectorKey]
            except Exception as e:
                LOGGER.info('no collector, exception: %s', repr(e))
                LOGGER.info('No collector: ' + theobj['collector'])

        if len(oneCollector) != 0:
            # and isinstance(oneCollector['agent_id'], int)
            collectorName = theobj['collector']
            newRow = insert_related_agent_by_name(collectorName, theobj['sample_id'], 1,
                                                  timestamp)
            if len(newRow) != 0:
                if len(newRow) < 7:
                    logging.debug(f'2. related agent too short: {newRow}')
                else:
                    result = insertRow(cursor, RelatedAgentTable, newRow)
                    try:
                        newDb.commit()
                    except Exception as e:
                        LOGGER.info('2. exception: %s', repr(e))
                        LOGGER.info(f'2. collectorName related agent commit fail. {collectorName}')

        elif len(multiCollector) != 0:
            for collectorName in multiCollector:
                newRow = {}
                if collectorName == '':
                    continue
                else:
                    # collectorName = cleanKey(collectorName)
                    newRow = insert_related_agent_by_name(collectorName, theobj['sample_id'], 1,
                                                          timestamp)
                    if len(newRow) != 0:
                        if len(newRow) < 7:
                            print(f'3. related agent too short: {newRow}')
                        else:
                            result = insertRow(cursor, RelatedAgentTable, newRow)
                            try:
                                newDb.commit()
                            except Exception as e:
                                LOGGER.info('3. exception: %s', repr(e))
                                LOGGER.info(f'3. multi collectorName related agent commit fail. {collectorName}')

    #   original_owner.  This should be a SESAR user, so the ID is the same
    if theobj['orig_owner_id'] != 'blank':
        newRow = {}
        origOwnerID = str(theobj['orig_owner_id'])
        try:
            agentName = AGENT_NAME_LKUP[origOwnerID]['label_verbatim']
        except:
            agentName = AGENT_ID_LKUP[origOwnerID]['label_verbatim']

        try:
            newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 2, timestamp)
            if len(newRow) != 0:
                if len(newRow) < 7:
                    print(f'4. related agent too short: {newRow}')
                else:
                    result = insertRow(cursor, RelatedAgentTable, newRow)
                    try:
                        newDb.commit()
                    except Exception as e:
                        LOGGER.info('4. exception: %s', repr(e))
                        LOGGER.info(f'4. origOwnerID related agent commit fail. {newRow}')
        except Exception as e:
            LOGGER.info('Original owner exception: %s', repr(e))
            LOGGER.info('original owner fail, orig_owner_id: ', theobj['orig_owner_id'])

    # Archive lookup.  Point of contact is a role, using related_agent table.  In SESAR db, there is a current_archive
    # and an original archive, these are treated as different related agent. Each has an accompanying point of contact
    # (POC).  Sometimes the archive is an individual, sometimes it is an institution, the POC might be an individual
    # or an institution.  Some individuals or institutions have multiple values; these are flagged in the lookup
    # table as 'multi'.  populated related_agent records with unique combinations of {institution_id, individual_id}
    # where one of this might be null. Some institutions have e-mail address for a curator or other role; these are
    # flagged with individual ID '0', and the e-mail goes in the institution e-mail.  Otherwise e-mail addresses
    # are associated with individuals.
    #   current_archive
    #   original_archive
    try:
        currArchiveKey = cleanKey((theobj['current_archive'] + theobj['current_archive_contact'])
                                  .replace('blank', 'null'))
        if currArchiveKey == 'nullnull':
            currArchiveKey = ''
    except Exception as e:
        currArchiveKey = ''

    try:
        origArchiveKey = cleanKey((theobj['original_archive'] + theobj['original_archive_contact'])
                                  .replace('blank', 'null'))
        if origArchiveKey == 'nullnull':
            origArchiveKey = ''
    except Exception as e:
        origArchiveKey = ''

    if currArchiveKey:
        try:
            thisPOC = ARCHIVE_POC_LKUP[currArchiveKey]
            if len(thisPOC) != 0:
                if thisPOC['individual'] == 'multi':
                    if thisPOC['poc'].lower() != 'null':
                        multiKey = cleanKey(thisPOC['poc'])
                    else:
                        multiKey = cleanKey(thisPOC['archive'])
                    try:
                        multiAgent = MULTI_COLLECTOR_LKUP[multiKey]
                        for agentName in multiAgent:
                            newRow = {}
                            if agentName == '':
                                continue
                            else:
                                newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 3,
                                                                      timestamp)
                                if len(newRow) != 0:
                                    if len(newRow) < 7:
                                        print(f'5. related agent too short: {newRow}')
                                    else:
                                        result = insertRow(cursor, RelatedAgentTable, newRow)
                                        try:
                                            newDb.commit()
                                        except Exception as e:
                                            LOGGER.info('5. exception: %s', repr(e))
                                            LOGGER.info(f'5. multiAgent related agent commit fail. {agentName}')
                    except Exception as e:
                        LOGGER.info('Multi poc key exception: %s', repr(e))
                        LOGGER.info(f"bad multi poc key: {thisPOC['poc']}")
                else:
                    newRow = insert_POC(thisPOC, 3, timestamp, theobj['sample_id'])
                    if len(newRow) != 0:
                        result = insertRow(cursor, RelatedAgentTable, newRow)
                        try:
                            newDb.commit()
                        except Exception as e:
                            LOGGER.info('6. exception: %s', repr(e))
                            LOGGER.info(
                                f'6. currArchiveKey related agent commit fail. ARCHIVE_POC_LKUP[{currArchiveKey}]')
        except Exception as e:
            LOGGER.info('current archive exception: %s', repr(e))
            LOGGER.info(f'bad current archive key: {currArchiveKey}, thisPOC: {thisPOC}')

    if origArchiveKey:
        try:
            thisPOC = ARCHIVE_POC_LKUP[origArchiveKey]
            try:
                if len(thisPOC) != 0:
                    if thisPOC['individual'] == 'multi':
                        # multiKey = cleanKey(thisPOC['poc'])
                        if thisPOC['poc'].lower() != 'null':
                            multiKey = cleanKey(thisPOC['poc'])  # list of names is in contact
                        else:
                            multiKey = cleanKey(thisPOC['archive'])  # list of names is in archive field
                        try:
                            multiAgent = MULTI_COLLECTOR_LKUP[multiKey]
                            # multi collector lookup maps a string to a list of names that are mapped in the
                            #  agentID_lkup.csv table to individual or institution ids.
                            for agentName in multiAgent:
                                newRow = {}
                                if agentName == '':
                                    continue
                                else:
                                    newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 4,
                                                                          timestamp)
                                    if len(newRow) != 0:
                                        if len(newRow) < 7:
                                            print(f'7. related agent too short: {newRow}')
                                        else:
                                            result = insertRow(cursor, RelatedAgentTable, newRow)
                                            try:
                                                newDb.commit()
                                            except Exception as e:
                                                LOGGER.info('7. exception: %s', repr(e))
                                                LOGGER.info(
                                                    f'7. multiAgent POC related agent commit fail. thisPOC: {thisPOC}')
                        except:
                            LOGGER.info(f'bad multi poc key: {multiKey}, thisPOC: {thisPOC}')
                    else:
                        newRow = insert_POC(thisPOC, 4, timestamp, theobj['sample_id'])
                        if len(newRow) != 0:
                            if len(newRow) < 7:
                                print(f'8. related agent too short: {newRow}')
                            else:
                                try:
                                    result = insertRow(cursor, RelatedAgentTable, newRow)
                                    newDb.commit()
                                except Exception as e:
                                    LOGGER.info('8.  %s', repr(e))
                                    LOGGER.info(f'8. origArchiveKey related agent commit fail. {thisPOC}')
            except Exception as e:
                LOGGER.info('thisPOC exception: %s', repr(e))
                LOGGER.info(f'thisPOC process problem: {origArchiveKey}, thisPOC: {thisPOC}')
        except Exception as e:
            LOGGER.info('archive POC lkup exception: %s', repr(e))
            LOGGER.info(f'ARCHIVE_POC_LKUP[origArchiveKey] problem: {origArchiveKey}, thisPOC: {thisPOC}')

    #   req_registrant(798rows )
    if theobj['req_registrant_id'] != 'blank':
        newRow = {}
        agentID = str(theobj['req_registrant_id'])
        try:
            agentName = AGENT_NAME_LKUP[agentID]['label_verbatim']
        except:
            agentName = AGENT_ID_LKUP[agentID]['label_verbatim']

        try:
            newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 5, timestamp)
            if len(newRow) != 0:
                if len(newRow) < 7:
                    print(f'9. related agent too short: {newRow}')
                else:
                    result = insertRow(cursor, RelatedAgentTable, newRow)
                    try:
                        newDb.commit()
                    except Exception as e:
                        LOGGER.info('9.  %s', repr(e))
                        LOGGER.info(f'9. req_registrant_id related agent commit fail. {agentName}')

        except Exception as e:
            LOGGER.info('req registrant exception: %s', repr(e))
            LOGGER.info('req registrant fail, agent_id: ', theobj['agentID'])

    #   last_registrant(~32000 rows)
    if theobj['last_registrant_id'] != 'blank':
        newRow = {}
        agentID = str(theobj['last_registrant_id'])
        try:
            agentName = AGENT_NAME_LKUP[agentID]['label_verbatim']
        except:
            agentName = AGENT_ID_LKUP[agentID]['label_verbatim']

        try:
            newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 6, timestamp)
            if len(newRow) != 0:
                if len(newRow) < 7:
                    print(f'1. related agent too short: {newRow}')
                else:
                    result = insertRow(cursor, RelatedAgentTable, newRow)
                    try:
                        newDb.commit()
                    except Exception as e:
                        LOGGER.info('1. exception: %s', repr(e))
                        LOGGER.info(f'1. last_registrant_id related agent commit fail. {agentName}')
        except Exception as e:
            LOGGER.info('last registrantexception: %s', repr(e))
            LOGGER.info('last registrant fail, agent_id: ', theobj['agentID'])

    #   sample additional name
    if theobj['external_sample_id'] != 'blank' and theobj['external_sample_id'] != theobj['name']:
        newRow = {}
        try:
            newRow['name'] = theobj['external_sample_id'].replace('\'', '\'\'')
            newRow['sample_id'] = theobj['sample_id']
            newRow['name_authority'] = 'not specified'
            # generate insert queries
            result = insertRow(cursor, SampleAdditionalNameTable, newRow)
            newDb.commit()
        except Exception as e:
            LOGGER.info('additional name exception: %s', repr(e))
            LOGGER.info(f"additional name igsn: {theobj['igsn']}, external sample id: {theobj['external_sample_id']}")

    cursor.close()

    return 1


def load_correlation_tables(newDb, data, fl):
    # data contains array of sample data table rows.
    # iterate through legacy sample table
    # TBD: lookup any materials associated with sample through the training data;
    #  import lookup table
    # add sampleMaterial instances for classification_id in sample table
    #   use material_lkup table generated during sample processing
    start_time = time.time()  # time the function execution
    timestamp = datetime.now().isoformat('T', 'seconds')

    SampleMaterialTableName = 'sample_material'
    # process multiple agents for collector,
    RelatedAgentTable = 'related_sample_agent'
    #   sample additional name
    SampleAdditionalNameTable = 'sample_additional_name'
    #   sample additional identifier

    rows = []
    rowNum = 0
    cursor = newDb.cursor()
    for row in data:
        theobj = {}
        # arecord = {}
        for nc in range(len(row)):
            if row[nc] is None:
                theobj[fl[nc]] = 'blank'
                # replace null values with 'blank'
            else:
                theobj[fl[nc]] = row[nc]
        # theobj contains key-value pairs for one data row in the oldDb

        # process classification_id
        if theobj['classification_id'] != 'blank':
            newRow = {}
            newRow['label'] = MATERIAL_LKUP[str(theobj['classification_id'])]['label'].replace('\'', '\'\'')
            if MATERIAL_LKUP[str(theobj['classification_id'])]['description'] != 'blank':
                newRow['description'] = MATERIAL_LKUP[str(theobj['classification_id'])]['description'].replace('\'',
                                                                                                               '\'\'')
            newRow['material_type_id'] = MATERIAL_LKUP[str(theobj['classification_id'])]['material_id']
            newRow['sample_id'] = theobj['sample_id']
            newRow['source'] = 'Legacy data mapped to new vocabulary'
            if MATERIAL_LKUP[str(theobj['classification_id'])]['material_role_id'] != '':
                newRow['material_role_id'] = MATERIAL_LKUP[str(theobj['classification_id'])]['material_role_id']
            # generate insert queries
            result = insertRow(cursor, SampleMaterialTableName, newRow)

        # collector is list of individuals
        if theobj['collector'] != 'blank':
            # process multiple agents for collector,lookup collector list
            # iterate names in collector list for each row,
            # get individual_id for each and add related_agent record
            oneCollector = ''
            multiCollector = ''

            collectorKey = cleanKey(theobj['collector'])
            try:
                oneCollector = AGENT_ID_LKUP[collectorKey]
            except:
                try:
                    multiCollector = MULTI_COLLECTOR_LKUP[collectorKey]
                except Exception as e:
                    LOGGER.info('no collector, exception: %s', repr(e))
                    LOGGER.info('No collector: ' + theobj['collector'])

            if len(oneCollector) != 0:
                # and isinstance(oneCollector['agent_id'], int)
                collectorName = theobj['collector']
                newRow = insert_related_agent_by_name(collectorName, theobj['sample_id'], 1,
                                                      timestamp)
                if len(newRow) != 0:
                    if len(newRow) < 7:
                        logging.debug(f'2. related agent too short: {newRow}')
                    else:
                        result = insertRow(cursor, RelatedAgentTable, newRow)
                        try:
                            newDb.commit()
                        except Exception as e:
                            LOGGER.info('2. exception: %s', repr(e))
                            LOGGER.info(f'2. collectorName related agent commit fail. {collectorName}')

            elif len(multiCollector) != 0:
                for collectorName in multiCollector:
                    newRow = {}
                    if collectorName == '':
                        continue
                    else:
                        # collectorName = cleanKey(collectorName)
                        newRow = insert_related_agent_by_name(collectorName, theobj['sample_id'], 1,
                                                              timestamp)
                        if len(newRow) != 0:
                            if len(newRow) < 7:
                                print(f'3. related agent too short: {newRow}')
                            else:
                                result = insertRow(cursor, RelatedAgentTable, newRow)
                                try:
                                    newDb.commit()
                                except Exception as e:
                                    LOGGER.info('3. exception: %s', repr(e))
                                    LOGGER.info(f'3. multi collectorName related agent commit fail. {collectorName}')

        #   original_owner.  This should be a SESAR user, so the ID is the same
        if theobj['orig_owner_id'] != 'blank':
            newRow = {}
            origOwnerID = str(theobj['orig_owner_id'])
            try:
                agentName = AGENT_NAME_LKUP[origOwnerID]['label_verbatim']
            except:
                agentName = AGENT_ID_LKUP[origOwnerID]['label_verbatim']

            try:
                newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 2, timestamp)
                if len(newRow) != 0:
                    if len(newRow) < 7:
                        print(f'4. related agent too short: {newRow}')
                    else:
                        result = insertRow(cursor, RelatedAgentTable, newRow)
                        try:
                            newDb.commit()
                        except Exception as e:
                            LOGGER.info('4. exception: %s', repr(e))
                            LOGGER.info(f'4. origOwnerID related agent commit fail. {newRow}')
            except Exception as e:
                LOGGER.info('Original owner exception: %s', repr(e))
                LOGGER.info('original owner fail, orig_owner_id: ', theobj['orig_owner_id'])

        # Archive lookup.  Point of contact is a role, using related_agent table.  In SESAR db, there is a current_archive
        # and an original archive, these are treated as different related agent. Each has an accompanying point of contact
        # (POC).  Sometimes the archive is an individual, sometimes it is an institution, the POC might be an individual
        # or an institution.  Some individuals or institutions have multiple values; these are flagged in the lookup
        # table as 'multi'.  populated related_agent records with unique combinations of {institution_id, individual_id}
        # where one of this might be null. Some institutions have e-mail address for a curator or other role; these are
        # flagged with individual ID '0', and the e-mail goes in the institution e-mail.  Otherwise e-mail addresses
        # are associated with individuals.
        #   current_archive
        #   original_archive
        try:
            currArchiveKey = cleanKey((theobj['current_archive'] + theobj['current_archive_contact'])
                                      .replace('blank', 'null'))
            if currArchiveKey == 'nullnull':
                currArchiveKey = ''
        except Exception as e:
            currArchiveKey = ''

        try:
            origArchiveKey = cleanKey((theobj['original_archive'] + theobj['original_archive_contact'])
                                      .replace('blank', 'null'))
            if origArchiveKey == 'nullnull':
                origArchiveKey = ''
        except Exception as e:
            origArchiveKey = ''

        if currArchiveKey:
            try:
                thisPOC = ARCHIVE_POC_LKUP[currArchiveKey]
                if len(thisPOC) != 0:
                    if thisPOC['individual'] == 'multi':
                        if thisPOC['poc'].lower() != 'null':
                            multiKey = cleanKey(thisPOC['poc'])
                        else:
                            multiKey = cleanKey(thisPOC['archive'])
                        try:
                            multiAgent = MULTI_COLLECTOR_LKUP[multiKey]
                            for agentName in multiAgent:
                                newRow = {}
                                if agentName == '':
                                    continue
                                else:
                                    newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 3,
                                                                          timestamp)
                                    if len(newRow) != 0:
                                        if len(newRow) < 7:
                                            print(f'5. related agent too short: {newRow}')
                                        else:
                                            result = insertRow(cursor, RelatedAgentTable, newRow)
                                            try:
                                                newDb.commit()
                                            except Exception as e:
                                                LOGGER.info('5. exception: %s', repr(e))
                                                LOGGER.info(f'5. multiAgent related agent commit fail. {agentName}')
                        except Exception as e:
                            LOGGER.info('Multi poc key exception: %s', repr(e))
                            LOGGER.info(f"bad multi poc key: {thisPOC['poc']}")
                    else:
                        newRow = insert_POC(thisPOC, 3, timestamp, theobj['sample_id'])
                        if len(newRow) != 0:
                            result = insertRow(cursor, RelatedAgentTable, newRow)
                            try:
                                newDb.commit()
                            except Exception as e:
                                LOGGER.info('6. exception: %s', repr(e))
                                LOGGER.info(
                                    f'6. currArchiveKey related agent commit fail. ARCHIVE_POC_LKUP[{currArchiveKey}]')
            except Exception as e:
                LOGGER.info('current archive exception: %s', repr(e))
                LOGGER.info(f'bad current archive key: {currArchiveKey}, thisPOC: {thisPOC}')

        if origArchiveKey:
            try:
                thisPOC = ARCHIVE_POC_LKUP[origArchiveKey]
                try:
                    if len(thisPOC) != 0:
                        if thisPOC['individual'] == 'multi':
                            # multiKey = cleanKey(thisPOC['poc'])
                            if thisPOC['poc'].lower() != 'null':
                                multiKey = cleanKey(thisPOC['poc'])  # list of names is in contact
                            else:
                                multiKey = cleanKey(thisPOC['archive'])  # list of names is in archive field
                            try:
                                multiAgent = MULTI_COLLECTOR_LKUP[multiKey]
                                # multi collector lookup maps a string to a list of names that are mapped in the
                                #  agentID_lkup.csv table to individual or institution ids.
                                for agentName in multiAgent:
                                    newRow = {}
                                    if agentName == '':
                                        continue
                                    else:
                                        newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 4,
                                                                              timestamp)
                                        if len(newRow) != 0:
                                            if len(newRow) < 7:
                                                print(f'7. related agent too short: {newRow}')
                                            else:
                                                result = insertRow(cursor, RelatedAgentTable, newRow)
                                                try:
                                                    newDb.commit()
                                                except Exception as e:
                                                    LOGGER.info('7. exception: %s', repr(e))
                                                    LOGGER.info(
                                                        f'7. multiAgent POC related agent commit fail. thisPOC: {thisPOC}')
                            except:
                                LOGGER.info(f'bad multi poc key: {multiKey}, thisPOC: {thisPOC}')
                        else:
                            newRow = insert_POC(thisPOC, 4, timestamp, theobj['sample_id'])
                            if len(newRow) != 0:
                                if len(newRow) < 7:
                                    print(f'8. related agent too short: {newRow}')
                                else:
                                    try:
                                        result = insertRow(cursor, RelatedAgentTable, newRow)
                                        newDb.commit()
                                    except Exception as e:
                                        LOGGER.info('8.  %s', repr(e))
                                        LOGGER.info(f'8. origArchiveKey related agent commit fail. {thisPOC}')
                except Exception as e:
                    LOGGER.info('thisPOC exception: %s', repr(e))
                    LOGGER.info(f'thisPOC process problem: {origArchiveKey}, thisPOC: {thisPOC}')
            except Exception as e:
                LOGGER.info('archive POC lkup exception: %s', repr(e))
                LOGGER.info(f'ARCHIVE_POC_LKUP[origArchiveKey] problem: {origArchiveKey}, thisPOC: {thisPOC}')

        #   req_registrant(798rows )
        if theobj['req_registrant_id'] != 'blank':
            newRow = {}
            agentID = str(theobj['req_registrant_id'])
            try:
                agentName = AGENT_NAME_LKUP[agentID]['label_verbatim']
            except:
                agentName = AGENT_ID_LKUP[agentID]['label_verbatim']

            try:
                newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 5, timestamp)
                if len(newRow) != 0:
                    if len(newRow) < 7:
                        print(f'9. related agent too short: {newRow}')
                    else:
                        result = insertRow(cursor, RelatedAgentTable, newRow)
                        try:
                            newDb.commit()
                        except Exception as e:
                            LOGGER.info('9.  %s', repr(e))
                            LOGGER.info(f'9. req_registrant_id related agent commit fail. {agentName}')

            except Exception as e:
                LOGGER.info('req registrant exception: %s', repr(e))
                LOGGER.info('req registrant fail, agent_id: ', theobj['agentID'])

        #   last_registrant(~32000 rows)
        if theobj['last_registrant_id'] != 'blank':
            newRow = {}
            agentID = str(theobj['last_registrant_id'])
            try:
                agentName = AGENT_NAME_LKUP[agentID]['label_verbatim']
            except:
                agentName = AGENT_ID_LKUP[agentID]['label_verbatim']

            try:
                newRow = insert_related_agent_by_name(agentName, theobj['sample_id'], 6, timestamp)
                if len(newRow) != 0:
                    if len(newRow) < 7:
                        print(f'1. related agent too short: {newRow}')
                    else:
                        result = insertRow(cursor, RelatedAgentTable, newRow)
                        try:
                            newDb.commit()
                        except Exception as e:
                            LOGGER.info('1. exception: %s', repr(e))
                            LOGGER.info(f'1. last_registrant_id related agent commit fail. {agentName}')
            except Exception as e:
                LOGGER.info('last registrantexception: %s', repr(e))
                LOGGER.info('last registrant fail, agent_id: ', theobj['agentID'])

        #   sample additional name
        if theobj['external_sample_id'] != 'blank' and theobj['external_sample_id'] != theobj['name']:
            newRow = {}
            try:
                newRow['name'] = theobj['external_sample_id'].replace('\'', '\'\'')
                newRow['sample_id'] = theobj['sample_id']
                newRow['name_authority'] = 'not specified'
                # generate insert queries
                result = insertRow(cursor, SampleAdditionalNameTable, newRow)
                newDb.commit()
            except Exception as e:
                LOGGER.info('additional name exception: %s', repr(e))
                LOGGER.info(
                    f"additional name igsn: {theobj['igsn']}, external sample id: {theobj['external_sample_id']}")

        #   sample additional name
        # if theobj['field_name'] != 'blank':
        #     newRow = {}
        #     try:
        #         newRow['name'] = theobj['field_name'].replace('\'', '\'\'')
        #         newRow['sample_id'] = theobj['sample_id']
        #         # generate insert queries
        #         result = insertRow(cursor, SampleAdditionalNameTable, newRow)
        #     except Exception as e:
        #         LOGGER.info('additional name exception: %s', repr(e))
        #         LOGGER.info(
        #             f"additional name fail, sample_id {theobj['sample_id']}. field_name: {theobj['field_name']}")

        try:
            newDb.commit()
        except Exception as e:
            LOGGER.info('load correlation commit exception: %s', repr(e))
            LOGGER.info(f'load correlation commit fail. ')

        rowNum = rowNum + 1
        if rowNum % 10000 == 0:
            # newDb.commit()  already done
            LOGGER.debug(f'load_correlation_tables, rowNum: {rowNum}')

    end_time = time.time()
    execution_time = end_time - start_time
    LOGGER.info(f"load correlation tables execution time: {execution_time} seconds")
    return 1


def load_sample_relations(newDb, oldDb, data, fl):
    start_time = time.time()  # time the function execution
    RelatedResourceTable = 'related_resource'
    rows = []
    rowNum = 0
    cursor = newDb.cursor()
    for row in data:
        theobj = {}
        for nc in range(len(row)):
            if row[nc] is None:
                theobj[fl[nc]] = 'blank'
                # replace null values with 'blank'
            else:
                theobj[fl[nc]] = row[nc]
        # external parent sample not registered in SESAR
        if theobj['external_parent_name'] != 'blank':
            newRow = {}
            try:
                typelabel = ''
                if theobj['external_parent_sample_type_id'] != 'blank':
                    typelabel = SAMPLE_TYPE_LKUP[theobj['external_parent_sample_type_id']]['label']
                newRow['relation_label'] = ('external parent sample:' + typelabel + ': ' +
                                            theobj['external_parent_name'].replace('\'', '\'\''))[:100]
                newRow['related_resource_uri'] = ('urn:publicid:' + theobj['external_parent_name']
                                                  .replace('\'', '\'\''))[:254]
                # the urn:publicid (which is registered at https://www.rfc-editor.org/rfc/rfc3151.html
                #  is just to make the name a more legit URI
                newRow['relation_type_id'] = 1
                newRow['related_resource_type_id'] = 26
                # theobj)['external_parent_sample_type_id'] urn:publicid:
                newRow['sample_id'] = theobj['sample_id']
                # generate insert queries
                result = insertRow(cursor, RelatedResourceTable, newRow)
            except Exception as e:
                LOGGER.info('parent resource exception: %s', repr(e))
                LOGGER.info(
                    f"external parent resource, sample_id {theobj['sample_id']}. external_parent_name: {theobj['external_parent_name']}")

        # parent sample,  registered in SESAR
        if theobj['origin_sample_id'] != 'blank':
            newRow = {}
            try:
                thequery = 'SELECT distinct origin.igsn, origin.name, ' + \
                           'origin.sample_type_id from sample ' + \
                           'join sample as origin on origin.sample_id = sample.origin_sample_id ' + \
                           'where sample.origin_sample_id = ' + str(theobj['origin_sample_id'])

                try:
                    qres = executeQuery(oldDb, thequery)
                    parentinfo = qres[0]
                except Exception as e:
                    LOGGER.info('parent query exception: %s', repr(e))
                    LOGGER.info(
                        f"parent query fail, sample_id {theobj['sample_id']}, origin_sample_id: {theobj['origin_sample_id']}")

                typelabel = SAMPLE_TYPE_LKUP[parentinfo[2]]['label']

                newRow['relation_label'] = ('parent sample:' + str(typelabel) + ': ' +
                                            parentinfo[1].replace('\'', '\'\''))[:100]
                newRow['related_resource_uri'] = 'igsn:' + parentinfo[0]
                newRow['relation_type_id'] = 1
                newRow['related_resource_type_id'] = 26
                # theobj)['external_parent_sample_type_id']
                newRow['sample_id'] = theobj['sample_id']
                newRow['related_sesar_sample_id'] = theobj['origin_sample_id']
                # generate insert queries
                result = insertRow(cursor, RelatedResourceTable, newRow)
            except Exception as e:
                LOGGER.info('parent resource exception: %s', repr(e))
                LOGGER.info(
                    f"parent resource, sample_id {theobj['sample_id']}. Origin sampleID: {theobj['origin_sample_id']}")

            thequery = "UPDATE public.sample SET  parent_sample_id= '" + str(theobj['origin_sample_id']) + \
                   "' WHERE sample_id = '" + str(theobj['sample_id'])+ "';"
            try:
                cursor.execute(thequery)
            except Exception as e:
                LOGGER.info(f'update parent_sample_id fail {repr(e)}')

        try:
            newDb.commit()
        except Exception as e:
            LOGGER.info('related resource commit exception: %s', repr(e))
        rowNum = rowNum + 1
        if rowNum % 10000 == 0:
            LOGGER.debug(f'load sample relation, rowNum: {rowNum}')

    newDb.commit()  # commit any thing not committed yet.
    end_time = time.time()
    execution_time = end_time - start_time
    LOGGER.info(f"load sample relation table execution time: {execution_time} seconds")
    if cursor:
        cursor.close()
    return 1


def copy_table(PK_LKUP, newDb, oldDb, newTableName, oldTableName, purgeflag=False, cascade=False):
    fl = getFields(oldDb, oldTableName)
    try:
        if purgeflag:
            result = truncateTable(newDb, newTableName, cascade)
        oldbcursor = oldDb.cursor()
        oldbcursor.execute(f"SELECT * FROM {oldTableName}")
        rows = oldbcursor.fetchall()
    except Exception as e:
        LOGGER.info(f'copy table exception, select {oldTableName}; exception {repr(e)}')
        oldbcursor.close()
        return 0
    cursor = newDb.cursor()
    rowNum = 0
    for row in rows:
        theobj = {}
        newRow = {}
        for nc in range(len(row)):
            if row[nc] == 0:
                newRow[fl[nc]] = row[nc]
            elif (fl[nc] == 'first_name' or fl[nc] == 'last_name' or fl[nc] == 'email') and not (row[nc]):
                newRow[fl[nc]] = 'missing'  # missing required values in legacy data
            elif (fl[nc] == 'sample_id') and (newTableName == 'sample_publication_url') and not (row[nc]):
                newRow[fl[nc]] = ''  # some sample_pub_url records are missing sample_id to link to a sample, skip these
            elif (fl[nc] == 'sample_id') and (newTableName == 'permission') and not (row[nc]):
                newRow[fl[nc]] = 1266  # sample_id is FK in permission, but all values are NULL in legacy
            elif row[nc]:
                if fl[nc] != 'sample_additional_name_id':  # additional names are added during sample processing
                    # so autoincrement ids copied from legacy db.
                    newRow[fl[nc]] = row[nc]

        # newRow contains key-value pairs for one data row in the oldDb
        try:
            if (('sample_id' in fl) and newRow['sample_id']) or (not ('sample_id' in fl)):
                result = insertRow(cursor, newTableName, newRow, PK_LKUP)
                newDb.commit()
        except Exception as e:
            LOGGER.info(f'copy {newTableName} insert row exception, {repr(e)}')

        rowNum = rowNum + 1
        LOGGER.debug('rowNum: ', rowNum)
    oldbcursor.close()
    cursor.close()
    return 1


# ******************************************************************
#  EXECUTION STARTs HERE  *****************************************

def main():
    tstart_time = time.time()

    purgeAllFlag = False
    # configure what should get processed
    # all purges turned off; the Truncate  .... CASCADE keep deleting
    #  stuff from tables I don't want to purge...
    # So just do one big purge at start.
    loadVocabs = True
    purgeVocsFlag = False
    loadsample = True
    purgeSampleFlag = False
    loadsamplerelations = True
    purgeSamRelFlag = False
    copyTables = True

    # LOG_LEVELS = {
    #     "DEBUG": logging.DEBUG,
    #     "INFO": logging.INFO,
    #     "WARNING": logging.WARNING,
    #     "WARN": logging.WARNING,
    #     "ERROR": logging.ERROR,
    #     "FATAL": logging.CRITICAL,
    #     "CRITICAL": logging.CRITICAL,
    # }

    logging.basicConfig(filename='migration.log', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    timestamp = datetime.now().isoformat('T', 'seconds')
    LOGGER.info(f'Started, time: {timestamp}')

    # database connection is global variable.
    oldDb = get_legacyConnection()
    if oldDb:
        print("Connection to the Legacy PostgreSQL database established successfully.")
    else:
        print("Connection to the Legacy PostgreSQL database encountered and error.")
        exit()

    # database connection is global variable.
    newDb = get_2024Connection()
    if newDb:
        print("Connection to SESAR2025 PostgreSQL database established successfully.")
    else:
        print("Connection to SESAR2025 PostgreSQL encountered an error.")
        exit()

    # set up to process a table

    if purgeAllFlag:
        # tables = ['affiliation_type','agent_role_type']
        tables = ['sampled_feature_type', 'locality', 'sample', 'sample_type',
                  'sampling_method', 'geologic_time_scale',
                  'collection_type', 'initiative_type', 'initiative',
                  'country', 'material_type', 'launch_type', 'platform',
                  'platform_type', 'location_method', 'sesar_user', 'relation_type',
                  'related_resource', 'resource_type', 'property_type', 'other_property',
                  'sample_additional_name', 'sesar_spatial_ref_sys',
                  'sample_material', 'related_local_doc', 'geospatial_location', 'sample_collection',
                  'collection_member', 'institution_type', 'institution', 'individual',
                  'material_role_type', 'affiliation_type', 'affiliation',
                  'parent_institution', 'agent_role_type', 'related_sample_agent', 'sample_additional_name',
                  'sample_doc', 'sample_publication_url', 'sesar_user_code', 'auth_group',
                  'auth_group_permissions', 'auth_permission', 'auth_user', 'auth_user_groups',
                  'auth_user_user_permissions',
                  'public.group', 'permission', 'transfer_history', 'sesar_role', 'group_member', 'django_content_type']
        #    tables = ['sample',  'geospatial_location', 'parent_institution', 'related_sample_agent']
        result = cleanDb(newDb, tables, cascade=True)
        if result == 1:
            newDb.commit()  # don't commit until all done
    if loadVocabs:
        # first load vocabularies
        voctimestamp = time.time()
        if purgeVocsFlag:
            tables = ['sampled_feature_type', 'locality', 'sample_type',
                      'sampling_method', 'geologic_time_scale', 'institution_type',
                      'collection_type', 'initiative_type', 'initiative', 'individual',
                      'institution',
                      'country', 'material_type', 'launch_type', 'platform', 'material_role_type',
                      'platform_type', 'location_method', 'sesar_user', 'sesar_spatial_ref_sys', 'relation_type',
                      'resource_type', 'affiliation_type', 'property_type', 'agent_role_type']
            #    tables = ['sample',  'geospatial_location', 'parent_institution', 'related_sample_agent']
            result = cleanDb(newDb, tables)
            newDb.commit()
        # agent affiliation type
        result = load_affiliation_type(newDb)
        if result == 1:
            print("Affiliation")
        # agent role type
        result = load_agent_role_type(newDb)
        if result == 1:
            print("Agent Role")
        # collection_type
        # country
        result = load_country(newDb)
        print('load country done')
        # geologic_time_scale
        result = load_geologic_time_scale(newDb)
        print('load geologic time scale done')
        # initiative type
        result = load_initiative_type(newDb)
        print('load initiative type done')
        # institution Type
        result = load_institution_type(newDb)
        print('load institution type done')
        # launch type
        result = load_launch_type(newDb)
        print('load launch type done')
        # location method
        result = load_location_method(newDb)
        print('load location method done')
        # material role
        result = load_material_role(newDb)
        print('load material role done')
        # material type
        result = load_material_type(newDb)
        print('load material type done')
        # platform type
        result = load_platform_type(newDb)
        print('load platform type done')
        # property type
        # relation type
        result = load_relation_type(newDb)
        print('load relation type done')
        # resource type
        result = load_resource_type(newDb)
        print('load resource type done')
        # sample type
        result = load_sample_type(newDb)
        print('load sample type done')
        # sampled feature type
        result = load_sampled_feature_type(newDb)
        print('load sampled feature type done')
        # SESAR spatial reference system vocab
        result = load_spatial_ref_sys(newDb)
        print('load spatial reference system vocab done')

        # locality
        print('start load locality')
        result = load_locality(newDb)
        print('load locality done')
        # sampling method
        result = load_sampling_method(newDb)
        print('load sampling method done')

        # Agents are loaded from the agentsMapping.xlsx workbook
        # to load individual:
        result = load_individual(newDb)
        print('load individual done')

        # load group from sesar_user_group tab.  This includes non-institution groups as well as institutions that
        #    have a SESAR user ID and also appear in institution table.  For these assign group owner=Kerstin id=75 (sesar user id)
        # result = load_group() ??? check TBD??
        #  next load organizations from unique_org_all (exported to institutionvocab.csv)
        result = load_institution(newDb)
        print('load institution done')
        # load affiliations for individuals
        #
        # sesar_user is loaded from the old db table, except that sesar_users must map to either
        # an individual or a group.  simplest course here seems like lookup the individual or group id for each
        # sesar_user id. generate the lookup table in excel.  Sesar User also has a single affiliation to an institution
        # this requires lookup from label in sesar user table through OrgLKUP tab in agentsMapping.xlsx to get the
        # normalized institution name, and then to unique_org_all to get the institution_id.
        result = load_sesar_user(newDb)
        print('load sesar user done')
        # load initiatives (cruise, field program etc.
        result = load_initiative(newDb)
        print('load initiative done')
        # load platform
        result = load_platform(newDb)
        print('load platform done')

        tend_time = time.time()
        execution_time = tend_time - voctimestamp
        LOGGER.info(f'load vocabs run time: {execution_time / 60} minutes')

    # then the big one-- loop over samples, and update related table

    tableName = 'sample'
    fl = getFields(oldDb, tableName)
    LOGGER.debug(f'{tableName} fields: {fl}')
    print('start processing sample, get the data')

    # process legacy data in batches
    batch_size = 100000
    # batch_size = 10   # for debugging

    maxIDQuery = "SELECT max(sample_id) FROM public.sample"
    try:
        result = executeQuery(oldDb, maxIDQuery)
        sample_max_id = result[0][0]
    except:
        data = {}
        sample_max_id = 0

    if loadsample:
        samtimestamp = time.time()
        if purgeSampleFlag:
            tables = ['other_property',
                      'sample_additional_name',
                      'sample_material', 'related_local_doc', 'geospatial_location', 'sample_collection',
                      'collection_member', 'related_sample_agent', 'sample']
            #    tables = ['sample',  'geospatial_location', 'parent_institution', 'related_sample_agent']
            result = cleanDb(newDb, tables)
            newDb.commit()
        # run through all samples, load sample table, geospatial locations, and
        # relations between sample and agents or vocabularies

        result = load_lookups()
        print('start load the sample table')
        PK_LKUP = pk_lkup(newDb)

        max_id = 0  # starting value
        # max_id = 5128239
        while True:
            selectRecordQuery = 'SELECT * FROM public.' + tableName + ' where sample_id > ' + str(max_id) + \
                                '  order by sample_id ' + \
                                '  LIMIT ' + str(batch_size) + ';'
            LOGGER.debug("get_sample_data record query: ", repr(selectRecordQuery))
            try:
                data = executeQuery(oldDb, selectRecordQuery)
            except:
                LOGGER.info('get_sample_data data query failed')
                break

            selectMaxQuery = "SELECT max(subset.sample_id) FROM (select * from public." + tableName + \
                             " where sample_id > " + str(max_id) + \
                             "  order by sample_id " + \
                             "  LIMIT " + str(batch_size) + ") as subset;"
            LOGGER.debug("get_sample_data max sample_id query: ", repr(selectMaxQuery))
            try:
                result = executeQuery(oldDb, selectMaxQuery)
                max_id = result[0][0]
            except:
                LOGGER.info('get_max sample ID failed')
                break
            LOGGER.debug(f'got sample data, start at max_id {max_id}')

            result = load_sample(newDb, data, fl)
            print(f'load sample done. new max_id: {max_id}')
            if result == 0:
                sys.exit("load sample failed")

            # other foreign keys to vocab tables:
            # geospatial locations (for non- lat-long coordinate locations), has FK constraint to sample_id.
            # result = insert_geospatial_location(newDb, data, fl)
            # print('insert geospatial location done')
            #
            # correlation tables:
            #   sample additional name, sample additional identifier,
            #   sample related_sample_agent correlation, sample materials
            # result = load_correlation_tables(newDb, data, fl)
            # print(f'load correlation tables done, max_id: {max_id}')
            LOGGER.info(f'load iteration done. max_id: {max_id}')
            if max_id == sample_max_id:
                print(f'load sample loop done. break')
                result = 1
                break

        tend_time = time.time()
        execution_time = tend_time - samtimestamp
        LOGGER.info(f'load sample run time: {execution_time / 60} minutes')
        # end load sample loop here
    # *************************************************************

    # then do it again to add related_resource links between
    # samples; can't do this until all samples are loaded

    if loadsamplerelations:
        #   parent sample via related_resource table
        print('start processing sample relations')
        reltimestamp = time.time()
        if purgeSamRelFlag:
            tables = ['related_resource']
            result = cleanDb(newDb, tables)
            newDb.commit()
        if not loadsample:
            result = load_lookups()

        maxIDQuery = "SELECT max(sample_id) FROM public.sample " + \
            "where ((external_parent_name is not null) or (origin_sample_id is not null))"
        try:
            result = executeQuery(oldDb, maxIDQuery)
            sample_max_id = result[0][0]
        except:
            data = {}
            sample_max_id = 0

        max_id = 0  # starting value
        # max_id = 3600015  (for debugging, set start sample_id...)
        # sample relations loop
        while True:
            # data = get_sample_data_batch(tableName, max_id, oldDb, batch_size)
            selectRecordQuery = 'SELECT * FROM public.' + tableName + \
                                ' where (sample_id > ' + str(max_id) + ') and ' + \
                    '((external_parent_name is not null) or (origin_sample_id is not null)) ' + \
                                '  order by sample_id ' + \
                                '  LIMIT ' + str(batch_size) + ';'
            LOGGER.debug("sample relations, get_sample_data record query: ", repr(selectRecordQuery))
            try:
                data = executeQuery(oldDb, selectRecordQuery)
            except Exception as e:
                LOGGER.info(f'sample relations, get_sample_data data query failed, exception {repr(e)}')
                LOGGER.info(f'sample relations query fail query: {selectRecordQuery}')
                break

            selectMaxQuery = "SELECT max(subset.sample_id) FROM (select * from public." + tableName + \
                             " where (sample_id > " + str(max_id) + ") and " + \
                             "((external_parent_name is not null) or (origin_sample_id is not null)) " + \
                             "  order by sample_id " + \
                             "  LIMIT " + str(batch_size) + ") as subset;"
            LOGGER.debug("sample relation, get_sample_data max sample_id query: ", repr(selectMaxQuery))
            try:
                result = executeQuery(oldDb, selectMaxQuery)
                max_id = result[0][0]
            except:
                LOGGER.info('get_max sample ID failed')
                break
            LOGGER.debug(f'got sample data, start at max_id {max_id}')

            result = load_sample_relations(newDb, oldDb, data, fl)

            if max_id == sample_max_id:
                print(f'load sample relations done. break')
                result = 1
                break
        tend_time = time.time()
        execution_time = tend_time - reltimestamp
        LOGGER.info(f'load parent links run time: {execution_time / 60} minutes')

    # copy these tables whole cloth, after loading samples so FK to sample_id is valid
    #  don't commit to newDb until all done to defer FK checking
    if copyTables:
        copytimestamp = time.time()
        PK_LKUP = pk_lkup(newDb)  # need the pk's for insert or update on copy
        #  that way, don't need to purge all the admin tables and deal with the colliding FKs
        tables = ['sample_doc', 'sample_publication_url', 'sesar_user_code', 'auth_group',
                  'auth_group_permissions', 'auth_permission', 'auth_user', 'auth_user_groups',
                  'auth_user_user_permissions',
                  'public.group', 'permission', 'transfer_history', 'sesar_role', 'group_member', 'django_content_type']
        # result = cleanDb(newDb, tables, cascade=False)
        # newDb.commit()  # don't commit until all done

        result = copy_table(PK_LKUP, newDb, oldDb, 'sample_doc', 'sample_doc', False)
        print('copy sample_doc done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'sample_publication_url', 'sample_publication_url', False)
        print('copy sample_publication_url done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'sample_additional_name', 'sample_additional_name', False)
        print('copy sample_additional_name done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'django_content_type', 'django_content_type', False)
        print('copy django_content_type done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'auth_group', 'auth_group', False)
        print('copy auth_group done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'auth_permission', 'auth_permission', False)
        print('copy auth_permission done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'auth_group_permissions', 'auth_group_permissions', False)
        print('copy auth_group_permissions done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'auth_user_groups', 'auth_user_groups', False)
        print('copy auth_user_groups done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'auth_user_user_permissions', 'auth_user_user_permissions', False)
        print('copy auth_user_user_permissions done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'auth_user', 'auth_user', False)
        print('copy auth_user done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'public.group', 'public.group', False)
        print('copy group done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'sesar_role', 'sesar_role', False)
        print('copy sesar_role done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'sesar_user_code', 'sesar_user_code', False)
        print('copy sesar_user_code done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'permission', 'permission', False)
        print('copy permission done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'transfer_history', 'transfer_history', False)
        print('copy transfer_history done')
        result = copy_table(PK_LKUP, newDb, oldDb, 'group_member', 'group_member', False)
        print('copy group_member done')
        tend_time = time.time()
        execution_time = tend_time - copytimestamp
        LOGGER.info(f'copy tables run time: {execution_time / 60} minutes')

    if result == 1:
        newDb.commit()  # don't commit until all done
        print("done with loading sample data")
    else:
        print("done, loading sample data fail")
    #
    tend_time = time.time()
    execution_time = tend_time - tstart_time
    LOGGER.info(f'total run time: {execution_time / 60} minutes')

    oldDb.close()
    newDb.close()


if __name__ == "__main__":
    main()
