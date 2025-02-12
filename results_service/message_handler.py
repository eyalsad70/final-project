import json
from datetime import datetime

from common_utils.local_logger import logger
from common_utils.utils import UserRequestFieldNames, BreakPointName
import common_utils.db_utils as db
from common_utils.telegram_bot import send_message

def send_route_summary(json_message, chat_id):
    origin = json_message[UserRequestFieldNames.ORIGIN.value].replace(" ", "-")
    destination = json_message[UserRequestFieldNames.DESTINATION.value].replace(" ", "-")
    main_route = json_message[UserRequestFieldNames.MAIN_ROUTE.value]
    distance = json_message[UserRequestFieldNames.TOTAL_DISTANCE.value] / 1000
    message_text = f"route summary: from {origin} to {destination} - go through {main_route}, total-distance = {distance}km "
    return send_message(chat_id, message_text)

def send_restaurant_list(json_message, chat_id):
    places = json_message['places']
    send_message(chat_id, "Restaurants List:")
    for idx, place in enumerate(places):    
        name = place['name']    
        address = place['address']
        opening_hours = place['working_hours']
        rating = place['rating']
        price_level = place['price_level']
        website = place['website']
        google_url = place['url']
        
        text_message = f"{idx+1}: Name={name} ; Address={address} ; Opening-hours={opening_hours} ; Rating={rating} ; PriceLevel={price_level} \n \
            web-site {website} \n Google-Maps {google_url} "
        if not send_message(chat_id,text_message):
            return False        
    return False

def send_gas_stations_list(json_message, chat_id):
    places = json_message['places']
    send_message(chat_id, "Gas stations List:")
    for idx, place in enumerate(places):    
        name = place['name']    
        address = place['address']
        opening_hours = place['working_hours']
        google_url = place['url']
  
        services = {
            "disabled": place["wheelchair_accessible"],
            "octanl98": place["petrol98"],
            "electric": place["electric_charge"],
            "store": place["convenient_store"],
            "car_wash": place["car_wash"]
        }                
        # Join all keys where the value is not None
        services_str = ",".join(key for key, value in services.items() if value is True)
        text_message = f"{idx+1}: Name={name} ; Address={address} ; Opening-hours={opening_hours} Services=({services_str}) \n  {google_url} "
        if not send_message(chat_id,text_message):
            return False        
    return True

def send_attractions_list(json_message, chat_id):
    places = json_message['places']
    send_message(chat_id, "Attrations List:")
    
    for idx, place in enumerate(places):    
        attraction_name = place["attraction_name"]
        address = place["address"]
        category = place["category"]
        audience_type = place["audience_type"]
        opening_hours = place["opening_hours"]

        text_message = f"{idx+1}: Name={attraction_name} ; Address={address} ; Opening-hours={opening_hours} ; Category={category} ; Audience_type={audience_type}"
        if not send_message(chat_id,text_message):
            return False        
    return True


def process_message(json_message):
    if not json_message:
        logger.error("process_message was called with no message")
        return False

    chat_id = json_message['user_id']
    
    send_route_summary(json_message, chat_id)
    
    place_type = json_message['place_type']
    
    if(place_type == BreakPointName.FUELING.value):
        return send_gas_stations_list(json_message, chat_id)
    elif (place_type == BreakPointName.ATTRACTION.value):
        return send_attractions_list(json_message, chat_id)
    elif (place_type == BreakPointName.RESTAURANT.value):
        return send_restaurant_list(json_message, chat_id)
    elif (place_type == BreakPointName.NONE.value):
        return True
    
    logger.error(f"received message from results topic with unknown place type {place_type}")
    return False


if __name__ == "__main__":
    # Load the JSON file
#    with open("./route_gas_station_haifa_tel_aviv.json", "r", encoding="utf-8") as file:
#    with open("./route_restaurant_haifa_tel_aviv.json", "r", encoding="utf-8") as file:
    with open("./route_attraction_haifa_tel_aviv.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Parse JSON
        process_message(data)