
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from common_utils.local_logger import logger
from enum import Enum

# MongoDB connection details
MONGO_DB = "nayaProj"       # Change if needed

MONGO_HOST = os.getenv('MONGO_DB_HOST')
if not MONGO_HOST:
    raise ValueError("MONGO_HOST found!")
MONGO_PORT = os.getenv('MONGO_DB_PORT')

class CollectionType(Enum):
    MONGO_TEST_COLLECTION = "testing"
    MONGO_ROUTES_REQUESTS_COLLECTION = "route_requests"
    MONGO_ROUTES_DATA_COLLECTION = "routes_data"

client = None
my_db = None

def connect_db():
    """
    Establishes a connection to the mongoDB database and sets the global client and project DB.
    """
    global client, my_db 
    if client is None:
        # Connect to MongoDB (No authentication)
        # Set a timeout of 5 seconds
        client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/", serverSelectionTimeoutMS=5000)
    try:
        # Attempt to fetch the list of databases to test connection
        dbs = client.list_database_names()
        logger.info(f"Connected to MongoDB! Databases: {dbs}")
        my_db = client[MONGO_DB]
    except ServerSelectionTimeoutError as e:
        logger.error(f"Failed to connect to MongoDB: {e}")


def disconnect_db():
    global client, my_db
    if client:
        client.close()
        client = None
        my_db = None

        
def get_collection(type:CollectionType):
    return my_db[type.value]


def insert_data(type:CollectionType, data):
    if my_db is None:
        logger.error("insert_data: MongoDB is not connected")
        return False
    
    """Insert a document into MongoDB"""
    status = False
    try:
        collection = my_db[type.value]
        result = collection.insert_one(data)
        logger.info(f"Data inserted to Mongo with ID: {result.inserted_id}")
        status =True
    except Exception as e:
        logger.error(f"error {e} - failed to insert data to mongo")
    return status


def fetch_data(type:CollectionType, query={}):
    """Fetch documents from MongoDB"""
    if my_db is None:
        logger.error("fetch_data: MongoDB is not connected")
        return None
    try:
        collection = my_db[type.value]
        results = collection.find(query)
        return list(results)  # Convert cursor to list
    except:
        return None
    

def entry_exists(type:CollectionType, query):
    """Check if a route with given origin & destination exists."""
    if my_db is None:
        logger.error("entry_exists: MongoDB is not connected")
        return False
    try:
        collection = my_db[type.value]
        status = collection.find_one(query) is not None  # Returns True if found, else False
        return status
    except:
        return False


if __name__ == "__main__":
     # Save data
    sample_data = {"name": "Motty", "age": 50, "city": "Haifa"}
    connect_db()
    insert_data(CollectionType.MONGO_TEST_COLLECTION, sample_data)
    # Fetch data
    documents = fetch_data(CollectionType.MONGO_TEST_COLLECTION)
    for doc in documents:
        print(doc)
        
    # the following is an eample usage for route table containing origin & destination
    """Check if a route with given origin & destination exists."""
    query = {"origin": "Tel Aviv", 'destination': 'Ashdod'}
    status = entry_exists(CollectionType.MONGO_ROUTES_REQUESTS_COLLECTION,query) 
    disconnect_db()
    




