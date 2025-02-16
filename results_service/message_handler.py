import json
import os
from datetime import datetime

from common_utils.local_logger import logger
from common_utils.utils import UserRequestFieldNames, BreakPointName
import common_utils.db_utils as db
from common_utils.telegram_bot import send_message
from common_utils.sendgrid_mail import send_email


def send_route_details_on_email(json_message, text_to_send):
    email_addr = json_message.get(UserRequestFieldNames.USER_EMAIL.value, os.getenv('RECEIVER_EMAIL'))
    if email_addr:
        route = json_message[UserRequestFieldNames.ROUTE_ID.value]  
        place_type = json_message['place_type']
        send_email(email_addr, f"{place_type} list for {route}", text_to_send)

    
def send_route_summary(json_message, chat_id):
    origin = json_message[UserRequestFieldNames.ORIGIN.value].replace(" ", "-")
    destination = json_message[UserRequestFieldNames.DESTINATION.value].replace(" ", "-")
    main_route = json_message[UserRequestFieldNames.MAIN_ROUTE.value]
    distance = json_message[UserRequestFieldNames.TOTAL_DISTANCE.value] / 1000
    message_text = f"route summary: from {origin} to {destination} - go through {main_route}, total-distance = {distance}km "
    return send_message(chat_id, message_text)

def send_restaurant_list(json_message, chat_id):
    places = json_message['places']
    full_text = ""
    send_message(chat_id, "Restaurants List:\n")
    for idx, place in enumerate(places):    
        name = place.get('name', "")
        address = place.get('address', "N/A")
        opening_hours = place.get('working_hours', "N/A")
        google_url = place.get('url', "N/A")
        rating = place.get('rating', 0)
        price_level = place.get('price_level', 0)
        website = place.get('website', "N/A")
        
        text_message = f"{idx+1}: Name={name} ; Address={address} ; Opening-hours={opening_hours} ; Rating={rating} ; PriceLevel={price_level} \n \
            web-site {website} \n Google-Maps {google_url} \n"
        full_text += text_message
        if not send_message(chat_id,text_message):
            return False       
         
    send_route_details_on_email(json_message, full_text)
    return False


def send_gas_stations_list(json_message, chat_id):
    places = json_message['places']
    full_text = ""
    send_message(chat_id, "Gas stations List:\n")
    for idx, place in enumerate(places):    
        name = place.get('name', "")
        address = place.get('address', "N/A")
        opening_hours = place.get('working_hours', "N/A")
        google_url = place.get('url', "")
  
        services = {
            "disabled": place.get("wheelchair_accessible", False),
            "octanl98": place.get("petrol98", False),
            "electric": place.get("electric_charge", False),
            "store": place.get("convenient_store", False),
            "car_wash": place.get("car_wash", False)
        }                
        # Join all keys where the value is not None
        services_str = ",".join(key for key, value in services.items() if value is True)
        text_message = f"{idx+1}: Name={name} ; Address={address} ; Opening-hours={opening_hours} Services=({services_str}) \n  {google_url} "
        full_text += text_message
        if not send_message(chat_id,text_message):
            return False        
    
    send_route_details_on_email(json_message, full_text)
    return True


def send_attractions_list(json_message, chat_id):
    places = json_message['places']
    full_text = ""
    send_message(chat_id, "Attrations List:\n")
    
    for idx, place in enumerate(places):    
        attraction_name = place["attraction_name"]
        address = place["address"]
        category = place["category"]
        audience_type = place["audience_type"]
        opening_hours = place["opening_hours"]

        text_message = f"{idx+1}: Name={attraction_name} ; Address={address} ; Opening-hours={opening_hours} ; Category={category} ; Audience_type={audience_type}"
        full_text += text_message
        if not send_message(chat_id,text_message):
            return False        
        
        send_route_details_on_email(json_message, full_text)
        return True


def results_process_message(json_message):
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
    with open("./json_samples/route_gas_station_haifa_tel_aviv.json", "r", encoding="utf-8") as file:
#    with open("./json_samples/route_restaurant_haifa_tel_aviv.json", "r", encoding="utf-8") as file:
#    with open("./route_attraction_haifa_tel_aviv.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Parse JSON
        results_process_message(data)