import psycopg2
import requests
import pandas
import sqlalchemy


def get_legacyConnection():
    try:
        return psycopg2.connect(
            database="sesardb20240525",
            user="postgres",
            password="smrpostgis",
            host="127.0.0.1",
            port=5432,
        )
    except:
        return False


def get_2024Connection():
    try:
        return psycopg2.connect(
            database="SESAR2024",
            user="postgres",
            password="smrpostgis",
            host="127.0.0.1",
            port=5432,
        )
    except:
        return False


def executeQuery(conn, querystring):
    # CREATE A CURSOR USING THE CONNECTION OBJECT
    curr = conn.cursor()
    # EXECUTE THE SQL QUERY
    curr.execute(querystring)
    # FETCH ALL THE ROWS FROM THE CURSOR
    data = curr.fetchall()
    return data


def getFields(conn, tableName):
    #  get field names for table
    fieldsquery = "SELECT column_name,ordinal_position " \
                  "FROM information_schema.columns " + \
                  "WHERE table_schema = 'public' AND table_name = '" + \
                  tableName + "' ORDER BY ordinal_position"
    print(fieldsquery)
    fields = executeQuery(conn, fieldsquery)

    fieldlist = []
    for row in fields:
        fieldlist.append(row[0])
    return fieldlist


def getTableData(conn, tableName, tablePK):
    fl = getFields(conn, tableName)
    print(tableName, " fields ", fl)
    selectRecordQuery = "SELECT * FROM public." + tableName
    # print("record query: ", selectRecordQuery)

    data = executeQuery(conn, selectRecordQuery)
    # do something with THE RECORDS
    print(tableName, " number of records: ", len(data))

    theDict = {}
    rows = []
    rowNum = 0
    for row in data:
        theobj = {}
        arecord = {}
        for nc in range(len(row)):
            if row[nc] is None:
                # don't put null values in JSON
                continue
            theobj[fl[nc]] = row[nc]
        # if tablePK=='noPK':
        #    arecord['id'+str(rowNum)]=theobj
        # else:
        #    arecord[theobj[tablePK]]=theobj
        # print(arecord)
        # rows.append(arecord)
        rows.append(theobj)
        rowNum = rowNum + 1

    # print(rows)
    theDict[tableName] = rows
    return theDict


def getPrimaryKey(conn, tableName):
    pkquery = "SELECT c.column_name " + \
              " FROM information_schema.key_column_usage AS c " + \
              " LEFT JOIN information_schema.table_constraints AS t " + \
              " ON t.constraint_name = c.constraint_name " + \
              " WHERE t.table_name = '" + tableName + "' AND t.constraint_type = 'PRIMARY KEY'; "
    # print(pkquery)
    key = executeQuery(conn, pkquery)
    print("the primary key: ", key)
    if len(key) == 0:
        return "noPK"
    else:
        return key[0][0]


def purgeTable(conn, tableName):
    # this is tricky because of foreign key constraints
    pkquery = "TRUNCATE " + tableName + ""
    try:
        key = executeQuery(conn, pkquery)
    except:
        print("Purge fail: ", tableName)
        return "purge fail"
    return 1


# *******************************************************************
# ******************************************************************
# functions to process tables

def load_launch_type():
    # table: launch_type.  Simple copy from olddb to newdb, field order is the same,
    #  but new launch_type table has a source field, so have to append this in dictionary
    #  with a default value 'missing'.
    tableName = 'launch_type'
    newTableName = 'launch_type'
    thepk = getPrimaryKey(oldDb, tableName)
    print('table: ', tableName, ' primaryKey: ', thepk)

    theDict = getTableData(oldDb, tableName, thepk)
    for row in theDict[tableName]:
        row['source'] = 'missing'

    # print(list(theDict[tableName][1].values()))
    # newDb.autocommit = True
    cursor = newDb.cursor()
    for anobj in theDict[tableName]:
        thevalues = list(anobj.values())
        insertvalues = '('
        for val in thevalues:
            if isinstance(val, str):
                val = '\'' + val + '\''
            else:
                val = str(val)
            insertvalues = insertvalues + val + ', '

        print(insertvalues[:-2] + ')')
        sql2 = '''insert into ''' + newTableName + ''' (launch_type_id , label , 
              description , source) VALUES {};'''.format(insertvalues[:-2] + ')')
        print('the query: ', sql2)
        cursor.execute(sql2)

    newDb.commit()
    return 1


