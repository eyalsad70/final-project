
""" 
    Holds general utilities required by this project
"""
import re
import os
import csv
import json
from datetime import datetime
import pandas as pd
from enum import Enum
from math import radians, sin, cos, sqrt, atan2

israeli_cities = set()

class UserRequestFieldNames(Enum):
    USERID = 'user_id'
    USER_EMAIL = 'email'
    CREATED_AT = 'createdAt'
    ORIGIN = 'origin'
    DESTINATION = 'destination'
    DEPARTURE_TIME = 'departure'
    FUEL_REQUIRED = 'gas-stations'
    FOOD_REQUIRED = 'restaurants'
    ATTRACTION_REQUIRED = 'attractions'
    ROUTE_ID = 'route_id'
    WAYPOINTS = 'waypoints' 
    MAIN_ROUTE = 'summary'
    TOTAL_DISTANCE = 'total-distance'
    LATITUDE = 'lat'
    LONGITUDE = 'lng'
        
class BreakPointName(Enum):
    NONE = "none"    
    FUELING = "gas_station"
    RESTAURANT = "restaurant"
    ATTRACTION = "attraction"
    
    
def normalize_city_name(city_name):
    """Convert city name to lowercase and remove hyphens."""
    return city_name.lower().replace('-', ' ')


def load_israeli_cities():
    """Load and normalize city names from the CSV file."""
    csv_file_path = './bot-service/il-cities.csv'  # Update this path to where your CSV file is located
    
    # Load the list of Israeli cities from the CSV
    cities_df = pd.read_csv(csv_file_path)

    for city in cities_df['city']:
        # Replace hyphen with space to split by and create separate city names
        parts = city.lower().replace('-', ' ').split()
    
        # Add all parts as individual city names (e.g., "Tel Aviv-Yafo" becomes "Tel Aviv" and "Yafo")
        israeli_cities.add(' '.join(parts))  # Add the full parts, like "Tel Aviv"
        if '-' in city:
            # If there was a hyphen, split at it and add individual parts
            for part in city.split('-'):
                israeli_cities.add(part.strip().lower())  # Add each city part separately, like "Tel" and "Yafo"



def validate_city(user_input):
    """Check if the normalized user input exists in the set of city names."""
    normalized_input = normalize_city_name(user_input)
    return normalized_input in israeli_cities


def validate_datetime(user_input):
    """Validate user input for format 'DD/MM HH:MM' and check if it's a real date & time.
       Returns the day of the week if valid, otherwise None."""
    try:
        # Get the current year
        current_year = datetime.now().year
        parts = user_input.split()
        if len(parts) != 2:
            return None
        str_time = f"{parts[0]}/{current_year} {parts[1]}"
        # Parse user input with the current year
        dt = datetime.strptime(str_time, "%d/%m/%Y %H:%M")
        
        # Return the valid datetime object and its day of the week
        return dt.strftime("%A")  # Returns full day name (e.g., "Monday")
    except ValueError:
        return None

    
def parse_numbers(user_input, min_val, max_val):
    """Convert a string of numbers into a unique sorted list, filtering by range."""
    numbers = set()  # Use a set to avoid duplicates

    for num in user_input.replace(',', ' ').split():  # Replace ',' with ' ' and split
        if num.isdigit():  # Ensure it's a valid number
            num = int(num)
            if min_val <= num <= max_val:  # Validate range
                numbers.add(num)

    return sorted(numbers)  # Return a sorted list


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in km

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c  # Distance in km


if __name__ == "__main__":
    print(validate_datetime("07/02 11:50"))
    print(parse_numbers("1 ,3 ,7 ,a b 18 ", 1, 7))
    
    with open("route_data.json", "r", encoding="utf-8") as file:
        data = json.load(file)  # Parse JSON
        # Extract coordinates of waypoints 0 & 1
        lat1, lon1 = data["waypoints"][0]["lat"], data["waypoints"][0]["lng"]
        lat2, lon2 = data["waypoints"][1]["lat"], data["waypoints"][1]["lng"]
        # Calculate distance
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        print(f"Distance between waypoints 0 & 1: {distance:.2f} km")