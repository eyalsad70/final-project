import requests
import json
import os
import common_utils.translator as tr  # Correct import
from common_utils.virtual_route_planner_logger import logger

# HereMaps API Key from environment variable
API_KEY = os.getenv('HEREMAPS_ATTRACTIONS_KEY')
if not API_KEY:
    logger.error("Error: API Key not found! Set the 'HEREMAPS_ATTRACTIONS_KEY' environment variable.")
    raise ValueError("API Key not found!")

# Mapping attraction categories to target audience
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

# Use the fixed `translate_text` function
def safe_translate(text):
    """ Wrapper function for translation with error handling. """
    return tr.translate_text(text) if text else text

def get_attractions(waypoints, max_results=20):
    """
    Fetches attractions near waypoints from the HERE Places API.
    Spreads searches along the route to avoid clustering.
    Uses improved translation handling.
    """
    attractions = []
    total_waypoints = len(waypoints)

    if total_waypoints == 0:
        logger.error("No waypoints available in the route.")
        return []

    step = max(1, total_waypoints // max_results)

    for i in range(0, total_waypoints, step):
        lat, lng = waypoints[i]["lat"], waypoints[i]["lng"]
        if len(attractions) >= max_results:
            break

        places_url = "https://discover.search.hereapi.com/v1/discover"
        params = {
            "q": "tourist attraction",
            "at": f"{lat},{lng}",
            "limit": 5,
            "sort": "popularity",
            "apiKey": API_KEY
        }

        response = requests.get(places_url, params=params)
        if response.status_code != 200:
            logger.error(f"Places API Error at {lat},{lng}: {response.status_code}")
            continue

        places_data = response.json()
        if "items" in places_data:
            for place in places_data["items"]:
                if len(attractions) >= max_results:
                    break

                category = place.get("categories", [{}])[0].get("name", "N/A")
                audience_type = CATEGORY_MAPPING.get(category, "General")

                opening_hours_list = place.get("openingHours", [])
                opening_hours = opening_hours_list[0]["text"] if opening_hours_list else ["N/A"]

                position = place.get("position", {})
                latitude = position.get("lat", None)
                longitude = position.get("lng", None)

                popularity_value = place.get("popularity")
                if popularity_value in [None, "N/A"]:
                    popularity_value = None  # Store NULL instead of "N/A"

                # Use `safe_translate()` to prevent API failures
                translated_attraction = {
                    "attraction_name": safe_translate(place["title"]),
                    "latitude": latitude,
                    "longitude": longitude,
                    "address": safe_translate(place.get("address", {}).get("label", "N/A")),
                    "category": safe_translate(category),
                    "audience_type": safe_translate(audience_type),
                    "popularity": popularity_value,
                    "opening_hours": safe_translate(opening_hours)
                }

                attractions.append(translated_attraction)

        logger.info(f"Fetched {len(attractions)} attractions so far.")

    return attractions


def fetch_attractions_from_route(route_data, max_results=20):
    """
    Fetches attractions along a predefined route given as JSON input.
    """
    try:
        #route_data = json.loads(route_json)
        waypoints = route_data["waypoints"]
        origin = tr.translate_text(route_data["origin"]).replace(" ", "_")
        destination = tr.translate_text(route_data["destination"]).replace(" ", "_")
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Invalid JSON format: {e}")
        return

    if not waypoints:
        logger.error("Error: No valid waypoints found in JSON.")
        return

    # Fetch attractions near waypoints
    attractions = get_attractions(waypoints, max_results)

    # Generate filename dynamically based on route start & end
    file_name = f"attractions_{origin}_to_{destination}.json"

    with open(file_name, "w", encoding="utf-8") as json_file:
        json.dump(attractions, json_file, indent=4, ensure_ascii=False)

    logger.info(f" JSON file '{file_name}' generated successfully with {len(attractions)} attractions!")

    return attractions


if __name__ == "__main__":
    # Example JSON input (simulating route_dictionary)
    route_dict = {
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
            {
                "lat": 32.0852876,
                "lng": 34.7817653
            },
            {
                "lat": 32.0574901,
                "lng": 34.7853104
            },
            {
                "lat": 31.9471941,
                "lng": 34.750032
            },
            {
                "lat": 31.7816482,
                "lng": 34.6701594
            },
            {
                "lat": 31.8062343,
                "lng": 34.657037
            }
        ]
    }
        
    fetch_attractions_from_route(route_dict, max_results=20)
