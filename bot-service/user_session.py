""" 
This file define and hold user sessions.
each user that access this APP through telegram BOT on his mobile/desktop will have a session created 
for him with his details and activities 
This allows multiple users using the BOT simultanously without affecting each other 
"""

from datetime import datetime
from enum import Enum
import random

from common_utils.local_logger import logger
import bot_brain
from bot_brain import UserBreakTypes, UserSelectOptions
import user_request
import google_routes
from common_utils.utils import UserRequestFieldNames
from common_utils import mongodb_adapter

class BoolQuestion(Enum):
    UNKNOWN = 0
    NO  = 1
    YES = 2

class FuelQuestion(Enum):
    UNKNOWN = 0
    NO  = 1
    YES = 2
    YES_GAS98 = 3
    YES_ELECTRIC = 4
    

class UserInfo():
    def __init__(self, userId, userName = "") -> None:
        self.user_id = userId
        self.user_name = userName
        self.user_email = None
        self.createdAt = datetime.now()
        self.detailsCompleted = False
        self.latest_route_id = 0
        #self.latest_route_state = "finished"
        
        
class UserRouteSession():
    def __init__(self, userId, routeId = 0, email = None) -> None:
        self.user_id = userId
        self.user_email = email
        self.route_id = routeId
        if self.route_id == 0:
            self.route_id = self.user_id * 100 + random.randint(100, 999)
        self.bot_started = False
        self.bot_activities = []
        self.bot_brain = bot_brain.RouteBotBrain()  # bot brain includes all data provided by user


    def handle_user_message(self, message):
        logger.info(f"user {self.user_id} request message {message.text}")
        if self.bot_started:
            self.log_activity(message.text, "request")
        content = self.bot_brain.handle_user_message(message)
        if content:
            self.log_activity(content, "response")        
            
        if self.bot_brain.is_bot_interaction_completed():
            json_request = self.create_json_request()
            user:UserInfo = get_user(self.user_id)    
            user.detailsCompleted = True
            if json_request:
                user_request.process_user_request(json_request)    
            else:
                content = f"route or waypoints for user {self.user_id} not found. cancelled! "
                
        return content

    
    def next_bot_action(self): # this is needed only for bi-dimensiona menu
        # return self.bot_brain.next_action()
        return None

    def start(self):
        self.bot_started = True
        self.bot_brain.restart()
    
    def get_bot_brain(self):
        return self.bot_brain

    
    def log_activity(self, message:str, message_from):
        self.bot_activities.append(f"{message_from}: {message}")
    
    def display_bot_activities(self):
        for activity in self.bot_activities:
            print(activity)
            
    def save_activities_log(self):
        file_name = f"summary_{self.user_id}.txt"
        with open(file_name, "w") as fd:
            fd.write(self.bot_activities)
    
    def create_json_request(self):
        request = dict()
        request[UserRequestFieldNames.USERID.value]= self.user_id
        request[UserRequestFieldNames.USER_EMAIL.value]= self.user_email
        request[UserRequestFieldNames.CREATED_AT.value] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        request[UserRequestFieldNames.ORIGIN.value] = self.bot_brain.origin
        request[UserRequestFieldNames.DESTINATION.value] = self.bot_brain.destination
        request[UserRequestFieldNames.DEPARTURE_TIME.value] = self.bot_brain.datetime
        request[UserRequestFieldNames.FUEL_REQUIRED.value] = 0
        request[UserRequestFieldNames.FOOD_REQUIRED.value] = 0
        request[UserRequestFieldNames.ATTRACTION_REQUIRED.value] = 0        
        request[UserRequestFieldNames.ROUTE_ID.value] = self.route_id

        for activity in self.bot_brain.breakpoints_list:
            if activity == UserBreakTypes.DIRECT.value:
                break
            if activity == UserBreakTypes.FUELING.value:
                request[UserRequestFieldNames.FUEL_REQUIRED.value] = 1
            elif activity == UserBreakTypes.RESTAURANTS.value:
                request[UserRequestFieldNames.FOOD_REQUIRED.value] = 1
            elif activity == UserBreakTypes.ATTRACTIONS.value:
                request[UserRequestFieldNames.ATTRACTION_REQUIRED.value] = 1   
                
        # check first if similar route exists in cache. call api only if not
        query = {"origin": self.bot_brain.origin, 'destination': self.bot_brain.destination}
        db_route = mongodb_adapter.fetch_data(mongodb_adapter.CollectionType.MONGO_ROUTES_REQUESTS_COLLECTION, query)    
        if not db_route:
            id, google_route = google_routes.get_route_raw(self.bot_brain.origin, self.bot_brain.destination)
            if google_route:
                status = google_routes.get_filtered_route(google_route, request)
                if status:
                    mongodb_adapter.insert_data(mongodb_adapter.CollectionType.MONGO_ROUTES_REQUESTS_COLLECTION, request)
                    removed_value = request.pop("_id", None)  # Removes id object added by mongo, if exists
                    logger.info(f"get Google route for route {self.route_id} from {self.bot_brain.origin} to {self.bot_brain.destination}")
                else: 
                    return None
            else:    
                logger.error(f"couldn't find google route from {self.bot_brain.origin} to {self.bot_brain.destination}. ABORTING!!!")
                return None
        else:
            request[UserRequestFieldNames.MAIN_ROUTE.value] = db_route[0][UserRequestFieldNames.MAIN_ROUTE.value]
            request[UserRequestFieldNames.TOTAL_DISTANCE.value] = db_route[0][UserRequestFieldNames.TOTAL_DISTANCE.value]
            request[UserRequestFieldNames.WAYPOINTS.value] = db_route[0][UserRequestFieldNames.WAYPOINTS.value]
            logger.info(f"get DB route for route {self.route_id} from {self.bot_brain.origin} to {self.bot_brain.destination}")

        return request

#####################################################################################################################
users_db = dict()
users_routes = dict()


def get_user(user_id):
    session = None
    try:  # if session exists return its object ; otherwise create new one
        session = users_db[user_id]        
    except:
        logger.info(f"user {user_id} not exists")
          
    return session


def create_user(user_id, user_name = ""):
    try:  # if session exists return its object ; otherwise create new one
        user = users_db[user_id]        
    except:
        user = UserInfo(user_id, user_name)
        users_db[user_id] = user
        logger.info(f"new user session was created for user {user_id}")
            
    return user


def get_user_active_route(user_id):
    # looking for latest active route session for this user. if not exists, create new one
    is_new_route = False
    user:UserInfo = get_user(user_id)    
    if user:
        if (user.latest_route_id > 0 and user.detailsCompleted == True) or not user.latest_route_id:
            route = UserRouteSession(user_id, 0, user.user_email)
            users_routes[route.route_id] = route
            user.latest_route_id = route.route_id
            user.detailsCompleted = False
            is_new_route = True
        else:
            route = users_routes[user.latest_route_id]
        return route, is_new_route
    logger.warning(f"User {user_id} not exists. you must create it first")
    return None, None
    

# def display_users_activities():
#     for user_obj in user_sessions.values():
#         print(f"User Id {user_obj.user_id} email {user_obj.email} : has the following activities: ")
#         user_obj.display_bot_activities()
        

