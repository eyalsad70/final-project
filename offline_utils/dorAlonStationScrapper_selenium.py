
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time

# Set up the WebDriver (ensure the driver is in your PATH or specify the path)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# URL of the website
url = "https://www.doralon.co.il/station/"

# Open the website
driver.get(url)

# Wait for the page to load completely
time.sleep(5)  # Adjust the sleep time if necessary

# Get the page source after JavaScript has rendered the content
page_source = driver.page_source

# Parse the page content with BeautifulSoup
soup = BeautifulSoup(page_source, 'html.parser')

# Create a list to store station data
stations_data = []

# Find all stations on the page
stations = soup.find_all('div', class_='sl__item')

# Loop through each station and extract the required data
for station in stations:
    # Station name
    station_name = station.find('h2', class_='sl__item-title').text.strip() if station.find('h2', class_='sl__item-title') else 'N/A'
    
    # Services (list of services under 'sl__item-services')
    services_list = station.find_all('li', class_='sl__item-service')
    services = [service.text.strip() for service in services_list] if services_list else ['N/A']
    
    # Latitude and Longitude
    latitude = station['data-lat'] if 'data-lat' in station.attrs else 'N/A'
    longitude = station['data-lng'] if 'data-lng' in station.attrs else 'N/A'
    
    # Address (from 'sl__items-address' inside 'sl__item-details')
    address = station.find('span', class_='sl__items-address').text.strip() if station.find('span', class_='sl__items-address') else 'N/A'

    # Append the data to the list
    stations_data.append([station_name, ', '.join(services), latitude, longitude, address])

# Write the data into a CSV file
csv_file = 'dor_gas_stations.csv'
header = ['Station Name', 'Services', 'Latitude', 'Longitude', 'Address']

with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(header)  # Write header row
    writer.writerows(stations_data)  # Write data rows

print(f"Data successfully scraped and saved to {csv_file}")

# Close the WebDriver
driver.quit()
