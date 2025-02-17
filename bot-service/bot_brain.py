
""" 
    BOT Brain - include all handlers for all user requests, Bot State-machine and various user operations
    its created per user-session so each bot user will have its own platform regardless of others running in paralel
"""
    
import json
from datetime import datetime
from enum import Enum

# local imports
import user_session
from common_utils import utils

class UserBreakTypes(Enum):
    DIRECT = 1
    FUELING = 2
    FUELING_SPECIAL = 3
    RESTAURANTS = 4
    RESTAURANTS_COFFEE_ONLY = 5
    ATTRACTIONS = 6
    ATTRACTIONS_KIDS = 7
    
class UserSelectOptions(Enum):
    CONTINUE = 'C'
    CANCEL = 'X'
    
###################################################################################################

class RouteBotBrain():
    """ This class holds the travel-app BOT brains with all supported actions and requests/responses logic
    
    THE BOT is currently support the following operations:
    command /start - to start/restart bot session for user 
    text requests:
        select origin & destination cities (other resolutions like full address not relevant)
        select departure date and time (this will allow validations of ammenties opening hours and optimize side attractions)
        select which breakpoints are required (gas station, restaurant or convenient store, side attractions) - multiple choices available
        show summary & process 
"""
    
    user_menu = """
            menu-options (choose number):
                1. add name
                2. add email
                3. save & continue
    """
    
    route_menu = """ 
            menu-options (choose number):
                1. select origin
                2. select destination
                3. select when 
                4. select break types
                6. show and send request
                /start to restart App
            """
    
    break_types_menu = f"""
            {UserBreakTypes.FUELING.value}. Fueling
            {UserBreakTypes.RESTAURANTS.value}. Restaurants
            {UserBreakTypes.ATTRACTIONS.value}. Attractions       
    """
    max_breaks = 7
    
    new_user_action_state_machine = {
        # 'state' : "next suggestion for user"
        'start' :'please add your name',
        'name_selected' : 'please add your email address',
        'mail_selected' : "save & continue? (y/n)",
        'menu_sel' : user_menu
    }
    
    new_route_action_state_machine = {
        # 'state that was finished' : "next suggestion for user"
        'start' :'Select Origin',
        'origin_sel' : 'Select Destination',
        'destination_sel' : "Select date (dd/mm) and estimated departure time (HH:mm)",             
        'time_sel' : f"Select breaks from menu (multiple choices available) or {UserBreakTypes.DIRECT.value} for Direct \n {break_types_menu}",
        'menu_sel' : f"Press {UserSelectOptions.CONTINUE.value} to Continue or {UserSelectOptions.CANCEL.value} to cancel",
        'finish' : 'Processing...',
        'cancel' : 'request was cancelled. press /start for new request'
    }
    
    def __init__(self) -> None:
        # self.start_command = 'start'
        self.restart()
        
    def restart(self):
        self.action_state = 'start'
        self.started = False
        self.origin = ""
        self.destination = ""
        self.datetime = ""
        self.day_of_week = "Unknown"
        self.breakpoints_str = ""
        self.breakpoints_list = set()   
    
    def display_status(self):
        print(f"state = {self.action_state} ; origin = {self.origin} ; destination = {self.destination}")
        
    def is_bot_interaction_completed(self):
        return self.action_state == 'finish'
    
    
    # ---------------------------------------------------------------------
    def handle_user_message(self, message):
        """ 
            this method is the Bot brain which handles the state machine and create proper responses to user 
        """
        if self.action_state == 'start':
            if self.started:
                result = self.handle_city_selection(message)
                if result: 
                    self.origin = message.text
                    self.action_state = 'origin_sel'
                    # self.response_sent = False
                    return self.new_route_action_state_machine['origin_sel']
                else:
                    # self.response_sent = True
                    return f"Invalid origin selected. choose again"
            else:
                self.started = True
                return self.new_route_action_state_machine['start']
     
            
        elif self.action_state == 'origin_sel':
            # handle destination selection
            result = self.handle_city_selection(message)   
            if result: 
                self.destination = message.text
                self.action_state = 'destination_sel'
                return self.new_route_action_state_machine['destination_sel']
            else:
                return f"destination is not valid or not of proper type for {self.destination}. choose again"     
            

        elif self.action_state == 'destination_sel':
            # handle departure time selection
            result = self.handle_departure_time_selection(message)   
            if result: 
                self.action_state = 'time_sel'
                return self.new_route_action_state_machine['time_sel']
            else:
                return f"time is not valid {self.datetime}. choose again as follows DD/MM HH:MN"     
            
        
        elif self.action_state == 'time_sel':
            # handle breakpoints selection
            result = self.handle_breaks_selection(message)   
            if result: 
                self.action_state = 'menu_sel'
                return self.new_route_action_state_machine['menu_sel']
            else:
                return f"invalid list {self.breakpoints_str}. make sure all numbers are valid and seperated with <,>"     
    
            
        elif self.action_state == 'menu_sel':
            # handle breakpoints selection
            result = self.handle_selection_completion(message)   
            if result: 
                self.action_state = 'finish'
                return self.new_route_action_state_machine['finish']
            else:
                self.action_state = 'cancel'
                return self.new_route_action_state_machine['cancel']    
        
        else:
            return "Bot is not in valid state. please press /start"
        
    # ------------------------------------------------------------------------------------
        
    def handle_city_selection(self, message):
        return utils.validate_city(message.text)  

            
    def handle_departure_time_selection(self, message):
        # should find attractions near by and return list in text format
        # if destination not a city will also fetch major cities in the area
        time_str = message.text
        day_of_week = utils.validate_datetime(time_str)
        if day_of_week:
            self.day_of_week = day_of_week
            self.datetime = time_str
            return True
        return False
        
    def handle_breaks_selection(self, message):
        numbers_list:set = utils.parse_numbers(message.text, 1, self.max_breaks)
        if numbers_list:
            self.breakpoints_list = numbers_list
            self.breakpoints_str = message.text
            return True
        return False
    
    def handle_selection_completion(self, message):
        if message.text.upper() == UserSelectOptions.CONTINUE.value:
            # TBD - create JSON request, save and send
            return True
        return False
        
    
    