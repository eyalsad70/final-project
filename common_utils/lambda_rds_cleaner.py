import os
import psycopg2
from datetime import datetime, timedelta

# Environment variables (set these in AWS Lambda)
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")  # Default PostgreSQL port

def lambda_handler(event, context):
    db_tables = ["restaurants_res", "gas_stations_res"]
    text_body = []
    
    try:
        # Connect to PostgreSQL RDS
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cur = conn.cursor()

        # Calculate the date 5 days ago
        five_days_ago = datetime.now() - timedelta(days=5)

        for idx, table in enumerate(db_tables):
            # Execute DELETE query
            cur.execute(f"DELETE FROM {table} WHERE created_at < %s;", (five_days_ago,))
            # Commit changes
            conn.commit()
            # Get the number of rows affected
            deleted_rows = cur.rowcount

            # Log the number of deleted records
            text_body.append(f"Deleted {deleted_rows} old records from {table}. ")

        # Close connection
        cur.close()
        conn.close()

        return {
            "statusCode": 200,
            "body": "\n".join(text_body)
        }    
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }
        