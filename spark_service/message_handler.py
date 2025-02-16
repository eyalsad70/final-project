import json
import os
from pyspark.sql import SparkSession
from common_utils.db_utils import connect_db, disconnect_db, get_record, convert_record
from common_utils.local_logger import logger
import common_utils.kafka_common as kfk
from common_utils.kafka_producer import send_request_to_queue

def enrich_json_with_postgres(json_data):
    """
    Enriches JSON data by filling NULL values with data from PostgreSQL and returns the enriched JSON.

    :param json_path: Path to input JSON file.
    :return: Enriched JSON as a Python dictionary.
    """
        
    # ✅ Initialize Spark Session
    spark = SparkSession.builder.appName("GasStationEnrichment").getOrCreate()
    # ✅ Connect to the database
    connect_db()
   
    # ✅ Extract the `places` list from JSON
    places = json_data.get("places", [])
    enriched_places = []

    for place in places:
        latitude = place.get("latitude")
        longitude = place.get("longitude")
        # ✅ Query gas_stations table for the given latitude and longitude
        db_record = get_record("gas_stations", {"latitude": latitude, "longitude": longitude})
        if db_record:
            db_record = convert_record(db_record)[0]  # Convert DB record to dictionary
            # ✅ Fill missing (NULL) values in JSON with values from PostgreSQL
            place["working_hours"] = place.get("working_hours") or db_record.get("working_hours")
            place["petrol98"] = place.get("petrol98") or db_record.get("petrol98")
            place["electric_charge"] = place.get("electric_charge") or db_record.get("electric_charge")
            place["convenient_store"] = place.get("convenient_store") or db_record.get("convenient_store")
            place["car_wash"] = place.get("car_wash") or db_record.get("car_wash")
        enriched_places.append(place)

    # ✅ Update JSON with enriched places
    json_data["places"] = enriched_places
    # ✅ Disconnect from DB
    disconnect_db()
    # ✅ Stop Spark session
    spark.stop()
    # ✅ Return the enriched JSON as a Python dictionary
    return json_data

def spark_process_message(json_message):
    json_enriched = enrich_json_with_postgres(json_message)
    pretty_json = json.dumps(json_enriched, indent=4, ensure_ascii=False)
    topic_name = kfk.RESULTS_TOPIC_NAME
    return send_request_to_queue(pretty_json, topic_name)

def main():
    """
    Main function to run the enrichment process.
    """
    # ✅ Define input file path
    json_path = "./json_samples/route_gas_station_haifa_tel_aviv.json"
    # ✅ Check if input file exists
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        return
    logger.info("Starting JSON enrichment process...")    
    # ✅ Get enriched JSON instead of saving it to a file
     # ✅ Load JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        
    enriched_json = enrich_json_with_postgres(json_data)
    # ✅ Print or process enriched JSON
    print(json.dumps(enriched_json, indent=4, ensure_ascii=False))  # Pretty-print JSON
    logger.info("JSON enrichment completed successfully.")

if __name__ == "__main__":
    main()
