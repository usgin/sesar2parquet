"""
This code generates isamples JSON representations of SESAR sample desxcription records
SMR 2025-12-19
THe main transformation is done via a complex SQL query isampleJSON-WHERE.sql, which
has a marker string at the end of the file '/*WHERE_CLAUSE_PLACEHOLDER*/'; the query in the file
has the SQL SELECT, FROM, and GROUPBY clauses, but no where clause,
the intention is that the where clause can be added in code that uses the query
to filter based on update date or other criteria.

This code is designed to stand alone

output is written to a table in the sesar database,
db connections are established using environmental variables
    DB_2024_NAME -- database name
    DB_2024_USER -- db user name
    DB_2024_PASSWORD -- password for user
    DB_2024_HOST
    DB_2024_PORT

Separate read and write connections are used to enable bulk inserts for better
performance.
"""

import logging
import sys
import time
from datetime import  timezone
import os
import json
import psycopg2
from typing import Dict, List, Optional, Union, Tuple
from psycopg2.extensions import connection
from psycopg2.extras import execute_values
from datetime import datetime
from pathlib import Path

PK_LKUP: Dict[str, str] = {}

def get_read_connection() -> Optional[connection]:
    """Establish connection to SESAR database"""
    try:
        read_conn =  psycopg2.connect(
            database=os.environ.get('DB_2024_NAME'),
            user=os.environ.get('DB_2024_USER'),
            password=os.environ.get('DB_2024_PASSWORD'),
            host=os.environ.get('DB_2024_HOST'),
            port=os.environ.get('DB_2024_PORT'),
        )
        read_conn.autocommit = False # Keep transaction open
        return read_conn
    except Exception as e:
        LOGGER.exception(f'SESAR db read connection problem: {e}')
        return None

def get_write_connection() -> Optional[connection]:
    """Establish connection to SESAR database"""
    try:
        return psycopg2.connect(
            database=os.environ.get('DB_2024_NAME'),
            user=os.environ.get('DB_2024_USER'),
            password=os.environ.get('DB_2024_PASSWORD'),
            host=os.environ.get('DB_2024_HOST'),
            port=os.environ.get('DB_2024_PORT'),
        )
    except Exception as e:
        LOGGER.exception(f'SESAR db write connection problem: {e}')
        return None

def configure_logger(
        name='gen_isamples',
        level=logging.INFO,
        log_file="isamplesjson.log"
) -> logging.Logger:
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    handlers = [
        logging.FileHandler(log_file, mode="w"),  # Optional file logging
        logging.StreamHandler(sys.stdout)  # Explicitly log to stdout for ECS
    ]

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

# Initialize the default logger
LOGGER = configure_logger()

def get_primary_key(conn: connection, table_name: str) -> Optional[str]:
    """Get primary key column for a table"""
    query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
                     JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                              AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_name = %s \
            """
    try:
        result = execute_query(conn, query, (table_name,))
        return result[0][0] if result else None
    except Exception as e:
        LOGGER.exception(f'PRIMARY KEY query failed for table {table_name}: {e}')
        return None

# Query Execution
def execute_query(
    conn: connection,
    querystring: str,
    params: Optional[Union[Tuple, List]] = None
) -> Optional[List[Tuple]]:
    """Execute a parameterized query safely"""
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(querystring, params)
        else:
            cursor.execute(querystring)
        return cursor.fetchall()
    except Exception as e:
        LOGGER.exception(f'Query failed: {querystring[:100]}... Error: {e}')
        return None
    finally:
        cursor.close()

def pk_lkup(conn: connection) -> Dict[str, str]:
    """Build primary key lookup dictionary for all tables"""
    global PK_LKUP
    query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE' \
            """
    rows = execute_query(conn, query)
    if rows:
        tables = [row[0] for row in rows]
    else:
        tables = []

    PK_LKUP = {
        table: get_primary_key(conn, table)
        for table in tables
    }
    LOGGER.debug(f'PK_LKUP: {PK_LKUP}')
    return PK_LKUP

