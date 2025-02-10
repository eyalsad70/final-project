import psycopg2
import psycopg2.extras
import os
from decimal import Decimal
from common_utils.local_logger import logger

# Global connection and cursor variables
conn = None
cur = None

def connect_db():
    """
    Establishes a connection to the PostgreSQL database and sets the global connection and cursor.
    """
    global conn, cur
    if conn is None or cur is None:
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
        except psycopg2.Error as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            exit(1)

def disconnect_db():
    """
    Closes the global database connection and cursor.
    """
    global conn, cur
    if cur:
        cur.close()
        cur = None
    if conn:
        conn.close()
        conn = None
    logger.info("Database connection closed.")

def get_record(table_name, filters):
    """
    Fetches records from the given table that match the filters.
    Assumes that `conn` and `cur` are already valid.
    """
    where_clause = " AND ".join([f"{k} = %s" for k in filters.keys()])
    query = f"SELECT * FROM {table_name} WHERE {where_clause}" if filters else f"SELECT * FROM {table_name}"
    cur.execute(query, tuple(filters.values()))
    records = cur.fetchall()
    logger.info(f"Retrieved records from {table_name}: {records}")
    return records

def insert_record(table_name, data):
    """
    Inserts a new record into the given table and returns it.
    Assumes that `conn` and `cur` are already valid.
    """
    columns = ', '.join(data.keys())
    values_placeholder = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({values_placeholder}) RETURNING *"
    cur.execute(query, tuple(data.values()))
    conn.commit()
    inserted_record = cur.fetchone()
    logger.info(f"Inserted record into {table_name}: {inserted_record}")
    return inserted_record

def update_record(table_name, data, filters):
    """
    Updates records in the given table that match the filters and returns the updated row.
    Assumes that `conn` and `cur` are already valid.
    """
    set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
    where_clause = " AND ".join([f"{k} = %s" for k in filters.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause} RETURNING *"
    cur.execute(query, tuple(data.values()) + tuple(filters.values()))
    conn.commit()
    updated_record = cur.fetchone()
    logger.info(f"Updated record in {table_name}: {updated_record}")
    return updated_record

def delete_record(table_name, filters):
    """
    Deletes records from the given table that match the filters and returns the deleted row.
    Assumes that `conn` and `cur` are already valid.
    """
    where_clause = " AND ".join([f"{k} = %s" for k in filters.keys()])
    query = f"DELETE FROM {table_name} WHERE {where_clause} RETURNING *"
    cur.execute(query, tuple(filters.values()))
    conn.commit()
    deleted_record = cur.fetchone()
    logger.info(f"Deleted record from {table_name}: {deleted_record}")
    return deleted_record


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
    connect_db()  # Ensure connection is established

    if conn is not None and cur is not None:  # Check before calling
        inserted_record = insert_record("users", {"username": "Yaniv Raba", "email": "yaniv.raba@example.com", "chat_id": 112233})
        logger.info(f"Inserted: {inserted_record}")

        users = get_record("users", {"username": "Yaniv Raba"})
        logger.info(f"Users: {users}")

        updated_record = update_record("users", {"email": "new.yanivraba@example.com"}, {"username": "Yaniv Raba"})
        logger.info(f"Updated: {updated_record}")

        deleted_record = delete_record("users", {"username": "Yaniv Raba"})
        logger.info(f"Deleted: {deleted_record}")

    disconnect_db()  # Close connection at the end
