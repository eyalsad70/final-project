
import json
from datetime import datetime
import os, sys

from common_utils.local_logger import logger
from common_utils.utils import UserRequestFieldNames, BreakPointName
import common_utils.db_utils as db
from common_utils.telegram_bot import send_message
import common_utils.kafka_common as kfk
from common_utils.kafka_producer import send_request_to_queue

java_home = os.getenv('JAVA_HOME')
#print(sys.path)

def send_places_data_to_queue(original_message, place_type, places_data):
    next_message = original_message
    #next_message[UserRequestFieldNames.CREATED_AT.value] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    next_message['place_type'] = place_type
    if places_data:       
        next_message['places'] = places_data
        print(next_message)
    
     # Convert to pretty JSON
    pretty_json = json.dumps(next_message, indent=4, ensure_ascii=False)
       
    return send_request_to_queue(pretty_json, kfk.RESULTS_TOPIC_NAME)


def process_message(json_message):
    if not json_message:
        logger.error("process_message was called with no message")
        return False

    # enrich data with CSVs
    # working_hours,Product98,Productgas,Producturea,Iselectric,Car_wash,Store

    # send result to results_topic
    place_type = BreakPointName.FUELING.value
    # implement enriched gas stations
    places = json_message['places']
    if places:
        topic_name = kfk.RESULTS_TOPIC_NAME            
        was_sent = send_places_data_to_queue(json_message, place_type, places, topic_name)


from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, coalesce


def enrich_gas_station_data(json_path: str, delek_csv_path: str, doralon_csv_path: str, paz_csv_path: str, output_path: str):
    """
    Enriches gas station data from a JSON file using three CSV files.

    Args:
        json_path (str): Path to the JSON file containing gas station data.
        delek_csv_path (str): Path to the Delek stations CSV file.
        doralon_csv_path (str): Path to the Doralon stations CSV file.
        paz_csv_path (str): Path to the Paz stations CSV file.
        output_path (str): Path to save the enriched JSON file.

    Returns:
        DataFrame: The enriched PySpark DataFrame.
    """

    # ✅ Initialize Spark session
    spark:SparkSession = SparkSession \
        .builder.master("local[*]") \
        .appName('GasStationDataEnrichment').getOrCreate()

    # ✅ Load JSON file
    json_df = spark.read.option("multiline", "true").json(json_path)

    # ✅ Explode 'places' array to extract gas station details
    json_df = json_df.withColumn("place", explode("places")).select(
        col("user_id"),
        col("place.place_id"),
        col("place.name"),
        col("place.address"),
        col("place.latitude"),
        col("place.longitude"),
        col("place.working_hours"),
        col("place.petrol98"),
        col("place.electric_charge"),
        col("place.convenient_store"),
        col("place.car_wash")
    ).alias("json")  # ✅ Assign alias to avoid ambiguity
    json_df.show()
    
    # ✅ Load CSV files (No need to rename columns)
    delek_df = spark.read.option("header", "true").csv(delek_csv_path).alias("delek")
    doralon_df = spark.read.option("header", "true").csv(doralon_csv_path).alias("doralon")
    paz_df = spark.read.option("header", "true").csv(paz_csv_path).alias("paz")
    paz_df. show()
    
    print("Delek Columns:", delek_df.columns)
    print("Doralon Columns:", doralon_df.columns)
    print("Paz Columns:", paz_df.columns)


    # ✅ Perform Left Joins with Explicit Column Names
    json_df = json_df.join(delek_df, col("json.name") == col("delek.name"), "left") \
        .select("json.*",
                coalesce(col("json.working_hours"), col("delek.working_hours")).alias("working_hours"),
                coalesce(col("json.petrol98"), col("delek.petrol98")).alias("petrol98"),
                coalesce(col("json.electric_charge"), col("delek.electric_charge")).alias("electric_charge"),
                coalesce(col("json.convenient_store"), col("delek.convenient_store")).alias("convenient_store"),
                coalesce(col("json.car_wash"), col("delek.car_wash")).alias("car_wash"))
    json_df.show()
    
    json_df = json_df.join(doralon_df, col("json.name") == col("doralon.name"), "left") \
        .select("json.*",
                col("json.working_hours"),  # ✅ Doralon has no working_hours, so we keep the existing value
                coalesce(col("json.petrol98"), col("doralon.petrol98")).alias("petrol98"),
                coalesce(col("json.electric_charge"), col("doralon.electric_charge")).alias("electric_charge"),
                coalesce(col("json.convenient_store"), col("doralon.convenient_store")).alias("convenient_store"),
                coalesce(col("json.car_wash"), col("doralon.car_wash")).alias("car_wash"))

    json_df = json_df.join(paz_df, col("json.name") == col("paz.name"), "left") \
        .select("json.*",
                coalesce(col("json.working_hours"), col("paz.working_hours")).alias("working_hours"),
                coalesce(col("json.petrol98"), col("paz.petrol98")).alias("petrol98"),
                coalesce(col("json.electric_charge"), col("paz.electric_charge")).alias("electric_charge"),
                coalesce(col("json.convenient_store"), col("paz.convenient_store")).alias("convenient_store"),
                coalesce(col("json.car_wash"), col("paz.car_wash")).alias("car_wash"))


    # ✅ Convert DataFrame to JSON
    pandas_df = json_df.toPandas()  # Convert Spark DataFrame to Pandas
    print(pandas_df)

    json_str = pandas_df.to_json(orient="records")  # Convert Pandas DataFrame to JSON string

    enriched_json = json.loads(json_str)  # Convert JSON string to Python dictionary

    return enriched_json


    # ✅ Save the enriched JSON file
    #json_df.write.mode("overwrite").json(output_path)


    # ✅ Print schema and sample data for verification
    #json_df.printSchema()
    #json_df.show(truncate=False)


if __name__ == "__main__":
    json_path = "./route_gas_station_haifa_tel_aviv.json"
    delek_csv_path = "./offline_utils/delek_stations_transformed.csv"
    doralon_csv_path = "./offline_utils/doralon_stations_transformed.csv"
    paz_csv_path = "./offline_utils/paz_stations_transformed.csv"
    output_path = "./spark/enriched_route_gas_station_haifa_tel_aviv.json"

    enriched_df = enrich_gas_station_data(json_path, delek_csv_path, doralon_csv_path, paz_csv_path, output_path)
    enriched_df.show(truncate=False)  # Display the enriched data

   # Load the JSON file
    with open("./route_gas_station_haifa_tel_aviv.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Parse JSON
        process_message(data)