def insert_rows_batch(
        cursor,
        table_name: str,
        rows: List[Dict],
        field_list: List[str]
) -> int:
    """Bulk insert multiple rows"""
    if not rows:
        return 0

    placeholders = ', '.join(['%s'] * len(field_list))
    field_names = ', '.join(field_list)
    # use this query for cursor.executemany
    #query = f"INSERT INTO {table_name} ({field_names}) VALUES ({placeholders})"
    # use this query for execute_values
    query = f"INSERT INTO {table_name} ({field_names}) VALUES %s "

    'INSERT INTO isamples_json (igsn, data, date) VALUES %s '


    # if table_name == 'sample_additional_name':
    #     on_conflict_field = 'sample_id, name'
    # elif table_name == 'sesar_code':
    #     on_conflict_field = 'sesar_code'
    # elif table_name in PK_LKUP:
    #     on_conflict_field = PK_LKUP[table_name]

    on_conflict_field = 'igsn'

    if on_conflict_field:
        update_set = ', '.join([
            f"{field} = EXCLUDED.{field}"
            for field in field_list
            if field != PK_LKUP[table_name]
        ])
        query += f" ON CONFLICT ({on_conflict_field}) DO UPDATE SET {update_set}"

    # Prepare values in correct order
    values = [
        tuple(
            json.dumps(row.get(field)) if isinstance(row.get(field), (dict, list)) else row.get(field, None)
            for field in field_list
        )
        for row in rows
    ]

    try:
        # cursor.executemany(query, values)
        execute_values(cursor, query, values)
        values = []
        return len(rows)
    except Exception as e:
        LOGGER.exception(f'Batch insert failed for {table_name}')
        return 0

def create_isamples_json(read_conn, write_conn):
    sample_time = time.time()
    batch_size = 10000
    samples_processed = 0

    try:
        # Load query from file
        query_path = Path(__file__).parent / "isamplesJSON-WHERE.sql"
        base_query = query_path.read_text()

        # Prepare WHERE clause if needed
        where_clause = ""
        # if IS_UPDATE:
        #     update_window = datetime.now().date() - timedelta(days=UPDATE_WINDOW)
        #     where_clause = f"WHERE s.last_update_date >= '{update_window.strftime('%Y-%m-%d 00:00:00')}'"

        # Insert WHERE clause at the marked position
        query = base_query.replace(
            "/*WHERE_CLAUSE_PLACEHOLDER*/",
            where_clause
        )

        # new_cursor = new_db.cursor()
        #        with new_db.cursor() as new_cursor:
        with read_conn.cursor(name="sample_json_cursor") as fetch_cursor:
            fetch_cursor.itersize = batch_size
            fetch_cursor.execute(query)
            with write_conn.cursor() as insert_cursor:
                inserted_count = 0
                batch_num = 0
                while True:
                    sample_batch = fetch_cursor.fetchmany(batch_size)
                    if not sample_batch:
                        LOGGER.info(f"Completed sample processing. Total inserted: {inserted_count}")
                        break

                    batch_num += 1
                    batch_timestamp = datetime.now(timezone.utc)
                    new_rows = [
                        {
                            'igsn': sample[0]['sample_identifier'],
                            'data': sample[0],
                            'date': batch_timestamp
                        }
                        for sample in sample_batch
                    ]

                    # Use batch insert function
                    inserted_count = insert_rows_batch(
                        cursor=insert_cursor,
                        table_name='isamples_json',
                        rows=new_rows,
                        field_list=['igsn', 'data', 'date']
                        )
                    if inserted_count != len(new_rows):
                        raise Exception(f"Batch insert failed. Expected {len(new_rows)} inserts, got {inserted_count}")

                    samples_processed += inserted_count
                    LOGGER.info(f"Processed source record batch: {inserted_count} samples (Total: {samples_processed})")

                    write_conn.commit()
        return True

    except Exception as e:
        LOGGER.exception(f"Sample processing failed: {e}")
        write_conn.rollback()
        return False

    finally:
        LOGGER.info(f"Source record total duration: {(time.time() - sample_time ) /60:.1f} minutes")
        read_conn.close()
        write_conn.close()

def main():
    timestamp = datetime.now().isoformat('T', 'seconds')
    LOGGER.info(f'Started, time: {timestamp}')

    read_conn = get_read_connection()
    if read_conn:
        print("Read connection to SESAR database database established successfully.")
    else:
        print("Read connection to SESAR database encountered an error.")
        exit()
    pk_lkup(read_conn)

    write_conn = get_write_connection()
    if write_conn:
        print("Write connection to SESAR database established successfully.")
    else:
        print("Write connection to SESAR database encountered an error.")
        exit()

    create_isamples_json(read_conn, write_conn)
    
    print("Finished.")

if __name__ == "__main__":
    main()