import requests
import os
import common_utils.translator as tr  # Correct import
from common_utils.local_logger import logger
from common_utils.db_utils import connect_db, disconnect_db, get_record, insert_record
import json
from decimal import Decimal
from datetime import datetime

# HereMaps API Key from environment variable
API_KEY = os.getenv('HEREMAPS_ATTRACTIONS_KEY')
if not API_KEY:
    logger.error("Error: API Key not found! Set the 'HEREMAPS_ATTRACTIONS_KEY' environment variable.")
    raise ValueError("API Key not found!")

CATEGORY_MAPPING = {
    "Amusement Park": "Children",
    "Zoo": "Children",
    "Aquarium": "Children",
    "Museum": "Family",
    "Historical Landmark": "Family",
    "Historical Monument": "Family",
    "Theme Park": "Family",
    "Water Park": "Family",
    "Tourist Attraction": "Family",
    "Nightlife": "Adults",
    "Casino": "Adults",
    "Bar": "Adults",
    "Club": "Adults"
}

def normalize_attraction(attraction):
    """
    Ensures all attractions follow the same JSON structure.
    - Converts Decimal to float
    - Converts datetime to string
    - Removes extra DB-specific fields
    """
    return {
        "route_id": str(attraction.get("route_id")),
        "attraction_name": attraction.get("attraction_name"),
        "latitude": float(attraction["latitude"]) if isinstance(attraction["latitude"], Decimal) else attraction["latitude"],
        "longitude": float(attraction["longitude"]) if isinstance(attraction["longitude"], Decimal) else attraction["longitude"],
        "wp_latitude": float(attraction["wp_latitude"]) if isinstance(attraction["wp_latitude"], Decimal) else attraction["wp_latitude"],
        "wp_longitude": float(attraction["wp_longitude"]) if isinstance(attraction["wp_longitude"], Decimal) else attraction["wp_longitude"],
        "address": attraction.get("address", "N/A"),
        "category": attraction.get("category", "N/A"),
        "audience_type": attraction.get("audience_type", "General"),
        "popularity": attraction.get("popularity"),
        "opening_hours": attraction.get("opening_hours", "N/A"),
    }

import requests
import logging

logger = logging.getLogger(__name__)

import requests
import logging

logger = logging.getLogger(__name__)