def load_launch_type():
    # table: launch_type.  Simple copy from olddb to newdb, field order is the same,
    #  but new launch_type table has a source field, so have to append this in dictionary
    #  with a default value 'missing'.
    tableName = 'launch_type'
    newTableName = 'launch_type'
    thepk = getPrimaryKey(oldDb, tableName)
    print('table: ', tableName, ' primaryKey: ', thepk)

    theDict = getTableData(oldDb, tableName, thepk)
    for row in theDict[tableName]:
        row['source'] = 'missing'

    # print(list(theDict[tableName][1].values()))
    # newDb.autocommit = True
    cursor = newDb.cursor()
    for anobj in theDict[tableName]:
        thevalues = list(anobj.values())
        insertvalues = '('
        for val in thevalues:
            if isinstance(val, str):
                val = '\'' + val + '\''
            else:
                val = str(val)
            insertvalues = insertvalues + val + ', '

        print(insertvalues[:-2] + ')')
        sql2 = '''insert into ''' + newTableName + ''' (launch_type_id , label , 
              description , source) VALUES {};'''.format(insertvalues[:-2] + ')')
        print('the query: ', sql2)
        cursor.execute(sql2)

    newDb.commit()
    return 1


def load_individual():  # was Agent
    # table: Agent. .
    tableName = 'sesar_user'
    newTableName = 'agent'
    thepk = getPrimaryKey(oldDb, tableName)
    print('table: ', tableName, ' primaryKey: ', thepk)

    theTempDict = getTableData(oldDb, tableName, thepk)
    theDict = {}
    rows = []
    for row in theTempDict[tableName]:
        newRow = {}
        newRow['agent_id'] = row['sesar_user_id']
        newRow['label'] = row['']
        newRow['fname'] = row['fname']
        newRow['lname'] = row['']
        newRow['agent_uri'] = row['orcid']
        newRow['address'] = row['address1'] + ', ' + row['address2'] + ', ' + row['city'] + ', ' + \
                            row['state_province'] + ', ' + row['postal_code']
        newRow['agent_type'] = 'individual'
        poc = ''
        # if not is None row['email']:
        #     poc = 'email: ' + row['email']
        # if not is None row['phone']:
        #     if len(poc)==0 :
        #         poc = 'phone: ' + row['phone']
        #     else:
        #         poc = poc + '; phone: ' + row['phone']
        newRow['point_of_contact'] = poc
        newRow['organization_affiliation_id'] = row['']
        newRow['parent_organization_id'] = row['']
        # print('newRow: ', newRow)
        rows.append(newRow)

    theDict[tableName] = rows
    # print(theDict)
    return 1


# load the geologic_time_scale table

def load_geologic_time_scale():
    newTableName = "geologic_time_scale"
    # get from excel workbook
    df = pandas.read_excel('../../MigrationNotes_LookupTables/GeologicTimeScale2020.xlsx')
    print(df.columns)
    theDict = {}
    rows = []
    for index, row in df.iterrows():
        print(row[0], row[1])
        newRow = {}
        newRow['label'] = row['label']
        tevent=""
        spoint=""
        scomment=""
        if not(pandas.isna(row.event) ):
            tevent = "Event: " + str(row['event'])
        if not(pandas.isna(row.bLevel)):
            spoint = "Stratigraphic point: " + str(row['bLevel'])
        if not(pandas.isna(row.stratotypeComment)):
            scomment = "Stratotype commment: " + str(row['stratotypeComment'])
        thetext = tevent + '; ' + spoint + '; ' + scomment
        thetext=thetext.replace("'","''")
        thetext=thetext.replace('"', '""')
        newRow['description'] = thetext
        newRow['geologic_time_interval_uri'] = row['URI']
        if pandas.isna(row.source) :
            rsource = 'missing'
        else:
            rsource = row['source']
        newRow['source'] = rsource
        newRow['scheme_uri'] = 'http://resource.geosciml.org/vocabulary/timescale/gts2020'
        newRow['numeric_older_bound'] = row['beginMa']
        newRow['numeric_younger_bound'] = row['endMa']
        newRow['notation'] = row['notation']
        print(newRow)
        rows.append(newRow)

    # print(list(theDict[tableName][1].values()))
    # newDb.autocommit = True
    cursor = newDb.cursor()
    for anobj in rows:
        thevalues = list(anobj.values())
        insertvalues = '('
        for val in thevalues:
            if isinstance(val, str):
                val = '\'' + val + '\''
            else:
                val = str(val)
            insertvalues = insertvalues + val + ', '

        print(insertvalues[:-2] + ')')
        sql2 = '''insert into ''' + newTableName + ''' (label , 
              description, geologic_time_interval_uri, source, scheme_uri, numeric_older_bound,numeric_younger_bound,notation) VALUES {};'''.format(insertvalues[:-2] + ')')
        print('the query: ', sql2)
        cursor.execute(sql2)

    newDb.commit()

    return df


