
import json
from datetime import datetime

from common_utils.local_logger import logger
from common_utils.utils import UserRequestFieldNames, BreakPointName
import common_utils.db_utils as db
from common_utils.telegram_bot import send_message
import common_utils.kafka_common as kfk
from common_utils.kafka_producer import send_request_to_queue

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

if __name__ == "__main__":
   # Load the JSON file
    with open("route_gas_station_haifa_tel_aviv.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Parse JSON
        process_message(data)