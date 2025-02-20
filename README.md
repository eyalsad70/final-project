# **Virtual Route Planner: ETL Project with Kafka, Python, PySpark, PostgreSQL, MongoDB and Telegram Bot**

## **Overview**
Route planner app is designed to give the best route and breakpoints (optional) for users who want to plan a day trip (currently in Israel only).
Users can choose a direct route between original & destination locations and can also choose to get breakpoints along the way.
Breakpoints may include restaurants and/or gas-stations and/or attractions 
Users will use a telegram BOT to interact with our APP and choose their amenities preferences and will also insert the date & time of travel (so app can collect only amenities which are opened

## **Project Objectives**
The Route Planner project is designed to assist users in planning their trips by providing optimized routes with optional breakpoints. The application allows users to define their start and destination locations while including amenities such as:
**Restaurants**
**Gas stations**
**Attractions**

## **Key Features**
**1. User Interaction via Telegram Bot:** Users provide trip details (start location, destination, date, and time).
**2. Real-Time Data Retrieval:** The system fetches live data to ensure breakpoints are available and open during the specified travel time.
**3. Personalized Route Planning:** Users can filter breakpoints based on preferences (e.g., gas stations with EV charging).
**4. Hybrid Cloud-Based Architecture:** Uses AWS services along with locally executed Python scripts for cost efficiency.
**5. ETL Pipelines for Data Handling:**
   **Main ETL Pipeline:** Fetches user-requested data, processes it, and returns results via Telegram.
   **Static Data ETL Pipeline:** Enhances data quality by integrating third-party sources.
   **Scheduled Cleanup Pipeline:** Maintains up-to-date data by cleaning outdated entries weekly.


## **Architecture**
The architecture is divided into three major pipelines.

### **Main ETL Pipeline**
Trigger: User interaction via Telegram Bot.
Process:
1. Extract data from external APIs (Google, TripAdvisor, etc.) and/or from cache
2. Transform data (cleaning, enrichment).
3. Load structured data into PostgreSQL and semi-structured data into MongoDB.
4. Send forward the optimized route and breakpoints – back to user through BOT and Email

![naya-project-arch-main-etl](https://github.com/user-attachments/assets/6cf3b681-a54e-4a4c-b0f0-682cc059132f)


### **Static data ETL Pipeline**
Purpose: Enhances gas station data by web scraping.
Process:
  1. Scrape gas station data from multiple vendors websites (using BeautifulSoup & Selenium) into temporary CSVs
  2. Translate Hebrew fields to English.
  3. Store cleaned data in PostgreSQL for enrichment.


![naya-project-static-enrich-etl](https://github.com/user-attachments/assets/9ce83efa-6e89-413d-8751-10aaaff89ef5)



### **Scheduled Tasks**
Purpose: Maintains data freshness.
Process:
1. AWS Lambda runs weekly via EventBridge.
2. Cleans old PostgreSQL records for gas stations, restaurants, and attractions.

![naya-project-arch-scheduled](https://github.com/user-attachments/assets/0c2edbfb-8231-46bf-a626-88bffc679df8)





## **Data Processing Model**
We divided the project into several data retrieval and processing pipelines, as shown in the above main flow diagram
(every pipeline has a python folder with corresponding name)

### **Pipeline 1 – Bot service**
1. Handle user interaction – listen to user requests coming from Telegram server, and perform Q&A with the user till having all data for processing request.
2. manage internal state machine for q&a per user
3. look for a similar route in DB (mongo) and fetch relevant data. Otherwise call Google Route API to fetch route summary and breakpoints (called waypoints by api) coordinates
4. create a json request with route request details, save in DB if needed, and send to Kafka topic 'user-requests-queue' for further processing

JSON requests examples can be found under 'json_samples' folder


### **Pipeline 2 – API service**
1. Consume user requests from Kafka,
2. Per breakpoint type requested by user:
  Search for places nearby given request waypoints (in a radius of up to 5km) 
  check in postgres DB table first:
    attractions_res – for breakpoint type 'attraction'
    gas_stations_res – for breakpoint type 'gas-station'
    restaurants_res – for breakpoint type ' restaurant'
  If not there call proper API, transform & clean data, and save in DB
3. places collected from DB/API are added to json and sent to next kafka topic for further processing
4. Kafka Topics:
    Attractions & Restaurants are sent directly to 'results_queue' since API is sufficient and no further enrichment needed
    Gas-stations are sent to 'intermediate_queue' for further enrichment as API details are poor

  **APIs being used:**
  
    https://maps.googleapis.com/maps/api/directions
    
    https://discover.search.hereapi.com/v1/discover
    
    https://maps.googleapis.com/maps/api/place/nearbysearch
    
    https://maps.googleapis.com/maps/api/place/details


JSON examples for attractions, gas-station & restaurant can be found under 'json_samples' folder



### **Pipeline 3 – spark service**
Consume messages from kafka topic 'intermediate_queue' 
Enrich data (for gas-stations) with 3rd party static data saved in postgres DB table 'gas_stations'. Note that this data was created by the static pipeline 
Send enriched places data to kafka topic 'results_queue'


### ***Pipeline 4 - results service***
Consume json messages from Kafka topic 'results_queue' 
Messages contains user parameters & places found on the route
Create textual responses (per place-type) and send to BOT
Aggregate textual responses and send to user's email


# **Installation**
this project was built in VS code running **python 3.10**

## **Step 1: Load project**
set root folder on your local machine and clone this repository 

## **Step 2: set local environment and install python packages**
its recommanded to create a virtual environment (VENV) to avoid versions conflicts between your python and packages needed to be installed.
when using **VENV** it can take all packages from **'requirements.txt'** file and install. otherwise you need to 'pip install' all packages in this file manually

our package contains a folder for each of the pipelines needed to run (simultanously) and 'main' routine to be run

in addition we have 'common-Utils' folder:
  It includes all generic functions that are common and used by the different pipeline services, as follows:
    DB adapters with all needed access APIs for both RDS-Postgres and Mongo
    Kafka producer/consumer APIs
    Logger – all methods are using this utility to log activities 
    Telegram BOT APIs 
    Google Translate facility
    Mail adapter

## **Step 3: Envirnment Variables**

this project is using environment variables for credentials, keys, kafka/mongo/postgres hosts IP & Port, etc...
for proper operations you should aquire the following, and can place them all in environment script (i.e. env_set.ps1 if running under PS terminal):

  $env:TELEGRAM_BOT_TOKEN=" "    # please add your telegram Bot key
  
  $env:GOOGLE_PLACES_KEY=" "       # google places API (from GCP) for routes & places
  
  $env:HEREMAPS_ATTRACTIONS_KEY=" "   # used for attractions
  
  $env:KAFKA_BROKER_HOST = ""     # IP/DNS of the host running Kafka broker
  
  $env:KAFKA_BROKER_PORT = "9092"   
  
  $env:RDS_DB_HOST = ""        # RDS DNS
  
  $env:RDS_DB_NAME = ""
  
  $env:RDS_DB_USER = "postgres"
  
  $env:RDS_DB_PASSWORD = ""
  
  $env:RDS_DB_PORT = "5432"
  
  $env:PYTHONPATH="C:\Naya\final-project"  # **need to change to your project root folder**
  
  $env:MONGO_DB_HOST = ""  # IP/DNS of the host running mongoDB
  
  $env:MONGO_DB_PORT = 27017            # Default MongoDB port
  
  $env:MONGO_DB_DBNAME = "nayaProj"     # Change if needed




## **Step 4 (optional): Email support**

Our project supports email through Twillo SendGrid which requires registration (free for up to 100 emails per day). We use it since it doesn't require a personal email password (instead it verifies us via our gmail or other personal mail and gives access key).

If you need email support you must register to SendGrid with personal mail and add environment script with the following:

  $env:SENDGRID_MAIL_KEY = ""
  
  $env:SENDER_EMAIL = ""   # this is the your personal mail with which you registered in sendgrid
  
  $env:RECEIVER_EMAIL = "<email1>;<email2>;" # list of receiver emails (as we don't have it through BOT UI yet)



## ** Step 5: Install Tools
this repository includes YAML files for Kafka & MongoDB dockers. you may install on local machine (and run using docker desktop) or install it on AWS ECS (t3.medium should be sufficient)
for PostgreSQL we are using AWS RDS but you can set up a local one
note that environment file above must include IP, Port & credentials for those tools


# ** Running Python Scripts**
1. open PS Terminal and run your envirnment file (i.e. .\env_set.ps1)
2. if you get an error run this script and repeat step 1:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
3. if you want emails to be sent run environment file for emails
4. run script 'run_scripts.bat'
   it will start all 4 python services and open 4 windows.
   if one of them drops make sure that all dependencies are valid (all pip packages installed and all environment variables are set)
   if your kafka/mongo/postgres are not up you will see ERROR in logs but no exception, and end2end flow will not work properly

5. to stop all services call script 'stop_scripts.bat'

   
   
  
Enjoy!
