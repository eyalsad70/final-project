
import requests
from bs4 import BeautifulSoup
import json
import random
import os
from common_utils.local_logger import logger
from common_utils.utils import UserRequestFieldNames, BreakPointName
import common_utils.translator as tr
import common_utils.db_utils as db

# Google API Key
API_KEY = os.getenv('GOOGLE_PLACES_KEY')
if not API_KEY:
    logger.error("Error: GOOGLE_PLACES_KEY not found")
    raise ValueError("GOOGLE_PLACES_KEY not found!")

SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'

save_routes = False

google_supported_place_types = ["restaurant", "cafe", "gas_station", "shopping_mall", "tourist_attraction", "park", "lodging"]
db_tables = { "restaurant":"restaurants_res", 
              "gas_station":"gas_stations_res"
            }

largest_gas_stations_israel = ["paz", "delek", "dor", "sonol"]
non_real_gas_stations = ["oak", "energy"]  # if gas station name includes this, its not a regular gas stations and may not support private cars

# look only for largest vendors and avoid stations that are 'non-real'
def is_gas_station_valid(station_name):
    valid = any(station in station_name.lower() for station in largest_gas_stations_israel)
    if valid:
        valid = not any(fake_station in station_name.lower() for fake_station in non_real_gas_stations)
    return valid

                    
    # first check if belong to one of the largest

##################################################################################
def get_places_near_coordinates(latitude, longitude, place_type):
    if place_type not in google_supported_place_types:
        logger.error(f"place type {place_type} is not supported")
        return None
    
    # Parameters for the Places API request
    params = {
        'key': API_KEY,
        'location': f'{latitude},{longitude}',
        'radius': 3000,  # Radius in meters
        'type': place_type  # 'restaurant' or 'lodging' (for hotels)
    }

    response = requests.get(SEARCH_URL, params=params)
    if response.status_code == 200:
        places = response.json()
        return places['results']
    return None

###################################################################################
def get_place_details(place_id):
    params = {
        'place_id': place_id,
        'key': API_KEY,
    }
    response = requests.get(DETAILS_URL, params=params)
    place_details = response.json().get('result', {})

    # print(place_details)
    return place_details

###################################################################################
def get_places_in_route(route_dict, place_type, fetch_details = False, max_places_per_location = 2):
    # Extract total trip distance

    # Extract waypoints at 10% distance intervals
    waypoints = route_dict[UserRequestFieldNames.WAYPOINTS.value]

    # Fetch gas stations and their details
    places = []
    place_ids = []
    total_id = 1

    for waypoint in waypoints:
        lat = waypoint[UserRequestFieldNames.LATITUDE.value]
        lng = waypoint[UserRequestFieldNames.LONGITUDE.value]
        # lat, lng = waypoint.split(",")
        places_response = get_places_near_coordinates(lat, lng, place_type)
        if places_response:
            logger.info(f"call google nearby places for route-id {route_dict[UserRequestFieldNames.ROUTE_ID.value]} - latitude:{lat} longitude:{lng}")
            #print(json.dumps(places_response, indent=4, ensure_ascii=False))
        else:
            logger.error(f"Failed to get google api places for route-id {UserRequestFieldNames.ROUTE_ID.value}")
            return None

        # Save gas stations response to file
        if save_routes:
            station_filename = f"./data/place-{place_type}-{total_id}.json"
            with open(station_filename, "w", encoding="utf-8") as file:
                json.dump(places_response, file, indent=4, ensure_ascii=False)

        # collect basic details from 'places_response', and if 'fetch_details' required add extra info
        collected_places = 0
        for idx, place in enumerate(places_response):
            if "closed" in place.get("business_status", "").lower():  # skip places which are temporarily closed
                continue
            place_id = place["place_id"]
            if place_id in place_ids:  # avoid duplications
                continue
            place_data = dict()
            db_record_found = False
            
            if place_type in db_tables:
                # note that 'get record' returns all matching records, but since 'place-id' is unique we'll get only 1 record
                place_record = db.get_record(db_tables[place_type], {'place_id' : place_id} )
                if place_record:
                    place_data = db.convert_record(place_record)[0]
                    removed_value = place_data.pop("created_at", None)  # Removes creation time which is in datetime format and not needed
                    db_record_found = True
                    place_ids.append(place_id)
            
            if not db_record_found:
                place_data['place_id'] = place_id
                name = place.get("name","NA")
                if name == 'Дор Алон':
                    name_eng = "dor alon"
                else:
                    name_eng = tr.translate_text(name).lower()
                place_data["name"] = name_eng if name_eng else name.lower()
                
                # skip non familiar gas stations
                if place_type == 'gas_station' and not is_gas_station_valid(place_data["name"]):
                    continue
                place_ids.append(place_id)
                place_data["latitude"] = place["geometry"]["location"].get("lat")
                place_data["longitude"] = place["geometry"]["location"].get("lng")
                place_data["rating"] = place.get("rating",1)
                place_data["vicinity"] = place.get("vicinity","israel").lower()
                place_data["url"] = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

                if fetch_details:        
                    place_details = get_place_details(place_id)
                    
                    # Save detailed gas station info
                    if save_routes:
                        station_filename = f"./data/place-{place_type}-{total_id}-{idx}.json"
                        total_id += 1
                        with open(station_filename, "w", encoding="utf-8") as file:
                            json.dump(place_details, file, indent=4, ensure_ascii=False)
                    
                    place_data["address"] = place_details.get("formatted_address", "Unknown")
                    place_data["working_hours"] = place_details.get("opening_hours", {}).get("weekday_text", "Not Available")
                #  place_data["types"] = place_details.get("types", [])
                    
                    if place_type == 'restaurant':
                        place_data["serves_alcohol"] = place_details.get("serves_beer", False)
                        place_data["wheelchair_accessible"] = place_details.get("wheelchair_accessible_entrance", False)
                        place_data["price_level"] = place_details.get("price_level", 1)
                        place_data["website"] = place_details.get("website","www.unknown")
                else:
                    place_data["address"] = place_data["vicinity"]
                    
                # add place to DB - tbd check first if exists
                if place_type in db_tables:
                    # rating_type = type(place_data["rating"])
                    # print(f"type: {rating_type}")
                    db.insert_record(db_tables[place_type], place_data)
                    
            places.append(place_data)
            collected_places += 1
            if collected_places >= max_places_per_location:
                break

    return places
    
            
        

###################################################################################
import message_handler

if __name__ == "__main__":
    # Read JSON file
    input_file_name = "./json_samples/route_request_jerusalem_dimona.json"
    #input_file_name = "./json_samples/route_request_haifa_tel aviv.json"
    with open(input_file_name, "r", encoding="utf-8") as file:
        data = json.load(file)  # Load JSON content into a dictionary    
        place_type = "gas_station"
        db.connect_db()    
        places = get_places_in_route(data, place_type)
        db.disconnect_db()
        #get_places_in_route(data, "restaurant", True)
        #get_places_in_route(data, "lodging")
        message_handler.create_json_result(data, place_type, places)
