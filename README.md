Route Planner 101:
the route planner allow users (using telegram bot as their client) to plan there route from chosen origin to chosen destination with optional customized breakpoints on their way.
user can choose to have breakpoints such as restaurants/cofee, gas-stations or attractions of different flavors. for this purpose user can enter date & time of departure so we can filter only services which are opened during the ride.
user can also choose a direct route which will give him/her total distance and best road to use

Multiple users can use the BOT client simultanously, but keep in mind of slow responses, due to backend resources which are currently limited

the following technologies are used to support asyncronous ETL pipeline and reliable storage of user requests and responses
1. Google Places & HereMaps APIs are used to fetch restaurants, gas-stations & attractions in JSON format
2. Postgres DB (running on AWS RDS) is used to save the above data (after cleaning and optionally enriching the data): Tables: 
3. MongoDB (running on AWS EC2) is storing user route requests (as it contains varying quantity of route waypoints, making it non-schematic)
4. Python & PySpark scripts are handling the whole pipeline as explained below
5. Kafka (running on EC2) is used as message queue (working in near real time batch process) between the python services
6. Web scrapping is used offline to retreive gas-stations details that are not given through google api (such as petrol98 or EV-charge support, car-wash, convenient store, etc...), and save them in CSV, then load the data (to enrich later on by PySpark) to "attractions" table in PostgreSQL DB.
7. email service allow user to get detailed response through email (using Twillo SendGrid service)
8. AWS Lambda is used to clean old DB entries, to make sure we are not caching old data

   ![naya-project-arch](https://github.com/user-attachments/assets/7373aea7-a837-432f-9d26-fb2376f1e49b)


Enjoy!
