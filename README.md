# **Route Planner 101: ETL Project with Kafka, Python, PySpark, PostgreSQL, MongoDB and Telegram Bot**

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





  
Enjoy!
