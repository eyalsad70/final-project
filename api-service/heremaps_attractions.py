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

def fetch_attractions(waypoints, route_id, max_results=20):
    """
    Fetches up to `max_results` attractions, ensuring they are evenly distributed across waypoints.
    - First, searches for attractions in `attractions_res` by latitude & longitude.
    - If not found in DB, fetches from API and inserts into `attractions_res`.
    - Stores the waypoint (`wp_latitude, wp_longitude`) to avoid future API calls.
    """
    route_id = str(route_id)  # Ensure route_id is a string
    attractions = []
    total_waypoints = len(waypoints)

    if total_waypoints == 0:
        logger.error("No waypoints available in the route.")
        return []

    connect_db()  # Establish DB connection
    # ✅ Ensure route_id exists in routes_req before inserting into attractions_res
    ###########################check_and_insert_route(route_id)	

    attraction_per_waypoint = max(1, max_results // total_waypoints)  # Ensure spreading & even distribution
    remaining_needed = max_results  # Track remaining attractions needed

    waypoint_index = 0
    while remaining_needed > 0 and waypoint_index < total_waypoints:
        wp_lat, wp_lng = waypoints[waypoint_index]["lat"], waypoints[waypoint_index]["lng"]

        # ✅ Step 1: Fetch from DB using `wp_lat, wp_lng`
        if remaining_needed > 0:
            existing_attractions = get_record(
                "attractions_res", {"wp_latitude": wp_lat, "wp_longitude": wp_lng}
            )
            for attraction in existing_attractions:
                if remaining_needed == 0:
                    break
                attractions.append(normalize_attraction(attraction))
                remaining_needed -= 1

        # ✅ Step 2: Fetch from API if needed
        if remaining_needed > 0:
            places_url = "https://discover.search.hereapi.com/v1/discover"
            params = {
                "q": "tourist attraction",
                "at": f"{wp_lat},{wp_lng}",
                "limit": attraction_per_waypoint,
                "sort": "popularity",
                "apiKey": API_KEY
            }

            try:
                response = requests.get(places_url, params=params, timeout=10)
                response.raise_for_status()  # Raises HTTPError if status is 4xx or 5xx
            except requests.exceptions.RequestException as e:
                err_msg = f"ERROR: Request failed: {e}"
                logger.error(err_msg)
                return None
            
            if response.status_code == 200:
                places_data = response.json()
                if "items" in places_data:
                    for place in places_data["items"]:
                        if remaining_needed == 0:
                            break

                        position = place.get("position", {})
                        latitude = position.get("lat", None)
                        longitude = position.get("lng", None)

                        # ✅ **Check if attraction already exists in DB by place coordinates**
                        existing_duplicate = get_record(
                            "attractions_res", {"latitude": latitude, "longitude": longitude}
                        )

                        if existing_duplicate:
                            logger.info(f"Skipping duplicate attraction at ({latitude}, {longitude})")
                            continue  # ✅ Skip duplicate

                        # ✅ **Fetch and insert new attraction**
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
                            "wp_latitude": wp_lat,  # Store waypoint coordinates to avoid duplicate API calls
                            "wp_longitude": wp_lng,
                            "address": safe_translate(place.get("address", {}).get("label", "N/A")),
                            "category": safe_translate(category),
                            "audience_type": safe_translate(audience_type),
                            "popularity": popularity_value,
                            "opening_hours": opening_hours,
                        }

                        insert_record("attractions_res", new_attraction)  # Store in database
                        attractions.append(new_attraction)
                        remaining_needed -= 1

        # ✅ Move to the next waypoint
        waypoint_index += 1
        if waypoint_index >= total_waypoints:
            waypoint_index = 0  # Restart from the beginning if not enough attractions

    disconnect_db()  # ✅ Close DB connection
    return attractions  # ✅ Final return

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
    
    json_output = fetch_attractions_from_route(route_json, max_results=10)
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
