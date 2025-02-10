"""
Telegram BOT handlers
initialize the bot, listen on requests, and support responses through handlers
"""

import telebot
from telebot import types
import time, datetime
import requests
import json
# import keys_loader
#from common_utils import my_logger
from common_utils.local_logger import logger
import user_session
import os

test_token = os.getenv('TELEGRAM_BOT_TOKEN') # keys_loader.load_private_key("telebot") 
if not test_token:
    logger.error("Error: test_token not found")
    raise ValueError("test_token not found!")

bot_name = "route-planner-101-bot"


# Get url for updates - run this once from Browser (not from here) to get chat id
# if you get empty list enter some text in the bot itself and
bot_url_get_updates = f'https://api.telegram.org/bot{test_token}/getUpdates'
#print(bot_url_get_updates)

def send_message(text):
    # put your chat id and send a message
    bot_url = f'https://api.telegram.org/bot{test_token}/'
    chat_id = 6550133750  # int(keys_loader.load_private_key("telebot_id"))

    url = bot_url + f'sendMessage?chat_id={chat_id}&text={text}'
    print(url)
    logger.info(url)
    
    # # Print the get request
    resp = requests.get(url)
    #print(resp.text)

    message = json.loads(resp.text)['result']
    print(message)
    logger.info(message)
    
    
def send_welcome_message():
    current_time = time.localtime()
    time_string = time.strftime("%Y-%m-%d %H:%M:%S", current_time)

    text = f'Wake up!! Its {time_string}'
    send_message(text)
    
###################################################################################################

def log_message(message):
        logger.info(f"Message ID: {message.message_id} From User ID: {message.from_user.id} ; Message Text: {message.text}")

# Create bot class
bot = telebot.TeleBot(test_token)


def start_bot():    
    # start listening
    bot.polling()
    
    
def bot_send_start_message(message):
    bot.reply_to(message, "welcome to your Route Planner BOT")
    with open('./bot-service/route-icon.jpg', 'rb') as photo:
        bot.send_photo(message.from_user.id, photo)
    bot.reply_to(message, "press any key to start!!!")
    
    
## ---------------------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def welcome(message):
    # get user session for this user. create it if not exists. Note that this 'start' command can be used also to restart session
    #userSession = user_session.get_user_session(message.from_user.id, True)
    #userSession.start()
    bot_send_start_message(message)
    

## ---------------------------------------------------------------------------------
@bot.message_handler(content_types=['text'])
def handle_response(message):
   
    log_message(message)

    my_user:user_session.UserInfo = user_session.get_user(message.from_user.id)
    if not my_user:
        my_user = user_session.create_user(message.from_user.id)
        # TBD - Start bot interaction for new user, getting its details
        # for now, use stub
    
    userSession, is_new_route = user_session.get_user_active_route(my_user.user_id)
    
    if userSession:        
        response = userSession.handle_user_message(message)
        if response:
            bot.reply_to(message, response)
    #     response = userSession.next_bot_action()
    #     if response:
    #         bot.reply_to(message, response)
    else:
        bot.reply_to(message, "press /start to begin!!")

if __name__ == "__main__":
    send_welcome_message()
