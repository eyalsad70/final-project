import requests
import json
import csv

url = "https://corporatedataapi.paz.co.il/api/dapi/station/mapStations?api-version="

headers = {
    "Content-Type": "application/json"
}

payload = {}  # Some APIs require a body, even if empty

response = requests.post(url, headers=headers, json=payload)
#print(response.json())

if response.status_code == 200:
    data = response.json()

    # Extract stations list
    stations = data.get("Body", {}).get("body", {}).get("stations", [])

    if not isinstance(stations, list):  # Ensure it's a list
        raise ValueError("Unexpected JSON structure: 'stations' is not a list")

    # Define CSV file name
    csv_filename = "paz_stations.csv"

        # Open CSV file for writing
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write header row
        writer.writerow(["name", "address", "city", "latitude", "longitude", 
                         "opening_hours", "product98", "productGas", "productUrea", 
                         "isElectric", "car_wash", "store"])

            # Write data rows
        for station in stations:
            opening_hours = "Unknown"
            meta_data = station.get("metaData", [])
                
            # Check for '24/7' and 'שומרת שבת' in metadata
            for service in meta_data:
                service_name = service.get("name", "")
                #print(f"Service name: {service_name}")  # Print metadata service names for debugging
                if service_name == "24/7":
                    opening_hours = "24/7"
                elif service_name == "שומרות שבת":
                    opening_hours = "Closed on Saturday"
                    
            writer.writerow([
                    station.get("name", ""),
                    station.get("address", ""),
                    station.get("city", ""),  # Added city field
                    station.get("geoLocation", {}).get("latitude", ""),
                    station.get("geoLocation", {}).get("longitude", ""),
                    opening_hours,
                    station.get("product98", False),
                    station.get("productGas", False),
                    station.get("productUrea", False),
                    station.get("isElectric", False),  # Added isElectric field
                    any("wash" in service.get("name", "").lower() for service in station.get("metaData", [])),
                    any(service.get("name", "").lower() == "yellow" for service in station.get("metaData", []))  # Renamed convenience_store to store
                ])

        print(f"Data successfully written to {csv_filename}")
else:
    print(f"Error {response.status_code}: {response.text}")