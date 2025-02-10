
import requests
from bs4 import BeautifulSoup
import json
import random
import os
import sys
from common_utils.utils import UserRequestFieldNames
from common_utils.local_logger import logger

# Google API Key
API_KEY = os.getenv('GOOGLE_PLACES_KEY')
save_routes = False


def get_route_raw(origin, destination):
    # Step 1: Get Route from Tel Aviv to Haifa
    # Get the route from Tel Aviv to Haifa
    route_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&language=en&key={API_KEY}"
    route_response = requests.get(route_url).json()
    if route_response['status'] != "OK":
        logger.error(route_response['status'])
        return None, None
    
    logger.info(f"calling route url {route_url}")
   # Generate a random 6-digit route ID
    route_id = random.randint(100, 999)
 
    if save_routes:
        #print(json.dumps(route_response, indent=4, ensure_ascii=False))
         # Save route response to file
        route_filename = f"./data/route-{route_id}.json"
        with open(route_filename, "w", encoding="utf-8") as file:
            json.dump(route_response, file, indent=4, ensure_ascii=False)
        
    # # Convert JSON to a pretty-printed string
    # pretty_json = json.dumps(route_response, indent=4, ensure_ascii=False)
    # # Format with BeautifulSoup
    # soup = BeautifulSoup(pretty_json, "html.parser")
    # # Print prettified output
    # print(soup.prettify())
       
    return route_id, route_response

###########################################################################################
def get_filtered_route(my_route, result:dict, max_wayouts = 4):
    # filter raw data into limited amount of waypoints + main road to use
    # Extract total trip distance
    try:
        total_distance = my_route["routes"][0]["legs"][0]["distance"]["value"]  # meters
        max_wayouts = max(max_wayouts, 1)
        interval = total_distance / max_wayouts

        # Extract waypoints at 10% distance intervals
        waypoints = []
        cumulative_distance = 0

        major_road = my_route["routes"][0]["summary"]
        
        logger.info(f"searching waypoints; total distance = {total_distance}m major-road={major_road}")
        
        for leg in my_route["routes"]:
            for step in leg["legs"][0]["steps"]:
                cumulative_distance += step["distance"]["value"]
                if cumulative_distance >= interval * len(waypoints):  # Every 10%
                    lat = step["start_location"]["lat"]
                    lng = step["start_location"]["lng"]
                    tmp_leg = dict()
                    tmp_leg[UserRequestFieldNames.LATITUDE.value] = lat
                    tmp_leg[UserRequestFieldNames.LONGITUDE.value] = lng
                    waypoints.append(tmp_leg)
                    #waypoints.append(f"{lat},{lng}")
        
        result[UserRequestFieldNames.MAIN_ROUTE.value] = major_road
        result[UserRequestFieldNames.TOTAL_DISTANCE.value] = total_distance
        result[UserRequestFieldNames.WAYPOINTS.value] = waypoints
        
        if not len(waypoints):
            logger.warning("No waypoints found on route")
            return False
    except:
        logger.error("no route in get_filtered_route")
        return False
    
    return True

    
###################################################################################

if __name__ == "__main__":
    id, my_route = get_route_raw("tel-aviv", "haifa")
    if my_route:
        result = dict()
        get_filtered_route(my_route, result)

