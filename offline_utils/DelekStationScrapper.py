import requests
from bs4 import BeautifulSoup
import csv

# URL of the gas stations page
URL = "https://delek.co.il/%d7%90%d7%99%d7%aa%d7%95%d7%a8-%d7%aa%d7%97%d7%a0%d7%94/"

# Send HTTP request
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(URL, headers=headers)
response.raise_for_status()  # Raise an error if request fails

# Parse the page with BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

# Find all station rows
stations = soup.find("tbody", id="stations").find_all("tr", class_="station-row")

# Prepare CSV file
csv_filename = "delek_gas_stations.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Station Name", "City", "Address", "Latitude", "Longitude", "Services", "Operating Hours"])

    # Extract data for each station
    for station in stations:
        name = station.get("data-name", "").strip()
        city = station.get("data-city", "").strip()
        address = station.get("data-address", "").strip()
        lat = station.get("data-lat", "").strip()
        lng = station.get("data-lng", "").strip()
        services = station.get("data-services", "").strip().replace(",", ", ")  # Format services nicely
        hours = station.get("data-hours", "").strip()

        writer.writerow([name, city, address, lat, lng, services, hours])

print(f"Scraping complete! Data saved in '{csv_filename}'.")
