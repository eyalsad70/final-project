import psycopg2
import psycopg2.extras
import os
from decimal import Decimal
from common_utils.virtual_route_planner_logger import logger

"""
get_record(table_name, filters, disconnect_db=True) → Fetches records matching the filters.
insert_record(table_name, data, disconnect_db=True) → Inserts a new record and returns it.
update_record(table_name, data, filters, disconnect_db=True) → Updates records and returns the updated row.
delete_record(table_name, filters, disconnect_db=True) → Deletes records and returns the deleted row.
"""

def setup_database_connection():
    """
    Establishes a connection to the PostgreSQL database and returns the connection and cursors.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('RDS_DB_NAME'),
            user=os.getenv('RDS_DB_USER'),
            password=os.getenv('RDS_DB_PASSWORD'),
            host=os.getenv('RDS_DB_HOST'),
            port=os.getenv('RDS_DB_PORT')
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        logger.info("Database connection established successfully.")
        return conn, cur
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        exit(1)


def get_record(table_name, filters, disconnect_db=True):
    conn, cur = setup_database_connection()
    where_clause = " AND ".join([f"{k} = %s" for k in filters.keys()])
    query = f"SELECT * FROM {table_name} WHERE {where_clause}" if filters else f"SELECT * FROM {table_name}"
    try:
        cur.execute(query, tuple(filters.values()))
        records = cur.fetchall()
        logger.info(f"Retrieved records from {table_name}: {records}")
        if disconnect_db:
            cur.close()
            conn.close()
        return records if disconnect_db else (conn, cur, records)
    except psycopg2.Error as e:
        logger.error(f"Error fetching records: {e}")
        return None if disconnect_db else (conn, cur, None)


def insert_record(table_name, data, disconnect_db=True):
    conn, cur = setup_database_connection()
    columns = ', '.join(data.keys())
    values_placeholder = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({values_placeholder}) RETURNING *"
    try:
        cur.execute(query, tuple(data.values()))
        conn.commit()
        inserted_record = cur.fetchone()
        logger.info(f"Inserted record into {table_name}: {inserted_record}")
        if disconnect_db:
            cur.close()
            conn.close()
        return inserted_record if disconnect_db else (conn, cur, inserted_record)
    except psycopg2.Error as e:
        logger.error(f"Error inserting record: {e}")
        conn.rollback()
        return None if disconnect_db else (conn, cur, None)


def update_record(table_name, data, filters, disconnect_db=True):
    conn, cur = setup_database_connection()
    set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
    where_clause = " AND ".join([f"{k} = %s" for k in filters.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause} RETURNING *"
    try:
        cur.execute(query, tuple(data.values()) + tuple(filters.values()))
        conn.commit()
        updated_record = cur.fetchone()
        logger.info(f"Updated record in {table_name}: {updated_record}")
        if disconnect_db:
            cur.close()
            conn.close()
        return updated_record if disconnect_db else (conn, cur, updated_record)
    except psycopg2.Error as e:
        logger.error(f"Error updating record: {e}")
        conn.rollback()
        return None if disconnect_db else (conn, cur, None)


def delete_record(table_name, filters, disconnect_db=True):
    conn, cur = setup_database_connection()
    where_clause = " AND ".join([f"{k} = %s" for k in filters.keys()])
    query = f"DELETE FROM {table_name} WHERE {where_clause} RETURNING *"
    try:
        cur.execute(query, tuple(filters.values()))
        conn.commit()
        deleted_record = cur.fetchone()
        logger.info(f"Deleted record from {table_name}: {deleted_record}")
        if disconnect_db:
            cur.close()
            conn.close()
        return deleted_record if disconnect_db else (conn, cur, deleted_record)
    except psycopg2.Error as e:
        logger.error(f"Error deleting record: {e}")
        conn.rollback()
        return None if disconnect_db else (conn, cur, None)


# Convert to a list of dictionaries with proper types
def convert_values(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)  # Convert to int if whole number, else float
    return obj

# convert DB record to dict() format
def convert_record(record):
    converted_data = [ {k: convert_values(v) for k, v in item.items()} for item in record ]
    return converted_data


# Example Usage
if __name__ == "__main__":
    conn, cur = setup_database_connection()
    inserted_record = insert_record("users", {"username": "John Doe", "email": "john.doe@example.com", "chat_id": 112233})
    logger.info(f"Inserted: {inserted_record}")

    conn, cur, inserted_record = insert_record("users", {"username": "Jane Doe", "email": "jane.doe@example.com", "chat_id": 112234}, disconnect_db=False)
    logger.info(f"Inserted (without disconnecting): {inserted_record}")

    users = get_record("users", {"username": "John Doe"})
    logger.info(f"Users: {users}")

    conn, cur, users = get_record("users", {"username": "Jane Doe"}, disconnect_db=False)
    logger.info(f"Users (without disconnecting): {users}")

    updated_record = update_record("users", {"email": "new.email@example.com"}, {"username": "John Doe"})
    logger.info(f"Updated: {updated_record}")

    deleted_record = delete_record("users", {"username": "John Doe"})
    logger.info(f"Deleted: {deleted_record}")

    cur.close()
    conn.close()