def fetch_attractions(waypoints, route_id, max_results=20):
    """
    Fetches up to `max_results` unique attractions, ensuring they are evenly distributed across waypoints.
    - First, searches for attractions in `attractions_res` by latitude & longitude.
    - If not found in DB, fetches from API and inserts into `attractions_res`.
    - Ensures duplicates are skipped and fetches more attractions if needed.
    """
    route_id = str(route_id)  # Ensure route_id is a string
    attractions = []
    total_waypoints = len(waypoints)

    if total_waypoints == 0:
        logger.error("No waypoints available in the route.")
        return []

    unique_attractions = set()  # ✅ Track unique attractions (lat, lng)

    connect_db()  # Establish DB connection

    attraction_per_waypoint = max(1, max_results // total_waypoints)  # Spread results across waypoints
    remaining_needed = max_results  # Track remaining unique attractions needed

    waypoint_index = 0
    while remaining_needed > 0 and waypoint_index < total_waypoints:
        wp_lat, wp_lng = waypoints[waypoint_index]["lat"], waypoints[waypoint_index]["lng"]
        retry_count = 0  # ✅ Prevent infinite loop

        while remaining_needed > 0 and retry_count < 3:  # ✅ Retry fetching only 3 times per waypoint
            new_attractions = []

            # ✅ Step 1: Fetch from DB using `wp_lat, wp_lng`
            existing_attractions = get_record(
                "attractions_res", {"wp_latitude": wp_lat, "wp_longitude": wp_lng}
            )

            for attraction in existing_attractions:
                lat_lng = (attraction["latitude"], attraction["longitude"])
                if lat_lng in unique_attractions:
                    continue  # Skip duplicate

                unique_attractions.add(lat_lng)
                attractions.append(normalize_attraction(attraction))
                remaining_needed -= 1

                if remaining_needed == 0:
                    break  # Stop if max_results is reached

            if remaining_needed == 0:
                break  # Stop processing if we have enough unique attractions

            # ✅ Step 2: Fetch from API if needed
            places_url = "https://discover.search.hereapi.com/v1/discover"
            params = {
                "q": "tourist attraction",
                "at": f"{wp_lat},{wp_lng}",
                "limit": attraction_per_waypoint + retry_count,  # ✅ Increase limit on retries
                "sort": "popularity",
                "apiKey": API_KEY
            }

            try:
                response = requests.get(places_url, params=params, timeout=10)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error(f"ERROR: Request failed: {e}")
                break  # Exit retry loop if request fails
            
            if response.status_code == 200:
                places_data = response.json()
                if "items" in places_data:
                    for place in places_data["items"]:
                        position = place.get("position", {})
                        latitude = position.get("lat", None)
                        longitude = position.get("lng", None)
                        lat_lng = (latitude, longitude)

                        if lat_lng in unique_attractions:
                            logger.info(f"Skipping duplicate attraction at {lat_lng}")
                            continue  # ✅ Skip duplicate

                        # ✅ **Check if attraction already exists in DB**
                        existing_duplicate = get_record(
                            "attractions_res", {"latitude": latitude, "longitude": longitude}
                        )
                        if existing_duplicate:
                            logger.info(f"Skipping duplicate attraction at {lat_lng} (already in DB)")
                            continue  # ✅ Skip duplicate

                        # ✅ **Prepare new attraction**
                        category = place.get("categories", [{}])[0].get("name", "N/A")
                        audience_type = CATEGORY_MAPPING.get(category, "General")

                        opening_hours_list = place.get("openingHours", [])
                        opening_hours = (
                            ', '.join(opening_hours_list[0]["text"])
                            if opening_hours_list
                            else "N/A"
                        )

                        popularity_value = place.get("popularity")
                        popularity_value = None if popularity_value in [None, "N/A"] else popularity_value

                        attraction_name = safe_translate(place["title"])

                        # ✅ Insert new attraction into DB
                        new_attraction = {
                            "route_id": route_id,
                            "attraction_name": attraction_name,
                            "latitude": latitude,
                            "longitude": longitude,
                            "wp_latitude": wp_lat,
                            "wp_longitude": wp_lng,
                            "address": safe_translate(place.get("address", {}).get("label", "N/A")),
                            "category": safe_translate(category),
                            "audience_type": safe_translate(audience_type),
                            "popularity": popularity_value,
                            "opening_hours": opening_hours,
                        }

                        insert_record("attractions_res", new_attraction)  # Store in DB
                        unique_attractions.add(lat_lng)  # ✅ Track as unique
                        attractions.append(new_attraction)
                        remaining_needed -= 1

                        if remaining_needed == 0:
                            break  # Stop when we have enough attractions

            retry_count += 1  # ✅ Prevent infinite retry loop

        # ✅ Move to the next waypoint
        waypoint_index += 1

        # Restart from the beginning if not enough attractions are found
        if waypoint_index >= total_waypoints and remaining_needed > 0:
            waypoint_index = 0

    disconnect_db()  # ✅ Close DB connection
    return attractions  # ✅ Return only unique attractions


def safe_translate(text):
    """ Wrapper function for translation with error handling. """
    return tr.translate_text(text) if text else text

def check_attraction_exists(lat, lng):
    """
    Checks if an attraction with the given latitude and longitude exists in the PostgreSQL DB.
    Returns the attraction record if found, otherwise returns None.
    """
    filters = {"latitude": lat, "longitude": lng}
    result = get_record("attractions_res", filters)
    return result[0] if result else None

def fetch_attractions_from_route(route_data, max_results=20):
    """
    Fetches attractions along a predefined route given as JSON input
    and returns the data as JSON.
    """
    try:
        waypoints = route_data["waypoints"]
        route_id = str(route_data["route_id"])  # Ensure route_id is string
    except KeyError as e:
        logger.error(f"Invalid input: Missing key {e}")
        return None

    if not waypoints:
        logger.error("Error: No valid waypoints found in JSON.")
        return None

    # Fetch attractions near waypoints with route_id
    attractions = fetch_attractions(waypoints, route_id, max_results)

    # Create the JSON data
    # json_data = json.dumps(attractions, indent=4, ensure_ascii=False)
    # logger.info(f"JSON data generated successfully with {len(attractions)} attractions!")

    # return json_data
    return attractions


if __name__ == "__main__":
    route_json = {
        "user_id": 6550133750,
        "createdAt": "08/02/2025 23:11:13",
        "origin": "תל אביב",
        "destination": "אשדוד",
        "departure": "02/05 11:00",
        "gas-stations": 1,
        "restaurants": 1,
        "attractions": 0,
        "route_id": 655013375547,
        "summary": "Ayalon Hwy/Route 20 and Route 4",
        "total-distance": 44792,
        "waypoints": [
            {"lat": 32.0852876, "lng": 34.7817653},
            {"lat": 32.0574901, "lng": 34.7853104},
            {"lat": 31.9471941, "lng": 34.750032},
            {"lat": 31.7816482, "lng": 34.6701594},
            {"lat": 31.8062343, "lng": 34.657037}
        ]
    }
    
    json_output = fetch_attractions_from_route(route_json, max_results=5)
    #print(json_output)

'''
def check_and_insert_route(route_id):
    """
    Ensures that a route with the given route_id exists in the routes_req table.
    If it doesn't exist, inserts it.
    """
    route_id = str(route_id)  # Convert to string before querying

    filters = {"route_id": route_id}
    existing_route = get_record("routes_req", filters)

    if not existing_route:
        # Insert a new route entry with minimal required data
        route_data = {"route_id": route_id}  # Convert to string explicitly
        insert_record("routes_req", route_data)
        logger.info(f"Inserted new route_id {route_id} into routes_req.")
    else:
        logger.info(f"route_id {route_id} already exists in routes_req.")
'''