def load_sample():
    # table: Sample.
    tableName = 'sample'
    newTableName = 'sample'

    thepk = getPrimaryKey(oldDb, tableName)
    print('table: ', tableName, ' primaryKey: ', thepk)

    theTempDict = getTableData(oldDb, tableName, thepk)
    theDict = {}
    rows = []
    for row in theTempDict[tableName]:
        # start by populating fields that copy directly
        newRow = {}

        newRow['age_qualifier'] = row['']
        newRow['archive_date'] = row['archive_date']
        newRow['collection_date_precision'] = row['collection_date_precision']
        newRow['collection_end_date'] = row['collection_end_date']
        newRow['collection_method_detail'] = row['collection_method_descr']
        newRow['collection_method_id'] = row['']
        newRow['collection_start_date'] = row['collection_start_date']
        newRow['cruise_field_prgrm_id'] = row['']
        newRow['cur_owner_id'] = row['cur_owner_id']  #fk to sesar user
        newRow['cur_registrant_id'] = row['cur_registrant_id']  #fk to sesar user
        newRow['geologic_age_verbatim'] = row['geological_age']
        newRow['geologic_unit'] = row['geological_unit']
        newRow['igsn'] = row['igsn']
        newRow['igsn_prefix'] = row['igsn_prefix']
        newRow['is_private'] = row['']
        newRow['last_changed_by_id'] = row['']
        newRow['last_update_date'] = row['']
        newRow['latitude'] = row['']
        newRow['latitude_end'] = row['']
        newRow['launch_label'] = row['sample_id']
        newRow['locality_detail'] = row['']
        newRow['location.qualifier'] = row['']
        newRow['longitude'] = row['']
        newRow['longitude_end'] = row['']
        newRow['material_name_verbatim'] = row['']
        newRow['metadata_store_status'] = row['']
        newRow['name'] = row['']
        newRow['name_is_system_assigned'] = row['']
        newRow['numeric_age_max'] = row['']
        newRow['numeric_age_min'] = row['']
        newRow['numeric_age_unit'] = row['']
        newRow['publish_date'] = row['']
        newRow['registration_date'] = row['']
        newRow['sample_description'] = row['']
        newRow['sample_id'] = row['sample_id']
        newRow['size'] = row['']
        newRow['vertical_max'] = row['']
        newRow['vertical_min'] = row['']

    return 1  # load sample


# ******************************************************************

# database connection is global variable.
oldDb = get_legacyConnection()
if oldDb:
    print("Connection to the Legacy PostgreSQL database established successfully.")
else:
    print("Connection to the Legacy PostgreSQL database encountered and error.")

# database connection is global variable.
newDb = get_2024Connection()
if newDb:
    print("Connection to SESAR2024 PostgreSQL database established successfully.")
else:
    print("Connection to SESAR2024 PostgreSQL encountered and error.")

# set up to process a table

# list of tables in database SELECT * FROM information_schema.tables WHERE table_schema = 'public' and table_type = 'BASE TABLE'
#  get field names for table
tablesquery = "SELECT table_name " + \
              "FROM information_schema.tables " + \
              "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
print(tablesquery)
tables = executeQuery(newDb, tablesquery)

tablelist = []
for row in tables:
    tablelist.append(row[0])
print(tablelist)

# uncomment functions for tables to test

result = load_sample()

oldDb.close()
newDb.close()
