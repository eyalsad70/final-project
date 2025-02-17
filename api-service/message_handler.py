
import json
from datetime import datetime

from common_utils.local_logger import logger
from common_utils.utils import UserRequestFieldNames, BreakPointName
import google_places
from heremaps_attractions import fetch_attractions_from_route
import common_utils.kafka_common as kfk
from common_utils.kafka_producer import send_request_to_queue
import common_utils.db_utils as db

save_to_file = False

def create_json_result(original_message, place_type, places_data):
    """ takes user request message + places result and create json message """
    next_message = original_message
    #next_message[UserRequestFieldNames.CREATED_AT.value] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    next_message['place_type'] = place_type
    if places_data:       
        next_message['places'] = places_data
        #print(next_message)
    
     # Convert to pretty JSON
    pretty_json = json.dumps(next_message, indent=4, ensure_ascii=False)
    
    if save_to_file:
        origin = next_message[UserRequestFieldNames.ORIGIN.value].replace(" ", "_")
        destination = next_message[UserRequestFieldNames.DESTINATION.value].replace(" ", "_")
        file_name = f"route_{place_type}_{origin}_{destination}.json"
        with open(file_name, "w", encoding="utf-8") as json_file:
            json_file.write(pretty_json)       
    return pretty_json

def send_places_data_to_queue(original_message, place_type, places_data, topic_name):
    pretty_json = create_json_result(original_message, place_type, places_data)
    return send_request_to_queue(pretty_json, topic_name)


def api_process_message(json_message):
    """ check for route breakpoints requested by user and call proper method to fetch breakpoint details (places)
        if user choose direct route with no breakpoints it is also handled under 'send_places_data_to_queue'
    """
    if not json_message:
        logger.error("process_message was called with no message")
        return False
    
    places = dict()
    was_sent = False
    
    db.connect_db()
    
    # if user requested fueling breaks (note that google api gives limited data so we are enriching it using statics tables through an intermediate queue)
    if json_message[UserRequestFieldNames.FUEL_REQUIRED.value]:
        place_type = BreakPointName.FUELING.value
        places = google_places.get_places_in_route(json_message, place_type, False, 1)
        if places:
            topic_name = kfk.TRANSFORMER_TOPIC_NAME
            was_sent = send_places_data_to_queue(json_message, place_type, places, topic_name)
    
    # if user requested restaurant breaks
    if json_message[UserRequestFieldNames.FOOD_REQUIRED.value]:
        place_type = BreakPointName.RESTAURANT.value
        places = google_places.get_places_in_route(json_message, place_type, True, 1)
        if places:            
            topic_name = kfk.RESULTS_TOPIC_NAME
            was_sent = send_places_data_to_queue(json_message, place_type, places, topic_name)
    
    # if user requested for attraction breaks
    if json_message[UserRequestFieldNames.ATTRACTION_REQUIRED.value]:
        place_type = BreakPointName.ATTRACTION.value
        places = fetch_attractions_from_route(json_message, 4)
        if places:
            topic_name = kfk.RESULTS_TOPIC_NAME            
            was_sent = send_places_data_to_queue(json_message, place_type, places, topic_name)
    
    if not was_sent:
        topic_name = kfk.RESULTS_TOPIC_NAME            
        place_type = BreakPointName.NONE.value
        was_sent = send_places_data_to_queue(json_message, place_type, None, topic_name)

    db.disconnect_db()
    
    return was_sent
            
    """ TBDs :
    check in DB for places ; save it if not
    """

if __name__ == "__main__":
    # Load the JSON file
    with open("./json_samples/route_request_haifa_tel aviv.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Parse JSON
        api_process_message(data)